from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.post("/run")
async def run_validation() -> dict:
    """Run 3D topology validation across all volumetric parcels."""
    from app.services.cadastre import validation as val_svc

    return await val_svc.run_validation()


@router.get("/conflicts")
async def list_conflicts(
    status: str | None = Query(default=None),
    conflict_type: str | None = Query(default=None),
    limit: int = Query(default=200, le=2000),
) -> dict:
    from app.services.cadastre import validation as val_svc

    return await val_svc.list_conflicts(status=status, conflict_type=conflict_type, limit=limit)


@router.post("/resolve/{conflict_id}")
async def resolve_conflict(conflict_id: int) -> dict:
    from app.services.cadastre import validation as val_svc

    return await val_svc.resolve_conflict(conflict_id)