"""Focus Area — per-building real-data dossier for the demo viewer.

Given a building_id, returns the ground truth / extracted data for that small
area: footprint bbox (for raster cropping), the volumetric parcel stack (floor
+ suite ULPINs), and the point-cloud density inside the bbox — so the viewer
can show *real* ortho / nDSM / LiDAR pixels for just one building.

    GET /api/focus/building/{id}  -> building + bbox + parcels + cloud_count
    GET /api/focus/raster/{name}  -> cropped PNG (bbox window of a GeoTIFF)
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app import db

router = APIRouter(tags=["focus"])

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
_RASTER_NAMES = {"ortho", "dsm", "ndsm", "truth_building_mask"}
_PAD_M = 6.0


def _bbox_from_footprint(fp: dict) -> list[float]:
    coords = fp.get("coordinates") or [[]]
    ring = coords[0]
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return [min(xs) - _PAD_M, min(ys) - _PAD_M, max(xs) + _PAD_M, max(ys) + _PAD_M]


def _parse_bbox(bbox: str) -> list[float]:
    try:
        x0, y0, x1, y1 = (float(v) for v in bbox.split(","))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="bbox=x0,y0,x1,y1") from exc
    return [x0, y0, x1, y1]


async def _cloud_count(bbox: list[float]) -> int:
    from app.services.reconstruction.cloudseg import load_point_cloud
    from app.services.reconstruction.manifest_store import load_manifest, reconstruction_dir

    m = load_manifest(str(DATA_DIR))
    if m is None or not m.cloud_path:
        return 0
    p = reconstruction_dir(str(DATA_DIR)) / m.cloud_path
    if not p.exists():
        return 0
    xyz, _ = load_point_cloud(p)
    x0, y0, x1, y1 = bbox
    sel = (xyz[:, 0] >= x0) & (xyz[:, 0] <= x1) & (xyz[:, 1] >= y0) & (xyz[:, 1] <= y1)
    return int(sel.sum())


@router.get("/api/focus/registered")
async def focus_registered() -> dict:
    """Every building that has a registered photoreal splat (scene preloads these)."""
    real_dir = DATA_DIR / "reconstruction" / "real"
    out = []
    if real_dir.exists():
        for d in sorted(real_dir.iterdir()):
            if not d.is_dir():
                continue
            try:
                bid = int(d.name)
            except ValueError:
                continue
            splat = _splat_for(bid)
            if splat is not None:
                out.append({"building_id": bid, "splat": splat})
    return {"buildings": out}


@router.get("/api/focus/building/{building_id}")
async def focus_building(building_id: int) -> dict:
    from app.services.cadastre import parcels as parcels_svc

    buildings = await parcels_svc.list_buildings()
    b = next((x for x in buildings if x["id"] == building_id), None)
    if b is None:
        raise HTTPException(status_code=404, detail="building not found")

    bbox = _bbox_from_footprint(b["footprint"])
    parcels = await parcels_svc.list_parcels(building_id=building_id, limit=500)
    cloud_count = await _cloud_count(bbox)

    from urllib.parse import quote

    bbox_q = quote(",".join(f"{v:.2f}" for v in bbox))
    return {
        "building": b,
        "bbox": bbox,
        "parcels": parcels["parcels"],
        "parcel_count": parcels["count"],
        "cloud_points": cloud_count,
        "rasters": {
            name: f"/api/focus/raster/{name}?bbox={bbox_q}&max_px=420"
            for name in ("ortho", "ndsm", "truth_building_mask")
        },
        "splat": _splat_for(building_id),
    }


def _splat_for(building_id: int) -> dict | None:
    """Photoreal building (photos -> 3DGS), if a registered splat exists.

    Served both as the raw `.splat` (drei) and as a lightweight colored
    point-cloud (`points.bin`) that renders on any GPU without WebGL data
    textures — most browsers/weak GPUs crash the RGBA32UI splat path.
    """
    real_dir = DATA_DIR / "reconstruction" / "real" / str(building_id)
    splat_file = real_dir / "scene.splat"
    pose_file = real_dir / "pose.json"
    if not (splat_file.exists() and pose_file.exists()):
        return None
    try:
        pose = json.loads(pose_file.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    info: dict = {
        "url": f"/api/real/{building_id}/scene.splat",
        "pose": pose,
        "bytes": splat_file.stat().st_size,
    }
    pts = real_dir / "points.bin"
    if pts.exists():
        info["points_url"] = f"/api/real/{building_id}/points.bin"
        info["point_count"] = int.from_bytes(pts.read_bytes()[:4], "little")
    return info


@router.get("/api/focus/raster/{name}")
async def focus_raster(
    name: str,
    bbox: str = Query(..., description="x0,y0,x1,y1 in local metres"),
    max_px: int = Query(default=420, le=900),
) -> Response:
    if name not in _RASTER_NAMES:
        raise HTTPException(status_code=404, detail=f"unknown raster {name!r}")
    path = DATA_DIR / "raw" / f"{name}.tif"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{name} not generated yet")

    try:
        import numpy as np
        import rasterio
        from PIL import Image
        from rasterio.windows import from_bounds
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    x0, y0, x1, y1 = _parse_bbox(bbox)

    with rasterio.open(path) as ds:
        win = from_bounds(x0, y0, x1, y1, transform=ds.transform)
        # round to integer pixels, boundless so partial windows still render
        win = win.round_offsets().round_lengths()
        data = ds.read(window=win, boundless=True, fill_value=0)

    if data.shape[1] == 0 or data.shape[2] == 0:
        raise HTTPException(status_code=404, detail="bbox outside raster extent")

    if data.shape[0] == 1:
        band = data[0].astype(np.float32)
        lo, hi = np.percentile(band[band != 0], [2, 98]) if (band != 0).any() else (0, 1)
        band = np.clip((band - lo) / max(hi - lo, 1e-6), 0, 1)
        pil = Image.fromarray((band * 255).astype(np.uint8), mode="L").convert("RGB")
    else:
        pil = Image.fromarray(np.transpose(data[:3], (1, 2, 0)).astype(np.uint8), mode="RGB")

    scale = min(1.0, max_px / max(pil.width, pil.height))
    if scale < 1.0:
        pil = pil.resize((max(1, int(pil.width * scale)), max(1, int(pil.height * scale))))

    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
