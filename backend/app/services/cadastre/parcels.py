"""Parcel & building queries for the cadastre API."""

from __future__ import annotations

import json

from app import db


def _parcel_row(r) -> dict:
    rights = r.get("rights_summary") or ""
    owner_name = "State / Municipal Authority"
    right_type = "Public Right"
    if " · " in rights:
        parts = rights.split(" · ")
        owner_name = parts[0]
        right_type = parts[1]
    return {
        "id": r["id"],
        "ulpin3d": r["ulpin3d"],
        "base_ulpin": r["base_ulpin"],
        "building_id": r["building_id"],
        "category": r["category"],
        "level_no": r["level_no"],
        "unit_no": r["unit_no"],
        "zmin": r["zmin"],
        "zmax": r["zmax"],
        "usage": r["usage"],
        "rights_summary": r["rights_summary"],
        "status": r["status"],
        "volume_m3": r["volume_m3"],
        "built_up_area_m2": r["built_up_area_m2"],
        "centroid": [r["cx"], r["cy"], r["cz"]],
        "footprint": json.loads(r["footprint_geojson"]),
        "owner_name": owner_name,
        "right_type": right_type,
    }


async def list_parcels(category: str | None = None, building_id: int | None = None, limit: int = 500) -> dict:
    where = []
    params: list = []
    if category:
        where.append("p.category = $%d::cadastre.category" % (len(where) + 1))
        params.append(category)
    if building_id:
        where.append("p.building_id = $%d" % (len(where) + 1))
        params.append(building_id)
    sql_where = ("WHERE " + " AND ".join(where)) if where else ""

    rows = await db.pool().fetch(
        f"""
        SELECT p.*,
               ST_X(ST_Centroid(p.footprint))::float8 AS cx,
               ST_Y(ST_Centroid(p.footprint))::float8 AS cy,
               ((p.zmin + p.zmax) / 2.0)::float8 AS cz,
               ST_AsGeoJSON(p.footprint, 6) AS footprint_geojson
        FROM cadastre.parcels_3d p
        {sql_where}
        ORDER BY p.zmin, p.level_no
        LIMIT $%d
        """
        % (len(where) + 1),
        *params,
        limit,
    )
    return {"parcels": [_parcel_row(r) for r in rows], "count": len(rows)}


async def get_parcel(parcel_id: int) -> dict | None:
    row = await db.pool().fetchrow(
        """
        SELECT p.*,
               ST_X(ST_Centroid(p.footprint))::float8 AS cx,
               ST_Y(ST_Centroid(p.footprint))::float8 AS cy,
               ((p.zmin + p.zmax) / 2.0)::float8 AS cz,
               ST_AsGeoJSON(p.footprint, 6) AS footprint_geojson
        FROM cadastre.parcels_3d p
        WHERE p.id = $1
        """,
        parcel_id,
    )
    return _parcel_row(row) if row else None


async def get_parcel_by_ulpin(ulpin3d: str) -> dict | None:
    row = await db.pool().fetchrow(
        """
        SELECT p.*,
               ST_X(ST_Centroid(p.footprint))::float8 AS cx,
               ST_Y(ST_Centroid(p.footprint))::float8 AS cy,
               ((p.zmin + p.zmax) / 2.0)::float8 AS cz,
               ST_AsGeoJSON(p.footprint, 6) AS footprint_geojson
        FROM cadastre.parcels_3d p
        WHERE p.ulpin3d = $1
        """,
        ulpin3d,
    )
    return _parcel_row(row) if row else None


async def list_buildings() -> list[dict]:
    rows = await db.pool().fetch(
        """
        SELECT id, name, floor_count, ground_z, height_m, roof_type, source,
               ST_X(ST_Centroid(footprint))::float8 AS cx,
               ST_Y(ST_Centroid(footprint))::float8 AS cy,
               ST_AsGeoJSON(footprint, 6) AS footprint_geojson
        FROM cadastre.buildings
        ORDER BY id
        """
    )
    return [
        dict(
            id=r["id"],
            name=r["name"],
            floor_count=r["floor_count"],
            ground_z=r["ground_z"],
            height_m=r["height_m"],
            roof_type=r["roof_type"],
            source=r["source"],
            cx=r["cx"],
            cy=r["cy"],
            footprint=json.loads(r["footprint_geojson"]),
        )
        for r in rows
    ]