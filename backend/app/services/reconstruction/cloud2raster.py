"""Grid a point cloud back into DSM / DEM / nDSM GeoTIFFs.

A dense reconstruction (splatfacto export or LiDAR) is reduced to elevation
rasters so the existing, well-scored raster pipeline and the classic nDSM
thresholding can consume it unchanged — and so viewers get a familiar DSM.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio

GROUND_CLASS = 2  # ASPRS/LAZ ground class (mirrors datagen/pointcloud.py)


def cloud_to_rasters(
    xyz: np.ndarray,
    *,
    out_dir: str | Path,
    cls: np.ndarray | None = None,
    cell: float = 2.0,
    crs: int = 32643,
    extent: tuple[float, float, int, int] | None = None,
) -> dict[str, str]:
    """Grid ``xyz`` (N, 3) metre coordinates into dem/dsm/ndsm GeoTIFFs.

    ``cls`` optionally carries per-point classifications; class-2 points (or the
    lowest return per cell) define the bare-earth DEM.  ``extent`` is
    ``(west, north, width_px, height_px)`` — pass it to grid into the *same*
    raster frame as the source imagery so masks align exactly.
    """
    xyz = np.asarray(xyz, dtype=np.float64)
    if xyz.ndim != 2 or xyz.shape[1] < 3:
        raise ValueError("xyz must be a (N, 3) point array")

    if extent is not None:
        west, north, w, h = extent
        west, north, w, h = float(west), float(north), int(w), int(h)
    else:
        west = float(xyz[:, 0].min()) - cell
        east = float(xyz[:, 0].max()) + cell
        south = float(xyz[:, 1].min()) - cell
        north = float(xyz[:, 1].max()) + cell
        w = int(np.ceil((east - west) / cell))
        h = int(np.ceil((north - south) / cell))

    col = np.floor((xyz[:, 0] - west) / cell).astype(np.int64)
    row = np.floor((north - xyz[:, 1]) / cell).astype(np.int64)
    row = np.clip(row, 0, h - 1)
    col = np.clip(col, 0, w - 1)

    transform = rasterio.transform.from_origin(west, north, cell, cell)

    dsm = np.full((h, w), -np.inf, dtype=np.float64)
    np.maximum.at(dsm, (row, col), xyz[:, 2])
    dsm[np.isneginf(dsm)] = 0.0

    if cls is not None:
        ground = np.asarray(cls) == GROUND_CLASS
        if ground.any():
            dem_cells = np.full((h, w), np.inf, dtype=np.float64)
            np.minimum.at(dem_cells, (row[ground], col[ground]), xyz[ground, 2])
            dem_cells[np.isinf(dem_cells)] = 0.0
            dem = dem_cells
        else:
            dem = np.zeros_like(dsm)
    else:
        # no classification — lowest return in each cell stands in for the DEM
        dem_cells = np.full((h, w), np.inf, dtype=np.float64)
        np.minimum.at(dem_cells, (row, col), xyz[:, 2])
        dem_cells[np.isinf(dem_cells)] = 0.0
        dem = dem_cells

    ndsm = np.clip(dsm - dem, 0, None).astype(np.float32)
    dsm = dsm.astype(np.float32)
    dem = dem.astype(np.float32)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, arr in (("dem", dem), ("dsm", dsm), ("ndsm", ndsm)):
        p = out_dir / f"{name}.tif"
        with rasterio.open(
            p, "w", driver="GTiff", height=h, width=w, count=1,
            dtype=arr.dtype, crs=rasterio.crs.CRS.from_epsg(crs), transform=transform,
        ) as dst:
            dst.write(arr, 1)
        paths[name] = str(p)
    return paths