"""End-to-end synthetic dataset generator.

Pipeline:
  topology model  ->  point cloud (LAS)  ->  DEM/DSM/nDSM + ortho + masks
                   ->  ground-truth volumes (GeoJSON) -> manifest
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

from . import pointcloud, rasters, truth
from .topology import build_model


@dataclass
class DatagenOptions:
    seed: int = 42
    blocks_x: int = 3
    blocks_y: int = 3
    block_w: float = 120.0
    block_h: float = 110.0
    road: float = 16.0
    max_floors: int = 8
    point_density: float = 0.6
    raster_cell: float = 2.0
    include_metro: bool = True
    origin_lat: float = 28.4593
    origin_lon: float = 77.0258


def generate(out_dir: str, opts: DatagenOptions | None = None) -> dict:
    opts = opts or DatagenOptions()
    raw_dir = os.path.join(out_dir, "raw")
    truth_dir = os.path.join(out_dir, "truth")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(truth_dir, exist_ok=True)

    model = build_model(
        blocks_x=opts.blocks_x, blocks_y=opts.blocks_y,
        block_w=opts.block_w, block_h=opts.block_h, road=opts.road,
        seed=opts.seed, max_floors=opts.max_floors,
        include_metro=opts.include_metro,
        origin_lat=opts.origin_lat, origin_lon=opts.origin_lon,
    )

    vols = truth.build_truth_volumes(model)

    # ---- point cloud -----------------------------------------------------
    pc_path = os.path.join(raw_dir, "pointcloud.las")
    x, y, z, cls = pointcloud.build_point_cloud(
        model, ground_density=opts.point_density,
    )
    pointcloud.write_las(pc_path, x, y, z, cls)
    n_points = int(x.size)

    # ---- rasters ---------------------------------------------------------
    rast_paths = rasters.make_rasters(model, out_dir=raw_dir, cell=opts.raster_cell)

    # ---- ground-truth JSON ------------------------------------------------
    with open(os.path.join(raw_dir, "parcels_2d.geojson"), "w") as f:
        json.dump(truth.parcels_to_geojson(model), f, indent=1)
    with open(os.path.join(raw_dir, "buildings.geojson"), "w") as f:
        json.dump(truth.buildings_to_geojson(model), f, indent=1)
    with open(os.path.join(raw_dir, "utilities.geojson"), "w") as f:
        json.dump(truth.utilities_to_geojson(model), f, indent=1)

    with open(os.path.join(truth_dir, "volumes.geojson"), "w") as f:
        json.dump(truth.volumes_to_geojson(vols), f, indent=1)

    floor_counts = {b.name: b.floor_count for b in model.buildings}
    with open(os.path.join(truth_dir, "floor_counts.json"), "w") as f:
        json.dump(floor_counts, f, indent=2)

    manifest = {
        "n_points": n_points,
        "n_parcels_2d": len(model.parcels),
        "n_buildings": len(model.buildings),
        "n_volumes_3d": len(vols),
        "n_assets": len(model.assets),
        "n_trees": len(model.trees),
        "blocks_x": opts.blocks_x,
        "blocks_y": opts.blocks_y,
        "origin_utm": list(model.utm_origin),
        "utm_zone": 32643,
        "bounds": [model.minx, model.miny, model.maxx, model.maxy],
        "rasters": {k: os.path.relpath(v, out_dir) for k, v in rast_paths.items()},
        "pointcloud": os.path.relpath(pc_path, out_dir),
        "options": asdict(opts),
    }
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate the synthetic 3D ULPIN demo locality")
    parser.add_argument("out_dir", nargs="?", default="data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--blocks-x", type=int, default=3)
    parser.add_argument("--blocks-y", type=int, default=3)
    parser.add_argument("--max-floors", type=int, default=8)
    parser.add_argument("--point-density", type=float, default=0.6)
    parser.add_argument("--raster-cell", type=float, default=2.0)
    parser.add_argument("--no-metro", action="store_true")
    args = parser.parse_args()

    opts = DatagenOptions(
        seed=args.seed, blocks_x=args.blocks_x, blocks_y=args.blocks_y,
        max_floors=args.max_floors, point_density=args.point_density,
        raster_cell=args.raster_cell, include_metro=not args.no_metro,
    )
    manifest = generate(args.out_dir, opts)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()