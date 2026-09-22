from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/cadastre", tags=["cadastre"])


@router.get("/parcels")
async def list_parcels(
    category: str | None = Query(default=None),
    building_id: int | None = Query(default=None),
    limit: int = Query(default=500, le=2000),
) -> dict:
    from app.services.cadastre import parcels as parcels_svc

    return await parcels_svc.list_parcels(category=category, building_id=building_id, limit=limit)


@router.get("/parcels/{parcel_id}")
async def get_parcel(parcel_id: int) -> dict:
    from app.services.cadastre import parcels as parcels_svc

    row = await parcels_svc.get_parcel(parcel_id)
    if row is None:
        raise HTTPException(status_code=404, detail="parcel not found")
    return row


@router.get("/buildings")
async def list_buildings() -> dict:
    from app.services.cadastre import parcels as parcels_svc

    return {"buildings": await parcels_svc.list_buildings()}


@router.get("/parcels/by-ulpin/{ulpin3d}")
async def get_parcel_by_ulpin(ulpin3d: str) -> dict:
    from app.services.cadastre import parcels as parcels_svc

    row = await parcels_svc.get_parcel_by_ulpin(ulpin3d)
    if row is None:
        raise HTTPException(status_code=404, detail="no parcel with this 3D ULPIN")
    return row