"""Assemble the full 3D scene payload for the web viewer."""

from __future__ import annotations

import json

from app import db


async def build_scene() -> dict:
    conn = db.pool()

    # Scene origin: south-west corner of the cadastre extent (UTM metres).
    origin_row = await conn.fetchrow(
        """
        SELECT ST_XMin(ext)::float8 AS x, ST_YMin(ext)::float8 AS y, 0.0 AS z
        FROM (SELECT ST_Extent(geom) AS ext FROM cadastre.parcels_2d) s
        """
    )
    origin = [float(origin_row["x"] or 0), float(origin_row["y"] or 0), 0.0]
    if not origin_row["x"]:
        origin = [0.0, 0.0, 0.0]

    buildings = [
        dict(
            id=r["id"],
            name=r["name"],
            floor_count=r["floor_count"],
            ground_z=r["ground_z"],
            height_m=r["height_m"],
            footprint=json.loads(r["footprint_geojson"]),
        )
        for r in await conn.fetch(
            """
            SELECT id, name, floor_count, ground_z, height_m,
                   ST_AsGeoJSON(footprint, 6) AS footprint_geojson
            FROM cadastre.buildings
            ORDER BY id
            """
        )
    ]

    parcels = [
        dict(
            id=r["id"],
            ulpin3d=r["ulpin3d"],
            base_ulpin=r["base_ulpin"],
            category=r["category"],
            level_no=r["level_no"],
            unit_no=r["unit_no"],
            building_id=r["building_id"],
            zmin=r["zmin"],
            zmax=r["zmax"],
            usage=r["usage"],
            rights_summary=r["rights_summary"],
            status=r["status"],
            volume_m3=r["volume_m3"],
            built_up_area_m2=r["built_up_area_m2"],
            centroid=[r["cx"], r["cy"], r["cz"]],
            footprint=json.loads(r["footprint_geojson"]),
            owner_name=r["rights_summary"].split(" · ")[0] if r["rights_summary"] and " · " in r["rights_summary"] else "State Authority",
            right_type=r["rights_summary"].split(" · ")[1] if r["rights_summary"] and " · " in r["rights_summary"] else "Public Right",
        )
        for r in await conn.fetch(
            """
            SELECT p.id, p.ulpin3d, p.base_ulpin, p.category, p.level_no, p.unit_no,
                   p.building_id, p.zmin, p.zmax, p.usage, p.rights_summary,
                   p.status, p.volume_m3, p.built_up_area_m2,
                   ST_X(ST_Centroid(p.footprint))::float8 AS cx,
                   ST_Y(ST_Centroid(p.footprint))::float8 AS cy,
                   ((p.zmin + p.zmax) / 2.0)::float8 AS cz,
                   ST_AsGeoJSON(p.footprint, 6) AS footprint_geojson
            FROM cadastre.parcels_3d p
            ORDER BY p.id
            """
        )
    ]

    utilities = [
        dict(
            id=r["id"],
            type=r["type"],
            operator=r["operator"],
            zmin=r["zmin"],
            zmax=r["zmax"],
            depth_m=r["depth_m"],
            diameter_m=r["diameter_m"],
            service=json.loads(r["service_geojson"]),
        )
        for r in await conn.fetch(
            """
            SELECT id, type, operator,
                   ST_ZMin(service_geometry)::float8 AS zmin,
                   ST_ZMax(service_geometry)::float8 AS zmax,
                   depth_m, diameter_m,
                   ST_AsGeoJSON(service_geometry, 6) AS service_geojson
            FROM cadastre.utilities
            ORDER BY id
            """
        )
    ]

    conflicts = [
        dict(
            id=r["id"],
            conflict_type=r["conflict_type"],
            parcel_a=r["parcel_a"],
            parcel_b=r["parcel_b"],
            volume_m3=r["volume_m3"],
            area_m2=r["area_m2"],
            severity=r["severity"],
            description=r["description"],
            status=r["status"],
        )
        for r in await conn.fetch(
            """
            SELECT id, conflict_type, parcel_a, parcel_b, volume_m3, area_m2,
                   severity, description, status
            FROM cadastre.conflicts
            ORDER BY id
            """
        )
    ]

    stats = await _stats(conn)

    return {
        "origin": origin,
        "buildings": buildings,
        "parcels": parcels,
        "utilities": utilities,
        "conflicts": conflicts,
        "stats": stats,
    }


async def _stats(conn) -> dict:
    by_cat = dict(
        (r["category"], r["n"])
        for r in await conn.fetch(
            "SELECT category::text AS category, count(*) AS n "
            "FROM cadastre.parcels_3d GROUP BY category"
        )
    )
    totals = await conn.fetchrow(
        """
        SELECT count(*)::int AS total_parcels,
               COALESCE(sum(volume_m3),0)::float8 AS total_volume_m3,
               COALESCE(sum(built_up_area_m2),0)::float8 AS total_area_m2,
               (SELECT count(*) FROM cadastre.buildings)::int AS building_count,
               (SELECT count(*) FROM cadastre.conflicts WHERE status <> 'resolved')::int AS open_conflicts
        FROM cadastre.parcels_3d
        """
    )
    utility_km = await conn.fetchval(
        "SELECT COALESCE(sum(ST_Length(service_geometry))/1000.0, 0.0)::float8 "
        "FROM cadastre.utilities"
    )
    return {
        "by_category": by_cat,
        "total_parcels": totals["total_parcels"],
        "total_volume_m3": totals["total_volume_m3"],
        "total_built_up_area_m2": totals["total_area_m2"],
        "building_count": totals["building_count"],
        "open_conflicts": totals["open_conflicts"],
        "utility_km": utility_km,
    }