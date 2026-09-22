"""Populate the PostGIS cadastre from the generated demo dataset.

Loads:
  * data/raw/parcels_2d.geojson     -> cadastre.parcels_2d
  * data/raw/buildings.geojson      -> cadastre.buildings
  * data/raw/utilities.geojson      -> cadastre.utilities
  * data/truth/volumes.geojson      -> cadastre.parcels_3d (+ owners, ownership)

Idempotent: wipes the four tables (FK order) then reseeds, then runs
topology validation and records an audit entry.

Usage (from repo root, backend venv active):
    PYTHONPATH=backend .venv/bin/python -m app.scripts.seed [data_dir]
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import asyncpg  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.cadastre import prisms  # noqa: E402
from app.services.ulpin import ulpin as ulpin_svc  # noqa: E402

CATEGORIES = {
    "surface", "floor", "suite", "underground", "parking",
    "air_right", "utility_network", "metro_tunnel", "structure",
}


async def seed(data_dir: str = "data") -> dict:
    conn = await asyncpg.connect(settings.database_url)
    try:
        raw = Path(data_dir) / "raw"
        truth = Path(data_dir) / "truth"

        parcels2d = json.loads((raw / "parcels_2d.geojson").read_text())
        buildings = json.loads((raw / "buildings.geojson").read_text())
        utilities = json.loads((raw / "utilities.geojson").read_text())
        volumes = json.loads((truth / "volumes.geojson").read_text())

        async with conn.transaction():
            # ---- wipe ---------------------------------------------------
            await conn.execute("TRUNCATE cadastre.ownership, cadastre.conflicts, cadastre.utilities, "
                               "cadastre.parcels_3d, cadastre.buildings, cadastre.parcels_2d, "
                               "cadastre.owners, cadastre.audit, cadastre.pipeline_runs CASCADE")

            locality = ulpin_svc.demo_locality()

            # ---- parcels_2d ---------------------------------------------
            pid_to_id: dict[int, int] = {}
            for f in parcels2d["features"]:
                props = f["properties"]
                ring = f["geometry"]["coordinates"][0]
                geom_wkt = prisms.footprint_ring_wkt(ring)
                base = props.get("ulpin") or locality.base(props["parcel_no"])
                pid_to_id[props["pid"]] = await conn.fetchval(
                    """
                    INSERT INTO cadastre.parcels_2d
                        (ulpin, state_code, district_code, sub_district_code, village_code,
                         parcel_no, geom, area_m2, usage)
                    VALUES ($1, $2, $3, $4, $5, $6, ST_GeomFromText($7, 32643),
                            ST_Area(ST_GeomFromText($7, 32643)), $8)
                    RETURNING id
                    """,
                    base, locality.state_code, locality.district_code,
                    locality.sub_district_code, locality.village_code,
                    str(props["parcel_no"]), geom_wkt, props["usage"],
                )

            # ---- buildings ----------------------------------------------
            bid_to_id: dict[int, int] = {}
            for f in buildings["features"]:
                props = f["properties"]
                ring = f["geometry"]["coordinates"][0]
                geom_wkt = prisms.footprint_ring_wkt(ring)
                bid_to_id[props["bid"]] = await conn.fetchval(
                    """
                    INSERT INTO cadastre.buildings
                        (name, parcel2d_id, footprint, floor_count,
                         ground_z, height_m, roof_type, source)
                    VALUES ($1, $2, ST_GeomFromText($3, 32643), $4, $5, $6, $7, 'truth')
                    RETURNING id
                    """,
                    props["name"], pid_to_id[props["parcel_id"]], geom_wkt,
                    props["floor_count"], props["ground_z"], props["height_m"],
                    props["roof_type"],
                )

            # ---- owners -------------------------------------------------
            owner_names = {v["properties"]["owner"] for v in volumes["features"]}
            owner_name_to_id: dict[str, int] = {}
            for name in sorted(owner_names):
                owner_name_to_id[name] = await conn.fetchval(
                    "INSERT INTO cadastre.owners (full_name) VALUES ($1) RETURNING id", name
                )

            # ---- parcels_3d + ownership --------------------------------
            inserted = 0
            for v in volumes["features"]:
                props = v["properties"]
                ring = v["geometry"]["coordinates"][0]
                if props["category"] not in CATEGORIES:
                    raise ValueError(f"unknown category {props['category']}")
                zmin, zmax = props["zmin"], props["zmax"]
                footprint_wkt = prisms.footprint_ring_wkt(ring)
                solid_ewkt = prisms.prism_ewkt(ring, zmin, zmax)
                rights = f"{props['owner']} · {props['right_type']}"
                base_ulpin = props["base_ulpin"]
                if props["category"] in ("utility_network", "metro_tunnel"):
                    base_ulpin = None  # network corridors are not surface parcels
                p3d_id = await conn.fetchval(
                    """
                    INSERT INTO cadastre.parcels_3d
                        (ulpin3d, base_ulpin, building_id, category, level_no, unit_no,
                         zmin, zmax, footprint, solid, centroid, built_up_area_m2, volume_m3,
                         usage, rights_summary, status)
                    VALUES ($1, $2, $3, $4::cadastre.category, $5, $6,
                            $7, $8,
                            ST_GeomFromText($9, 32643),
                            ST_GeomFromEWKT($10),
                            ST_Force3DZ(ST_Centroid(ST_GeomFromText($9, 32643))),
                            ST_Area(ST_GeomFromText($9, 32643)),
                            ST_Area(ST_GeomFromText($9, 32643)) * ($8::float8 - $7::float8),
                            $11, $12, 'active')
                    RETURNING id
                    """,
                    props["ulpin3d"], base_ulpin,
                    bid_to_id.get(props["building_id"]),
                    props["category"], props["level_no"], props["unit_no"],
                    zmin, zmax, footprint_wkt, solid_ewkt,
                    props["usage"], rights,
                )
                owner_id = owner_name_to_id[props["owner"]]
                await conn.execute(
                    """
                    INSERT INTO cadastre.ownership (parcel3d_id, owner_id, share, right_type)
                    VALUES ($1, $2, 1.0, $3)
                    """,
                    p3d_id, owner_id, props["right_type"],
                )
                inserted += 1

            # ---- utilities ---------------------------------------------
            for f in utilities["features"]:
                props = f["properties"]
                ring = f["geometry"]["coordinates"][0]
                # centreline along the longitudinal axis at mid-depth
                xs = [p[0] for p in ring]
                ys = [p[1] for p in ring]
                x0, x1 = min(xs), max(xs)
                y0, y1 = min(ys), max(ys)
                zm = (props["zmin"] + props["zmax"]) / 2.0
                if (x1 - x0) >= (y1 - y0):
                    line = [(x0, (y0 + y1) / 2.0), (x1, (y0 + y1) / 2.0)]
                else:
                    line = [((x0 + x1) / 2.0, y0), ((x0 + x1) / 2.0, y1)]
                axis_wkt = "SRID=32643;MULTILINESTRINGZ((" + \
                    ", ".join(f"{px} {py} {zm}" for px, py in line) + "))"
                depth = -props["zmax"] if props["zmax"] < 0 else props["zmin"]
                await conn.execute(
                    """
                    INSERT INTO cadastre.utilities
                        (type, operator, service_geometry, depth_m, diameter_m)
                    VALUES ($1, $2, ST_GeomFromEWKT($3), $4, $5)
                    """,
                    props["kind"], props["operator"], axis_wkt,
                    round(float(depth), 2), props["diameter_m"],
                )

            # ---- audit + validation ------------------------------------
            await conn.execute(
                """
                INSERT INTO cadastre.audit (action, actor, detail)
                VALUES ('create', 'seed', $1::jsonb)
                """,
                json.dumps({"kind": "demo-seed", "parcels_3d": inserted}),
            )

        # validation (outside the truncate transaction, on the app pool)
        from app import db
        from app.services.cadastre import validation as val_svc

        await db.connect()
        try:
            result = await val_svc.run_validation()
        finally:
            await db.close()

        return {
            "parcels_2d": len(parcels2d["features"]),
            "buildings": len(buildings["features"]),
            "parcels_3d": inserted,
            "owners": len(owner_names),
            "utilities": len(utilities["features"]),
            "validation": result["counts"],
        }
    finally:
        await conn.close()


async def main() -> None:
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    result = await seed(data_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())