"""Headless nerfstudio reconstruction driver — RUN ON A CUDA WORKER.

Feed it the synthetic drone views (``data/raw/drone_views``) or a real drone
capture and it:

  1. prepares a dataset (COLMAP for real captures, or the seeded UTM poses
     from ``transforms.json`` via ``--skip-colmap``),
  2. trains ``splatfacto`` (default) and exports a PLY point cloud,
  3. georeferences the export into EPSG:32643 (GCP pairs, or pose-seed identity),
  4. writes the artifact contract consumed by the app::

        data/reconstruction/pointcloud.ply   (CRS-aligned cloud)
        data/reconstruction/manifest.json    (ReconstructionManifest)
        data/reconstruction/dsm.tif …
                                     (gridded DEM/DSM/nDSM, optional)

The FastAPI backend never trains — it only reads these artifacts, so the demo
runs fully offline afterwards.

Usage (GPU host, from repo root):
  PYTHONPATH=backend python backend/app/scripts/reconstruct_gpu.py \
      --data data/raw/drone_views \
      --skip-colmap --method splatfacto --max-iter 20000 \
      --gcp-json data/raw/drone_views/gcps.json   # or --pose-seed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend"))


def _load_cloud(path: Path) -> tuple[np.ndarray, np.ndarray | None]:
    from app.services.reconstruction.cloudseg import load_point_cloud

    return load_point_cloud(path)


def _georeference(cloud: np.ndarray, args) -> tuple[np.ndarray, dict]:
    """Return (cloud_in_CRS, georef_dict) for the manifest."""
    from app.services.reconstruction.georeference import apply_transform, make_params

    if args.gcp_json:
        gcps = json.loads(Path(args.gcp_json).read_text())
        src = np.array([g["local"][:2] for g in gcps], dtype=float)
        dst = np.array([g["target"][:2] for g in gcps], dtype=float)
        src_z = np.array([g["local"][2] for g in gcps], dtype=float)
        dst_z = np.array([g["target"][2] for g in gcps], dtype=float)
        geo = make_params(src, dst, src_z, dst_z, strategy="gcp")
        return apply_transform(cloud, geo), geo.to_dict()
    if args.pose_seed:
        # synthetic path: poses already seeded in UTM; nerfstudio scale kept
        # small for a demo locality — a near-identity map is recorded honestly.
        from app.services.reconstruction.manifest import GeoreferenceParams

        geo = GeoreferenceParams(scale=1.0, strategy="pose_seed",
                                 note="pose-seeded transforms.json; hip shot only")
        return cloud, geo.to_dict()
    raise SystemExit("reconstruct_gpu: provide --gcp-json or --pose-seed")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True)
    ap.add_argument("--method", default="splatfacto")
    ap.add_argument("--max-iter", type=int, default=20_000)
    ap.add_argument("--skip-colmap", action="store_true",
                    help="true when data/ has a transforms.json (seeded poses)")
    ap.add_argument("--gcp-json", default=None, help="[{local:[x,y,z],target:[X,Y,Z]}]")
    ap.add_argument("--pose-seed", action="store_true",
                    help="pose-seeded synthetic dataset; identity georeference")
    ap.add_argument("--data-dir", default=str(REPO / "data"),
                    help="repo data dir (artifacts land in <data-dir>/reconstruction)")
    args = ap.parse_args()

    from app.services.reconstruction import (
        ReconStatus,
        cloud_to_rasters,
        export_pointcloud,
        process_data,
        train,
    )
    from app.services.reconstruction.manifest import (
        GeoreferenceParams,
        ReconstructionManifest,
    )
    from app.services.reconstruction.manifest_store import save_manifest, set_status
    from app.services.reconstruction.nerfrunner import NerfRunnerConfig

    run_dir = Path(args.data_dir) / "reconstruction"
    run_dir.mkdir(parents=True, exist_ok=True)
    set_status(args.data_dir, ReconStatus.RUNNING)

    cfg = NerfRunnerConfig(method=args.method, data_path=args.data,
                           output_dir=run_dir / "ts", max_iter=args.max_iter)

    if args.skip_colmap:
        dataset = Path(args.data)          # transforms.json already present
    else:
        dataset = process_data(cfg)
    cfg.dataset_dir = dataset

    ts_out = train(cfg)
    configs = sorted(ts_out.rglob("config.yml"))
    if not configs:
        raise SystemExit(f"no nerfstudio config.yml under {ts_out}")
    export_dir = export_pointcloud(cfg, configs[-1])
    cloud_path = run_dir / "pointcloud.ply"
    _rename_latest_ply(export_dir, cloud_path)

    xyz, cls = _load_cloud(cloud_path)
    cloud, geo = _georeference(xyz, args)
    geo_obj = GeoreferenceParams(**geo)

    try:
        cloud_to_rasters(cloud, out_dir=run_dir, cls=cls, extent=None)
    except Exception:  # noqa: BLE001 — gridding is best-effort
        pass

    manifest = ReconstructionManifest(
        method=args.method,
        source="synthetic_drone" if args.pose_seed else "upload",
        status=ReconStatus.DONE,
        cloud_path="pointcloud.ply",
        georeference=geo_obj,
        stats={
            "points": int(cloud.shape[0]),
            "extent_x_min_m": round(float(cloud[:, 0].min()), 2),
            "extent_y_min_m": round(float(cloud[:, 1].min()), 2),
            "zpct_95_m": round(float(np.percentile(cloud[:, 2], 95)), 2),
        },
        note="georeference via " + ("GCP fit" if args.gcp_json else "pose-seed"),
    )
    save_manifest(manifest, args.data_dir)
    print(f"[reconstruct_gpu] artifacts -> {run_dir}")
    return 0


def _rename_latest_ply(export_dir: Path, cloud_path: Path) -> None:
    plies = sorted(export_dir.glob("*.ply"))
    if not plies:
        raise SystemExit(f"no PLY exported in {export_dir}")
    plies[-1].replace(cloud_path)


if __name__ == "__main__":
    sys.exit(main())