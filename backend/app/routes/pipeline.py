"""AI extraction pipeline endpoints.

    POST /api/pipeline/run       -> execute the extraction + evaluation
    GET  /api/pipeline/last      -> latest persisted run metrics
    GET  /api/pipeline/parcels   -> detected parcels as GeoJSON (viewer overlay)
    GET  /api/raster/{name}      -> serve a generated GeoTIFF
    GET  /api/raster/{name}/png  -> grayscale/colour PNG preview of a raster
"""

import io
import json
from pathlib import Path

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app import db
from app.services.pipeline import run_pipeline

router = APIRouter(tags=["pipeline"])

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
_RASTER_NAMES = {"dem", "dsm", "ndsm", "ortho", "truth_building_mask"}
_LAST: dict | None = None


@router.post("/api/pipeline/run")
async def run(stage: str = Query(default="extract"), data_dir: str = Query(default=None)) -> dict:
    """Run the extraction pipeline (nDSM baseline or point-cloud reconstruction)."""
    global _LAST
    target = data_dir or str(DATA_DIR)

    try:
        report = run_pipeline(target, stage=stage)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=f"dataset not found: {exc}") from exc

    metrics = {
        "stage": report["stage"],
        "footprints_detected": report["footprints_detected"],
        **{k: report["evaluation"][k] for k in
           ("detected_buildings", "truth_buildings", "matched_buildings",
            "mask_iou", "floor_mae", "ulpins_assigned", "ulpins_valid")},
        "parcel_counts": report["evaluation"]["parcel_counts"],
    }
    _LAST = {"metrics": metrics, "parcels": report["parcels"]}

    run_id = None
    try:
        run_id = await db.pool().fetchval(
            """
            INSERT INTO cadastre.pipeline_runs (dataset, stage, metrics, finished_at)
            VALUES ($1, $2, $3::jsonb, now())
            RETURNING id
            """,
            target, f"{stage}:{report.get('source_note') or 'extract'}", json.dumps(metrics),
        )
        await db.pool().execute(
            "INSERT INTO cadastre.audit (action, actor, detail) VALUES ('validate', 'pipeline', $1::jsonb)",
            json.dumps({"pipeline_run": run_id, "metrics": metrics}),
        )
    except Exception:  # noqa: BLE001 - DB persistence is best-effort
        run_id = None

    resp = {"run_id": run_id, "metrics": metrics,
            "building_matches": report["evaluation"]["building_matches"]}
    if report.get("source_note"):
        resp["source_note"] = report["source_note"]
    if report.get("reconstruction"):
        resp["reconstruction"] = report["reconstruction"]
    return resp


@router.get("/api/pipeline/last")
async def last() -> dict:
    """Latest persisted run metrics, falling back to in-memory report."""
    try:
        row = await db.pool().fetchrow(
            "SELECT id, dataset, metrics, started_at, finished_at "
            "FROM cadastre.pipeline_runs ORDER BY id DESC LIMIT 1"
        )
        if row:
            return {"run_id": row["id"], "dataset": row["dataset"],
                    "metrics": json.loads(row["metrics"]) if isinstance(row["metrics"], str) else row["metrics"],
                    "started_at": row["started_at"], "finished_at": row["finished_at"]}
    except Exception:  # noqa: BLE001
        pass
    if _LAST is not None:
        return {"run_id": None, "metrics": _LAST["metrics"], "source": "memory"}
    raise HTTPException(status_code=404, detail="no pipeline run yet")


@router.get("/api/pipeline/parcels")
async def parcels(limit: int = Query(default=500, le=5000)) -> dict:
    """Detected volumetric parcels (from the last run) as a GeoJSON overlay."""
    if _LAST is None:
        # run on demand so the endpoint is useful standalone
        try:
            report = run_pipeline(str(DATA_DIR))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        globals()["_LAST"] = {"metrics": report["evaluation"], "parcels": report["parcels"]}
    feats = []
    for p in _LAST["parcels"][:limit]:
        feats.append({
            "type": "Feature",
            "properties": {k: p[k] for k in ("ulpin3d", "category", "level_no", "unit_no", "usage", "zmin", "zmax")},
            "geometry": {"type": "Polygon", "coordinates": [[list(pt) for pt in p["ring"]]]},
        })
    return {"type": "FeatureCollection", "features": feats}


@router.get("/api/raster/{name}")
async def raster(name: str) -> Response:
    if name not in _RASTER_NAMES:
        raise HTTPException(status_code=404, detail=f"unknown raster {name!r}")
    path = DATA_DIR / "raw" / f"{name}.tif"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{name} not generated yet")
    return Response(content=path.read_bytes(), media_type="image/tiff",
                    headers={"Content-Disposition": f'inline; filename="{name}.tif"'})


@router.get("/api/raster/{name}/png")
async def raster_png(name: str, max_px: int = Query(default=900, le=2000)) -> Response:
    if name not in _RASTER_NAMES:
        raise HTTPException(status_code=404, detail=f"unknown raster {name!r}")
    try:
        from PIL import Image
        import rasterio
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    path = DATA_DIR / "raw" / f"{name}.tif"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{name} not generated yet")

    with rasterio.open(path) as ds:
        img = ds.read()
    if img.shape[0] == 1:
        band = img[0].astype(np.float32)
        lo, hi = np.percentile(band, [2, 98])
        band = np.clip((band - lo) / max(hi - lo, 1e-6), 0, 1)
        out = (band * 255).astype(np.uint8)
        pil = Image.fromarray(out, mode="L").convert("RGB")
    else:
        pil = Image.fromarray(np.transpose(img[:3], (1, 2, 0)).astype(np.uint8), mode="RGB")

    scale = min(1.0, max_px / max(pil.width, pil.height))
    if scale < 1.0:
        pil = pil.resize((max(1, int(pil.width * scale)), max(1, int(pil.height * scale))))

    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
