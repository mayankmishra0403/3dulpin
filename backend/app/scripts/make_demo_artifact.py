"""Create a local reconstruction artifact from the synthetic LiDAR.

Lets the reconstruction stage exercise the *manifest contract* on a laptop with
no GPU: converts ``data/raw/pointcloud.las`` into the same artifact set a
nerfstudio GPU export would produce —

    data/reconstruction/pointcloud.ply   (binary PLY, x y z + class)
    data/reconstruction/manifest.json    (ReconstructionManifest, DONE)
    data/reconstruction/dem|dsm|ndsm.tif (gridded rasters)

Run: ``PYTHONPATH=backend python backend/app/scripts/make_demo_artifact.py``

A real nerfstudio run (``reconstruct_gpu.py``) replaces this file with a true
splatfacto export; the app cannot tell the difference.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend"))


def write_ply(path: Path, xyz: np.ndarray, cls: np.ndarray | None = None) -> None:
    n = len(xyz)
    cols = [xyz[:, 0], xyz[:, 1], xyz[:, 2]]
    names = ["property float x", "property float y", "property float z"]
    if cls is not None:
        cols.append(cls.astype(np.float32))
        names.append("property float class")
    header = ("ply\nformat binary_little_endian 1.0\n"
              f"element vertex {n}\n"
              + "\n".join(names) + "\nend_header\n").encode()
    body = np.column_stack(cols).astype(np.float32)
    with open(path, "wb") as f:
        f.write(header)
        f.write(body.tobytes())


def main() -> int:
    from app.services.reconstruction.cloudseg import load_point_cloud
    from app.services.reconstruction.cloud2raster import cloud_to_rasters
    from app.services.reconstruction.manifest import (
        GeoreferenceParams,
        ReconStatus,
        ReconstructionManifest,
    )
    from app.services.reconstruction.manifest_store import save_manifest

    data = REPO / "data"
    xyz, cls = load_point_cloud(data / "raw" / "pointcloud.las")

    out = data / "reconstruction"
    out.mkdir(parents=True, exist_ok=True)
    write_ply(out / "pointcloud.ply", xyz, cls)

    rst = (data / "raw" / "rasters.json").read_text()
    meta = json.loads(rst)
    extent = (float(meta["west"]), float(meta["north"]),
              int(meta["width"]), int(meta["height"]))
    cloud_to_rasters(xyz, out_dir=out, cls=cls, extent=extent)

    save_manifest(ReconstructionManifest(
        method="lidar",
        source="synthetic_lidar",
        status=ReconStatus.DONE,
        cloud_path="pointcloud.ply",
        georeference=GeoreferenceParams(scale=1.0, strategy="pose_seed"),
        stats={"points": int(len(xyz))},
        note="offline demo artifact (synthetic LAS → PLY); a GPU "
             "splatfacto export replaces it",
    ), data)
    print(f"artifact written -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())