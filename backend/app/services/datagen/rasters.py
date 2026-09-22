"""Raster generation — DEM, DSM, nDSM, synthetic ortho imagery, truth masks.

All rasters are written as GeoTIFFs in UTM 43N with a uniform cell size.
The DEM is the bare-earth surface (flat datum z=0 in the synthetic model);
the DSM includes buildings and tree canopies; nDSM = DSM - DEM feeds the
building-extraction stage.  The ortho mosaic is a procedural rendering of
the *authoritative* parcel map (drone imagery stand-in).
"""

from __future__ import annotations

import numpy as np
import rasterio
from rasterio.features import rasterize

from .topology import Tree, LocalityModel

GROUND_COLORS = {
    "open_space": (192, 218, 176),
    "civic": (210, 202, 190),
    "residential_walkup": (226, 213, 178),
    "residential_highrise": (206, 198, 182),
    "commercial_retail": (198, 216, 226),
}
ROAD_COLOR = (122, 122, 122)
ROOF_COLORS = {
    "tower": (150, 155, 168),
    "walkup": (198, 184, 148),
    "market": (172, 192, 212),
    "pavilion": (190, 190, 190),
}


def _build_grid(model: LocalityModel, cell: float = 2.0):
    w = int(np.ceil((model.maxx - model.minx) / cell))
    h = int(np.ceil((model.maxy - model.miny) / cell))
    west, north = model.minx, model.maxy
    transform = rasterio.transform.from_origin(west, north, cell, cell)
    return w, h, transform


def _shapes(polys: list[tuple[object, ...]], value_attr: str):
    """[(geometry, value)] where value read from attribute of the model object."""
    out = []
    for obj in polys:
        geom = obj.footprint if hasattr(obj, "footprint") else obj.ring
        out.append(({"type": "Polygon", "coordinates": [geom]}, getattr(obj, value_attr)))
    return out


def make_rasters(
    model: LocalityModel,
    *,
    out_dir: str,
    cell: float = 2.0,
    seed: int = 11,
) -> dict[str, str]:
    import json

    rng = np.random.default_rng(seed)
    w, h, transform = _build_grid(model, cell)
    shape = (h, w)

    # ---- building rasters ------------------------------------------------
    building_dsm = np.zeros(shape, dtype=np.float32)
    building_mask = np.zeros(shape, dtype=np.uint8)
    roof_class = np.zeros(shape, dtype=np.uint8)
    if model.buildings:
        b_shapes = [({"type": "Polygon", "coordinates": [b.footprint]}, b.height_m) for b in model.buildings]
        building_dsm = rasterize(b_shapes, out_shape=shape, transform=transform, fill=0, dtype=np.float32)
        mask_shapes = [({"type": "Polygon", "coordinates": [b.footprint]}, 1) for b in model.buildings]
        building_mask = rasterize(mask_shapes, out_shape=shape, transform=transform, fill=0, dtype=np.uint8)
        r_shapes = []
        for b in model.buildings:
            rc = 1 if b.parcel_type == "suite" else (3 if b.commercial else 2)
            r_shapes.append(({"type": "Polygon", "coordinates": [b.footprint]}, rc))
        roof_class = rasterize(r_shapes, out_shape=shape, transform=transform, fill=0, dtype=np.uint8)

    # ---- tree canopy DSM ---------------------------------------------------
    tree_dsm = np.zeros(shape, dtype=np.float32)
    for t in model.trees:
        cx = (t.x - model.minx) / cell
        cy = (model.maxy - t.y) / cell
        rp = int(np.ceil(t.r / cell))
        xs = np.arange(max(0, int(cx) - rp), min(w, int(cx) + rp + 1))
        ys = np.arange(max(0, int(cy) - rp), min(h, int(cy) + rp + 1))
        if xs.size == 0 or ys.size == 0:
            continue
        gx, gy = np.meshgrid(xs, ys)
        d = np.sqrt((gx - cx) ** 2 + (gy - cy) ** 2) * cell
        canopy = np.clip(t.h - 0.6 * d, 0, None).astype(np.float32)
        tree_dsm[gy, gx] = np.maximum(tree_dsm[gy, gx], canopy)

    # ---- assemble DEM / DSM / nDSM ----------------------------------------
    dem = np.zeros(shape, dtype=np.float32) + rng.normal(0, 0.01, shape).astype(np.float32)
    dsm = np.maximum(np.maximum(building_dsm, tree_dsm),
                     dem + rng.normal(0, 0.01, shape).astype(np.float32)).astype(np.float32)
    ndsm = np.clip(dsm - dem, 0, None).astype(np.float32)

    crs = rasterio.crs.CRS.from_epsg(32643)

    paths = {}
    for name, arr in (("dem", dem), ("dsm", dsm), ("ndsm", ndsm)):
        p = f"{out_dir}/{name}.tif"
        with rasterio.open(p, "w", driver="GTiff", height=h, width=w, count=1,
                           dtype=arr.dtype, crs=crs, transform=transform) as dst:
            dst.write(arr, 1)
        paths[name] = p

    mask_path = f"{out_dir}/truth_building_mask.tif"
    with rasterio.open(mask_path, "w", driver="GTiff", height=h, width=w, count=1,
                       dtype="uint8", crs=crs, transform=transform) as dst:
        dst.write(building_mask, 1)
    paths["truth_building_mask"] = mask_path

    # ---- synthetic ortho ----------------------------------------------------
    parcel_rgb = np.zeros((h, w, 1), dtype=np.uint8)  # class id
    for usage, cid in enumerate(GROUND_COLORS, start=1):
        shapes = [({"type": "Polygon", "coordinates": [p.ring]}, cid) for p in model.parcels if p.usage == usage]
        if shapes:
            parcel_rgb = np.maximum(parcel_rgb, rasterize(shapes, out_shape=shape, transform=transform,
                                                          fill=0, dtype=np.uint8)[..., None])

    img = np.zeros((h, w, 3), dtype=np.uint8)
    # roads default
    img[:, :] = ROAD_COLOR
    # parcel ground
    usages = list(GROUND_COLORS)
    for cid, usage in enumerate(usages, start=1):
        mask = parcel_rgb[:, :, 0] == cid
        img[mask] = GROUND_COLORS[usage]
    # roofs
    for rc_id, key in ((1, "tower"), (2, "walkup"), (3, "market"), (4, "pavilion")):
        img[roof_class == rc_id] = ROOF_COLORS[key]
    # trees
    for t in model.trees:
        cx = (t.x - model.minx) / cell
        cy = (model.maxy - t.y) / cell
        rp = int(np.ceil(t.r / cell))
        xs = np.arange(max(0, int(cx) - rp), min(w, int(cx) + rp + 1))
        ys = np.arange(max(0, int(cy) - rp), min(h, int(cy) + rp + 1))
        if xs.size == 0 or ys.size == 0:
            continue
        gx, gy = np.meshgrid(xs, ys)
        d = np.sqrt((gx - cx) ** 2 + (gy - cy) ** 2) * cell
        canopy = d < t.r
        img[gy, gx][canopy] = (54, 118, 58)

    ortho_path = f"{out_dir}/ortho.tif"
    with rasterio.open(ortho_path, "w", driver="GTiff", height=h, width=w, count=3,
                       dtype="uint8", crs=crs, transform=transform) as dst:
        dst.write(np.transpose(img, (2, 0, 1)))
    paths["ortho"] = ortho_path

    with open(f"{out_dir}/rasters.json", "w") as f:
        json.dump({"cell": cell, "width": w, "height": h,
                   "west": model.minx, "north": model.maxy,
                   "srid": 32643}, f, indent=2)

    return paths