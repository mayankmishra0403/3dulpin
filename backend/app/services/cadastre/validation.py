"""3D topology validation and conflict management.

Checks performed:
  * 3D_overlap          — volumetric intersection between any two parcels
                          (ST_3DIntersects with intersection volume > 0)
  * duplicate_ulpin     — same 3D ULPIN on more than one parcel
  * height_exceed       — parcel zmax above declared building top
  * slab_discontinuity  — gap between stacked floor envelopes of a building
"""

from __future__ import annotations

from app import db


async def run_validation() -> dict:
    conn = db.pool()
    counts: dict[str, int] = {}

    # --- duplicate ULPIN -------------------------------------------------
    dup = await conn.fetch(
        "SELECT ulpin3d, count(*) AS n FROM cadastre.parcels_3d GROUP BY ulpin3d HAVING count(*) > 1"
    )
    counts["duplicate_ulpin"] = len(dup)
    for row in dup:
        await _assert_conflict(
            conn, "duplicate_ulpin", row["ulpin3d"], None,
            description=f"3D ULPIN {row['ulpin3d']} assigned to {row['n']} parcels",
        )

    # --- 3D overlaps (GEOS ST_3DIntersects + exact prism extents) --------
    overlap_pairs = await conn.fetch(
        """
        SELECT p.id AS a_id, p.ulpin3d AS a_ulpin, p.category::text AS a_cat,
               o.id AS b_id, o.ulpin3d AS b_ulpin, o.category::text AS b_cat,
               GREATEST(LEAST(ST_XMax(p.solid), ST_XMax(o.solid))
                        - GREATEST(ST_XMin(p.solid), ST_XMin(o.solid)), 0)::float8 AS dx,
               GREATEST(LEAST(ST_YMax(p.solid), ST_YMax(o.solid))
                        - GREATEST(ST_YMin(p.solid), ST_YMin(o.solid)), 0)::float8 AS dy,
               GREATEST(LEAST(p.zmax, o.zmax) - GREATEST(p.zmin, o.zmin), 0)::float8 AS dz
        FROM cadastre.parcels_3d p
        JOIN cadastre.parcels_3d o ON p.id < o.id
            AND p.solid && o.solid
            AND ST_3DIntersects(p.solid, o.solid)
        WHERE p.solid IS NOT NULL AND o.solid IS NOT NULL
        ORDER BY (GREATEST(LEAST(ST_XMax(p.solid), ST_XMax(o.solid))
                    - GREATEST(ST_XMin(p.solid), ST_XMin(o.solid)), 0)
                 * GREATEST(LEAST(ST_YMax(p.solid), ST_YMax(o.solid))
                    - GREATEST(ST_YMin(p.solid), ST_YMin(o.solid)), 0)
                 * GREATEST(LEAST(p.zmax, o.zmax) - GREATEST(p.zmin, o.zmin), 0)) DESC
        """
    )
    surface_used_for_underground = {"underground", "parking", "metro_tunnel", "utility_network"}
    counts["3D_overlap"] = 0
    counts["underground_overlap"] = 0
    for r in overlap_pairs:
        volume = r["dx"] * r["dy"] * r["dz"]
        if volume <= 0:
            continue
        underground = (r["a_cat"] in surface_used_for_underground or r["b_cat"] in surface_used_for_underground)
        ctype = "underground_overlap" if underground else "3D_overlap"
        counts[ctype] = counts.get(ctype, 0) + 1
        severity = "high" if volume > 1 else "medium"
        desc = " and ".join(filter(None, [r["a_ulpin"], r["b_ulpin"]]))
        await _assert_conflict(
            conn, ctype, r["a_ulpin"], r["b_ulpin"],
            volume_m3=volume,
            severity=severity,
            description=f"{desc} intersect by {volume:.2f} m³",
        )

    # --- height exceed ---------------------------------------------------
    exceed = await conn.fetch(
        """
        SELECT p.ulpin3d, p.zmax, (b.ground_z + b.height_m) AS building_top
        FROM cadastre.parcels_3d p
        JOIN cadastre.buildings b ON b.id = p.building_id
        WHERE p.category IN ('floor', 'suite')
          AND p.zmax > (b.ground_z + b.height_m) + 0.01
        """
    )
    counts["height_exceed"] = len(exceed)
    for r in exceed:
        await _assert_conflict(
            conn, "height_exceed", r["ulpin3d"], None,
            severity="high",
            description=(
                f"{r['ulpin3d']} reaches z={r['zmax']:.2f}m but building top "
                f"is {r['building_top']:.2f}m"
            ),
        )

    # --- slab discontinuity (stacked floors leave a gap) ----------------
    buildings = await conn.fetch(
        """
        SELECT building_id, array_agg(DISTINCT (zmin, zmax)) AS zranges
        FROM cadastre.parcels_3d
        WHERE building_id IS NOT NULL AND category IN ('floor', 'suite')
        GROUP BY building_id
        """
    )
    gap_count = 0
    for b in buildings:
        ranges = sorted({(float(a), float(b)) for (a, b) in b["zranges"]})
        if len(ranges) < 2:
            continue
        prev_top = ranges[0][1]
        for lo, hi in ranges[1:]:
            gap = lo - prev_top
            if gap > 0.05:
                gap_count += 1
                await _assert_conflict(
                    conn, "slab_discontinuity", f"building:{b['building_id']}",
                    None, severity="medium",
                    description=f"vertical gap of {gap:.2f}m between stacked levels",
                )
            prev_top = max(prev_top, hi)
    counts["slab_discontinuity"] = gap_count

    total = (counts["3D_overlap"] + counts["underground_overlap"]
             + counts["duplicate_ulpin"] + counts["height_exceed"] + counts["slab_discontinuity"])
    return {"run_id": None, "counts": counts, "total": total, "checks": list(counts)}


