"""nerfstudio reconstruction artifact endpoints.

    POST /api/reconstruction/run      -> (re)build artifacts by running the
                                         reconstruct pipeline stage
    GET  /api/reconstruction/manifest -> ReconstructionManifest or 404
    GET  /api/reconstruction/cloud    -> capped point cloud for the three.js viewer
                                         (x,y,z[,class] as row arrays)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.services.pipeline import run_pipeline
from app.services.reconstruction.manifest import manifest_to_dict
from app.services.reconstruction.manifest_store import (
    load_manifest,
    reconstruction_dir,
)

router = APIRouter(tags=["reconstruction"])

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
_RUNNING = False


@router.get("/api/reconstruction/manifest")
async def manifest() -> dict:
    m = load_manifest(str(DATA_DIR))
    if m is None:
        raise HTTPException(status_code=404, detail="no reconstruction artifact yet")
    return manifest_to_dict(m)


@router.get("/api/reconstruction/cloud")
async def cloud(limit: int = Query(default=60000, le=250000)) -> dict:
    """Subsampled point cloud for the viewer (3D ULPIN demo fallback to lidar)."""
    m = load_manifest(str(DATA_DIR))
    if m is None:
        raise HTTPException(status_code=404, detail="no reconstruction artifact yet")

    from app.services.reconstruction.cloudseg import load_point_cloud

    p = reconstruction_dir(str(DATA_DIR)) / m.cloud_path
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"cloud file missing: {m.cloud_path}")
    xyz, cls = load_point_cloud(p)

    if len(xyz) > limit:
        idx = _stride(len(xyz), limit)
        xyz, cls = xyz[idx], cls[idx] if cls is not None else None

    out = {
        "count": len(xyz),
        "points": [list(map(lambda v: round(v, 2), row)) for row in xyz.tolist()],
        "has_class": cls is not None,
    }
    if cls is not None:
        out["class"] = cls.tolist()
    return out


def _stride(n: int, limit: int) -> list[int]:
    return list(range(0, n, max(1, n // limit)))


@router.post("/api/reconstruction/run")
async def run() -> dict:
    """(Re)build reconstruction artifacts via the reconstruct pipeline stage."""
    global _RUNNING
    if _RUNNING:
        raise HTTPException(status_code=409, detail="reconstruction already running")
    _RUNNING = True
    try:
        report = run_pipeline(str(DATA_DIR), stage="reconstruct")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        _RUNNING = False

    m = load_manifest(str(DATA_DIR))
    return {
        "ok": True,
        "source_note": report.get("source_note"),
        "metrics": report["evaluation"],
        "manifest": manifest_to_dict(m) if m is not None else None,
    }