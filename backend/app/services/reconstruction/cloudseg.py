"""Point-cloud building extraction & vertical parcel delineation (stage=reconstruct).

Stage 2 of the integration: consume a dense airborne point cloud — the
synthetic LiDAR in ``data/raw/pointcloud.las`` or a nerfstudio splatfacto
export — instead of / alongside the nDSM raster.  This is where the problem
statement's *AI/ML* building extraction + floor segmentation + vertical parcel
delineation actually live:

  1. Ground / non-building separation (classification or per-cell min-z DEM).
  2. Building footprints — occupancy grid + connected components + convex hull.
  3. Storey segmentation — per-building z-histogram slab-peak detection, so
     floors come from observed geometry, not the ``round(height / 3.2)`` guess.
  4. Volumetric parcels + 3D ULPINs via the canonical ULPIN service.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.services.ulpin import ulpin as ulpin_svc

from .cloud2raster import GROUND_CLASS

STOREY_HT = 3.2
BUILDING_CLASS = 6            # ASPRS/LAZ building class (datagen pointcloud.py)


# --------------------------------------------------------------------------- io
def load_point_cloud(path: str | Path) -> tuple[np.ndarray, np.ndarray | None]:
    """Load (xyz, class|None) from .las/.laz/.ply — supports PLY without deps."""
    path = Path(path)
    if path.suffix.lower() in (".las", ".laz"):
        import laspy

        las = laspy.read(path)
        xyz = np.column_stack([las.x, las.y, las.z]).astype(np.float64)
        cls = np.asarray(las.classification, dtype=np.int16)
        return xyz, cls
    if path.suffix.lower() in (".ply",):
        return _read_ply(path)
    raise ValueError(f"unsupported point cloud format: {path.suffix}")


def _read_ply(path: Path) -> tuple[np.ndarray, np.ndarray | None]:
    """Minimal PLY reader (ascii or binary_little_endian) for x/y/z [class]."""
    with open(path, "rb") as f:
        header = []
        line = f.readline()
        while line.strip() != b"end_header":
            header.append(line.strip().decode("ascii"))
            line = f.readline()
        props: list[str] = []
        count, fmt = 0, "ascii"
        for h in header:
            if h.startswith("format "):
                fmt = h.split()[1]
            elif h.startswith("element vertex"):
                count = int(h.split()[-1])
            elif h.startswith("property"):
                props.append(h.split()[-1])
        want = {"x", "y", "z"}
        idx = {p: i for i, p in enumerate(props) if p in want or p in ("class", "classification")}
        if not want.issubset(idx):
            raise ValueError(f"PLY {path} missing vertex x/y/z")

        dtype = np.dtype([(p, "<f4" if fmt == "binary_little_endian" else "f4") for p in props if p in idx])
        if fmt == "binary_little_endian":
            raw = np.fromfile(f, dtype=dtype, count=count)
        else:
            rows = []
            for _ in range(count):
                parts = f.readline().split()
                rows.append([float(parts[i]) for i in idx.values()])
            raw = np.array(rows, dtype=np.float64)

    xyz = np.column_stack([raw["x"], raw["y"], raw["z"]]).astype(np.float64)
    cls = None
    if "class" in idx:
        cls = raw["class"].astype(np.int16)
    elif "classification" in idx:
        cls = raw["classification"].astype(np.int16)
    return xyz, cls


# ------------------------------------------------------------- footprint stage
class _CloudBuilding:
    __slots__ = ("fid", "polygon", "height", "z", "center_ground_z")

    def __init__(self, fid, polygon, height, z, center_ground_z):
        self.fid = fid
        self.polygon = polygon
        self.height = float(height)
        self.z = z
        self.center_ground_z = float(center_ground_z)

    @property
    def area(self) -> float:
        return float(self.polygon.area)

    @property
    def bounds(self):
        return self.polygon.bounds


def _grid_index(xyz: np.ndarray, cell: float):
    west = float(xyz[:, 0].min()) - cell
    north = float(xyz[:, 1].max()) + cell
    w = int(np.ceil((float(xyz[:, 0].max()) - west) / cell))
    h = int(np.ceil((north - float(xyz[:, 1].min())) / cell))
    col = np.floor((xyz[:, 0] - west) / cell).astype(np.int64)
    row = np.floor((north - xyz[:, 1]) / cell).astype(np.int64)
    col = np.clip(col, 0, w - 1)
    row = np.clip(row, 0, h - 1)
    return row, col, w, h, west, north


def _is_building_point(xyz: np.ndarray, cls: np.ndarray | None, cell: float, min_h: float):
    row, col, w, h, west, north = _grid_index(xyz, cell)
    dem = np.full((h, w), np.inf, dtype=np.float64)
    np.minimum.at(dem, (row, col), xyz[:, 2])
    dem[np.isinf(dem)] = 0.0
    ndm = xyz[:, 2] - dem[row, col]

    if cls is not None:
        return cls == BUILDING_CLASS
    return ndm > min_h


def detect_buildings(
    xyz: np.ndarray,
    cls: np.ndarray | None = None,
    *,
    cell: float = 2.0,
    min_h: float = 2.5,
    min_area_m2: float = 12.0,
    min_points: int = 8,
) -> list[_CloudBuilding]:
    """Cluster elevated points into building footprints via occupancy labelling.

    Each returned building keeps its raw z-values so the storey stage can do
    per-building slab-peak segmentation instead of a global height heuristic.
    """
    building = _is_building_point(xyz, cls, cell, min_h)
    if not building.any():
        return []

    row, col, w, h, west, north = _grid_index(xyz, cell)
    occupy = np.zeros((h, w), dtype=bool)
    occupy[row[building], col[building]] = True

    from scipy.ndimage import label

    labels, n = label(occupy, structure=np.ones((3, 3)))
    lab = labels[row[building], col[building]]

    from shapely.geometry import MultiPoint

    buildings: list[_CloudBuilding] = []
    for fid in range(1, n + 1):
        idx = np.where(building)[0][np.where(lab == fid)[0]]
        idx = np.asarray(idx, dtype=np.int64)
        if idx.size < min_points:
            continue
        bz = xyz[idx, 2]
        height = float(np.percentile(bz, 95))
        if height - float(bz.min()) < min_h:
            continue

        pts2 = MultiPoint(np.column_stack([xyz[idx, 0], xyz[idx, 1]]))
        hull = pts2.convex_hull
        if hull.is_empty or hull.area < min_area_m2:
            continue

        center_ground = float(xyz[idx, 2].min())
        buildings.append(_CloudBuilding(len(buildings) + 1, hull, height, bz, center_ground))
    return buildings


# ---------------------------------------------------------------- storey stage
def segment_floors(building_z: np.ndarray, *, storey_ht: float = STOREY_HT) -> dict:
    """Find slab elevations from a building's point z-distribution.

    Synthetic LiDAR emits a dense ledge band at each slab top; real splat/LiDAR
    clouds show similar balcony/slab clusters.  We Gaussian-smooth the z
    histogram and locate peaks >= ``storey_ht`` apart.

    The *ground* slab (z ≈ 0) is intentionally excluded from the band list —
    peaks are the slab tops of floors 1..n (the roof top is the last one).
    Falls back to a regular height/floors grid when no distinct bands appear
    (noisy / sparse real clouds).

    Returns ``{floors, slabs, height}`` with ``floors`` storeys and ``slabs``
    the top elevation of each storey.
    """
    z = building_z
    if z.size < 10:
        return {"floors": 1, "slabs": [float(z.max())], "height": float(z.max())}

    zmin = float(z.min())
    zmax = float(z.max()) + 0.1
    height = float(np.percentile(z, 95))
    if zmax - zmin <= 1e-6:
        return {"floors": 1, "slabs": [zmax], "height": zmax}

    bin_w = 0.2
    edges = np.arange(zmin, zmax, bin_w)
    hist, _ = np.histogram(z, bins=edges)

    from scipy.ndimage import gaussian_filter1d
    from scipy.signal import find_peaks

    smooth = gaussian_filter1d(hist.astype(np.float64), sigma=2.0)
    dist = max(int(storey_ht * 0.6 / bin_w), 2)
    pk, _ = find_peaks(smooth, distance=dist, prominence=max(smooth.max() * 0.05, 1.0))
    slab_z = [zmin + (i + 0.5) * bin_w for i in pk]
    slab_z = sorted(s for s in slab_z if 0.0 <= s <= zmax + 1e-6)

    if slab_z and slab_z[0] <= storey_ht * 0.5:
        slab_z = slab_z[1:]      # ground slab band, not a storey top
    floors = len(slab_z)

    if floors < 1:
        # no usable bands — fall back to a regular grid over the observed height
        floors = max(1, int(round(height / storey_ht))) if height / storey_ht >= 0.5 else 1
        slab_z = [height * k / floors for k in range(1, floors + 1)]

    return {"floors": floors, "slabs": [float(s) for s in slab_z], "height": float(slab_z[-1]) if slab_z else height}


# ------------------------------------------------------------------ ULPIN stage
def classify_volumes(
    buildings: list[_CloudBuilding],
    parcel_no_for,
    *,
    suite_min_floors: int = 7,
) -> list[dict]:
    """Give cloud-detected buildings full volumetric parcels + 3D ULPINs."""
    locality = ulpin_svc.demo_locality()
    parcels_out: list[dict] = []
    for b in buildings:
        seg = segment_floors(b.z)
        floors = seg["floors"]
        slab = seg["slabs"]                      # top elevation of each storey
        ring = [tuple(p) for p in b.polygon.exterior.coords][:-1]
        ground = 0.0

        def floor_z(k: int) -> tuple[float, float]:
            z0 = ground if k == 1 else float(slab[k - 2])
            z1 = float(slab[k - 1]) if k <= len(slab) else float(seg["height"])
            return z0, z1

        base = locality.base(str(parcel_no_for(b)))
        tall = floors >= suite_min_floors
        area = b.area
        commercial = bool(floors <= 2 and area >= 400.0)

        if tall:
            for level in range(1, floors + 1):
                z0, z1 = floor_z(level)
                for unit, ux in enumerate(_quad_split(ring), start=1):
                    parcels_out.append(_mk(base, "suite", level, f"U{unit:02d}", ux,
                                           z0, z1, "residential_apartment"))
            parcels_out.append(_mk(base, "underground", -1, None, ring, -3.6, ground, "car_parking"))
            for slot, sx in enumerate(_quad_split(ring, 2, 3), start=1):
                parcels_out.append(_mk(base, "parking", -2, f"P{slot:02d}", sx, -7.0, -3.7, "parking_slot"))
            roof_top = seg["height"]
            parcels_out.append(_mk(base, "air_right", 0, None, ring, roof_top, roof_top + 30.0, "air_space_rights"))
        else:
            for level in range(1, floors + 1):
                z0, z1 = floor_z(level)
                usage = "commercial_retail" if commercial else "residential"
                parcels_out.append(_mk(base, "floor", level, None, ring, z0, z1, usage))
        parcels_out.append(_mk(base, "surface", 0, None, ring, 0.0, 0.2, "surface_land"))
    return parcels_out


def _quad_split(ring, nx: int = 2, ny: int = 2) -> list[list[tuple[float, float]]]:
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    out = []
    for gy in range(ny):
        for gx in range(nx):
            lo = (x0 + (x1 - x0) * gx / nx, y0 + (y1 - y0) * gy / ny)
            hi = (x0 + (x1 - x0) * (gx + 1) / nx, y0 + (y1 - y0) * (gy + 1) / ny)
            out.append([(lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])])
    return out


def _mk(base, category, level, unit, ring, z1, z2, usage) -> dict:
    obj = ulpin_svc.ULPIN3D(base_ulpin=base, category=category, level_no=level, unit_no=unit)
    ring = [tuple(p) for p in ring]
    return {
        "ulpin3d": obj.value,
        "category": category,
        "level_no": level,
        "unit_no": unit,
        "zmin": z1, "zmax": z2,
        "usage": usage,
        "ring": ring,
    }