async def _assert_conflict(
    conn,
    conflict_type: str,
    parcel_a: str,
    parcel_b: str | None,
    *,
    volume_m3: float | None = None,
    geom_ewkt: str | None = None,
    severity: str = "high",
    description: str = "",
) -> None:
    """Insert a conflict record if an identical open one does not exist."""
    exists = await conn.fetchval(
        """
        SELECT 1 FROM cadastre.conflicts
        WHERE conflict_type = $1 AND parcel_a = $2
          AND parcel_b IS NOT DISTINCT FROM $3 AND status <> 'resolved'
        LIMIT 1
        """,
        conflict_type, parcel_a, parcel_b,
    )
    if exists:
        return
    if geom_ewkt:
        await conn.execute(
            """
            INSERT INTO cadastre.conflicts
                (conflict_type, parcel_a, parcel_b, geometry, volume_m3, severity, description)
            VALUES ($1, $2, $3, ST_GeomFromEWKT($4), $5, $6, $7)
            """,
            conflict_type, parcel_a, parcel_b, geom_ewkt, volume_m3, severity, description,
        )
    else:
        await conn.execute(
            """
            INSERT INTO cadastre.conflicts
                (conflict_type, parcel_a, parcel_b, severity, description)
            VALUES ($1, $2, $3, $4, $5)
            """,
            conflict_type, parcel_a, parcel_b, severity, description,
        )


async def resolve_conflict(conflict_id: int) -> dict:
    conn = db.pool()
    await conn.execute(
        """
        UPDATE cadastre.conflicts
        SET status = 'resolved', resolved_at = now()
        WHERE id = $1
        """,
        conflict_id,
    )
    return {"status": "ok", "resolved_id": conflict_id}


async def list_conflicts(status: str | None = None, conflict_type: str | None = None, limit: int = 200) -> dict:
    where, params = [], []
    if status:
        where.append("status = $%d" % (len(where) + 1))
        params.append(status)
    if conflict_type:
        where.append("conflict_type = $%d" % (len(where) + 1))
        params.append(conflict_type)
    sql_where = ("WHERE " + " AND ".join(where)) if where else ""
    rows = await db.pool().fetch(
        f"""
        SELECT id, conflict_type::text AS conflict_type, parcel_a, parcel_b,
               volume_m3, area_m2, severity, description, status, created_at
        FROM cadastre.conflicts
        {sql_where}
        ORDER BY id
        LIMIT $%d
        """
        % (len(where) + 1),
        *params, limit,
    )
    return {"conflicts": [dict(r) for r in rows], "count": len(rows)}