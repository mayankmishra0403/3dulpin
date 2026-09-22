from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["scene"])


@router.get("/scene")
async def get_scene() -> dict:
    """Assemble the full 3D scene for the web viewer.

    Returns buildings, volumetric parcels, utilities and conflicts in
    UTM-metre coordinates plus the scene origin (UTM offset) so the
    front-end can render in local world space.
    """
    from app.services.cadastre import scene as scene_svc

    return await scene_svc.build_scene()