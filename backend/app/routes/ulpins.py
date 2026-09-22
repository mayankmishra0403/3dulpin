from fastapi import APIRouter, HTTPException

from app.models.schemas import ULPINGenerateIn, ULPINOut, ULPINParseOut
from app.services.ulpin import ulpin as ulpin_svc

router = APIRouter(prefix="/api/ulpins", tags=["ulpins"])


@router.get("/parse/{code}")
async def parse(code: str) -> ULPINParseOut:
    """Validate and parse a 3D ULPIN into its semantic components."""
    try:
        parsed = ulpin_svc.ULPIN3D.parse(code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    base = ulpin_svc.parse_base_ulpin(parsed.base_ulpin)
    base.pop("value", None)
    front = parsed.front
    from app.services.ulpin.ulpin import checksum

    return ULPINParseOut(
        value=parsed.value,
        front=front,
        base_ulpin=parsed.base_ulpin,
        category=parsed.category,
        level_no=parsed.level_no,
        unit_no=parsed.unit_no,
        checksum_ok=checksum(front) == parsed.value[-1],
        **base,
    )


@router.post("/generate")
async def generate(req: ULPINGenerateIn) -> ULPINOut:
    """Generate a single 3D ULPIN for a base parcel + vertical descriptor."""
    obj = ulpin_svc.ULPIN3D(
        base_ulpin=req.base_ulpin,
        category=req.category,
        level_no=req.level_no,
        unit_no=req.unit_no,
        asset=req.asset,
    )
    front = obj.front
    from app.services.ulpin.ulpin import checksum

    return ULPINOut(
        value=obj.value,
        front=front,
        base_ulpin=req.base_ulpin,
        category=obj.category,
        level_no=obj.level_no,
        unit_no=obj.unit_no,
        checksum_ok=checksum(front) == obj.value[-1],
    )


@router.get("/base/{parcel_no}")
async def base_ulpin(parcel_no: str) -> dict:
    """Compose (and parse) a 14-char base ULPIN for the demo locality."""
    locality = ulpin_svc.demo_locality()
    value = locality.base(parcel_no)
    return {"value": value, **ulpin_svc.parse_base_ulpin(value)}