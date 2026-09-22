from fastapi import APIRouter

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def stats() -> dict:
    from app.services.cadastre import dashboard as dash_svc

    return await dash_svc.stats()