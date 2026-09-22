"""Register a *real* building reconstructed from photos as a photoreal splat.

Flow: real drone/phone photos -> (GPU/Colab) nerfstudio splatfacto ->
``ns-export gaussian-splat --load-config ... --output-dir exports/splat``
-> an INRIA-format ``point_cloud/iteration_<N>/point_cloud.ply``.

This script converts that PLY into the browser-ready ``.splat`` format,
solves the georeference (nerf-local frame -> the cadastre local frame) from a
few surveyed GCP pairs, and writes the artifact the app serves::

    data/reconstruction/real/{building_id}/scene.splat   (what drei <Splat> renders)
    data/reconstruction/real/{building_id}/pose.json     (position/rotation/scale)

Run (from repo root):
    PYTHONPATH=backend python backend/app/scripts/register_real_building.py \
        --building-id 1 \
        --input exports/splat/point_cloud/iteration_30000/point_cloud.ply \
        --gcps data/raw/drone_views/gcps.json           # [{local:[x,y,z], target:[X,Y,Z]}]
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend"))


def ply_to_splat(ply_path: Path) -> np.ndarray:
    """INRIA 3DGS PLY -> packed .splat rows (32 bytes each).

    Row layout (antimatter15 / three.js SplatLoader):
      center[3]f32 | scale[3]f32 | rgba[4]u8 | rot[4]i8
    """
    from plyfile import PlyData

    v = PlyData.read(ply_path)["vertex"]
    pos = v["x"].astype(np.float32), v["y"].astype(np.float32), v["z"].astype(np.float32)
    a = v["opacity"].astype(np.float32)
    alpha = 255.0 * (1.0 / (1.0 + np.exp(-a)))                    # logit -> sigmoid
    sh0 = np.column_stack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]])  # DC term 0.5 offset
    rgb = np.clip(0.5 + 0.5 * sh0, 0.0, 1.0) * 255.0
    s = np.column_stack([v["scale_0"], v["scale_1"], v["scale_2"]])
    scale = np.exp(s).astype(np.float32)                          # log-scale -> linear
    q = np.column_stack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]]).astype(np.float32)
    n = len(pos[0])
    scale = np.maximum(scale, 1e-6)

    out = np.empty((n, 32), dtype=np.uint8)
    out[:, 0:12] = np.column_stack(pos).astype(np.float32).view(np.uint8)
    out[:, 12:24] = scale.view(np.uint8)
    out[:, 24] = np.clip(rgb[:, 0], 0, 255).astype(np.uint8)
    out[:, 25] = np.clip(rgb[:, 1], 0, 255).astype(np.uint8)
    out[:, 26] = np.clip(rgb[:, 2], 0, 255).astype(np.uint8)
    out[:, 27] = np.clip(alpha, 0, 255).astype(np.uint8)
    quat = (q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-9))
    out[:, 28:32] = np.rint(quat * 128.0).astype(np.int8).view(np.uint8)
    return out


def solve_pose(gcps: list[dict], building: dict) -> dict:
    """Match GCP pairs (local X,Y vs the cadastre footprint) to a similarity fit.

    Returns position/rotation/scale for the <Splat> mesh so the reconstructed
    building lands exactly on its cadastral footprint in the scene.
    """
    from app.services.reconstruction.georeference import estimate_similarity

    src = np.array([g["local"][:2] for g in gcps], dtype=float)
    dst = np.array([g["target"][:2] for g in gcps], dtype=float)
    scale, theta, t = estimate_similarity(src, dst)

    fp = building["footprint"]["coordinates"][0]
    cx = sum(p[0] for p in fp) / len(fp)
    cy = sum(p[1] for p in fp) / len(fp)
    ground_z = float(building.get("ground_z") or 0.0)
    return {
        "position": [round(float(t[0]), 3), round(float(t[1]), 3), round(ground_z, 3)],
        "rotation": [0.0, 0.0, round(float(theta), 5)],   # yaw about +Z (local frame)
        "scale": round(float(scale), 6),
        "gcp_count": len(gcps),
        "note": "nerf-local -> cadastre-local similarity fit (EPSG:32643 offset frame)",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--building-id", required=True)
    ap.add_argument("--input", required=True, help="INRIA 3DGS .ply (point_cloud.ply)")
    ap.add_argument("--gcps", required=True, help="[{local:[x,y,z],target:[X,Y,Z]}] local=capture frame")
    args = ap.parse_args()

import asyncio

from app import db
from app.services.cadastre import parcels as parcels_svc


async def _amain(args) -> None:
    await db.connect()
    buildings = await parcels_svc.list_buildings()
    building = next((b for b in buildings if str(b["id"]) == str(args.building_id)), None)
    if building is None:
        raise SystemExit(f"building {args.building_id} not found")
    await db.pool().close()

    gcps = json.loads(Path(args.gcps).read_text())

    rows = ply_to_splat(Path(args.input))
    out_dir = REPO / "data" / "reconstruction" / "real" / str(args.building_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "scene.splat").write_bytes(rows.tobytes())
    write_points_bin(out_dir, rows)
    pose = solve_pose(gcps, building)
    (out_dir / "pose.json").write_text(json.dumps(pose, indent=2))
    print(f"[register_real_building] {len(rows)} splats -> {out_dir}/scene.splat")
    print("pose:", pose)


def write_points_bin(out_dir: Path, rows: np.ndarray) -> None:
    """Reduce the splat to a colored point cloud for GPU-safe rendering."""
    centers = rows[:, 0:12].copy().view(np.float32).reshape(len(rows), 3)
    rgb = rows[:, 24:27].astype(np.uint8)
    alpha = rows[:, 27]
    keep = alpha >= 16
    centers, rgb = centers[keep], rgb[keep]
    with (out_dir / "points.bin").open("wb") as f:
        f.write(np.uint32(len(centers)).tobytes())
        f.write(centers.astype("<f4").tobytes())
        f.write(rgb.tobytes())
    print(f"[register_real_building] {len(centers)} points -> {out_dir}/points.bin")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--building-id", required=True)
    ap.add_argument("--input", required=True, help="INRIA 3DGS .ply (point_cloud.ply)")
    ap.add_argument("--gcps", required=True, help="[{local:[x,y,z],target:[X,Y,Z]}] local=capture frame")
    args = ap.parse_args()
    asyncio.run(_amain(args))
    return 0


if __name__ == "__main__":
    sys.exit(main())