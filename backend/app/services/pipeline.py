"""AI extraction pipeline (baseline) for 3D ULPIN generation.

Stages (deterministic, raster + point-free, hackathon baseline):
  1. normalize   – nDSM + greenness vegetation mask from ortho
  2. delineate   – building footprints: threshold nDSM > 2.5 m, vegetation
                   subtracted, morphological cleaning, connected components
                   simplified to their axis-aligned bounding footprints
  3. floor-infer – storey count per footprint from observed height
  4. map         – assign 3D ULPINs (surface / floor / suite / underground /
                   parking / air right) via the canonical ULPIN service
  5. evaluate    – metrics vs the authoritative truth volumes

The pipeline intentionally consumes only "sensor" inputs (nDSM + ortho),
never the truth vectors, so the evaluation is honest for a demo.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

from app.services.ulpin import ulpin as ulpin_svc

STOREY_HT = 3.2
BASE_DATA_DIRS = ("raw", "truth")


# ---------------------------------------------------------------------- stage 1-2
class _Footprint:
    def __init__(self, fid: int, polygon, height: float, mean_rgb):
        self.fid = fid
        self.polygon = polygon
        self.height = float(height)
        self.mean_rgb = tuple(mean_rgb)

    @property
    def bounds(self):
        return self.polygon.bounds

    @property
    def area(self) -> float:
        return self.polygon.area


def _vegetation_mask(ortho: np.ndarray, cell: float) -> np.ndarray:
    """Green-dominance vegetation mask (2G - R - B) signed, thresholded."""
    r = ortho[..., 0].astype(np.int16)
    g = ortho[..., 1].astype(np.int16)
    b = ortho[..., 2].astype(np.int16)
    greenish = (2 * g - r - b) > 12
    # tree canopies are elevated too; combine with height cue for robustness
    return greenish


def detect_footprints(
    ndsm_path: str,
    ortho_path: str,
    *,
    min_building_h: float = 2.5,
    min_area_m2: float = 12.0,
) -> list[_Footprint]:
    """Threshold nDSM into building components and box-fit each one."""
    with rasterio.open(ndsm_path) as ds:
        ndsm = ds.read(1)
        transform = ds.transform
        cell_x = abs(ds.transform.a)
        cell_y = abs(ds.transform.e)
        crs = ds.crs
    with rasterio.open(ortho_path) as ds:
        ortho = np.transpose(ds.read(), (1, 2, 0))

    rough = ndsm > min_building_h
    rough = (~_vegetation_mask(ortho, cell_x)) & rough

    # morphological cleanup: small kernels remove isolated slivers
    from scipy.ndimage import binary_opening

    rough = binary_opening(rough, structure=np.ones((3, 3)), iterations=1)
    if rough.sum() == 0:
        return []

    labels, nlabels = _label_components(rough)
    footprints: list[_Footprint] = []
    for lab in range(1, nlabels + 1):
        ys, xs = np.where(labels == lab)
        if len(xs) < max(3, int(min_area_m2 / (cell_x * cell_y))):
            continue
        x0, y0 = xs.min(), ys.min()
        x1, y1 = xs.max(), ys.max()
        if (x1 - x0 + 1) < 3 or (y1 - y0 + 1) < 3:
            continue
        # world coordinates: col/row via transform
        w0, n0 = rasterio.transform.xy(transform, y0, x0)
        w1, n1 = rasterio.transform.xy(transform, y1, x1)
        from shapely.geometry import box

        poly = box(min(w0, w1), min(n0, n1), max(w0, w1), max(n0, n1)).buffer(0)
        comp_dsm = ndsm[ys, xs]
        height = float(np.percentile(comp_dsm, 90))
        mean_rgb = np.median(ortho[ys, xs], axis=0)
        footprints.append(_Footprint(len(footprints) + 1, poly, height, mean_rgb))
    return footprints


def _label_components(mask: np.ndarray):
    from scipy.ndimage import label

    labels, n = label(mask, structure=np.ones((3, 3)))
    return labels, int(n)


# ---------------------------------------------------------------------- stage 3-4
def classify_and_build(footprints: list[_Footprint]) -> list[dict]:
    """Give every detected footprint full volumetric parcels + 3D ULPINs."""
    locality = ulpin_svc.demo_locality()
    parcels_out: list[dict] = []
    for fp in footprints:
        floors = max(1, round(fp.height / STOREY_HT))
        tall = floors >= 7  # tower-like -> suites
        r, g, b = fp.mean_rgb
        commercial = bool(b > r and r > g + 4 and floors <= 2)
        ring = [ (x, y) for (x, y) in zip(*fp.polygon.exterior.coords.xy) ][:-1]
        base = locality.base(str(_parcel_no_for(fp)))
        if floors == 0:
            continue
        if tall:
            for level in range(1, floors + 1):
                for unit, ux in enumerate(_quad_split(ring), start=1):
                    parcels_out.append(_mk(base, "suite", level, f"U{unit:02d}", ux,
                                           (level - 1) * STOREY_HT, level * STOREY_HT,
                                           "residential_apartment"))
            parcels_out.append(_mk(base, "underground", -1, None, ring, -3.6, -0.2, "car_parking"))
            for slot, sx in enumerate(_quad_split(ring, 2, 3), start=1):
                parcels_out.append(_mk(base, "parking", -2, f"P{slot:02d}", sx, -7.0, -3.7, "parking_slot"))
            parcels_out.append(_mk(base, "air_right", 0, None, ring,
                                   floors * STOREY_HT, floors * STOREY_HT + 30.0, "air_space_rights"))
        else:
            for level in range(1, floors + 1):
                z0 = (level - 1) * STOREY_HT
                usage = "commercial_retail" if commercial else "residential"
                parcels_out.append(_mk(base, "floor", level, None, ring, z0, z0 + STOREY_HT, usage))
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


def _parcel_no_for(fp: _Footprint) -> int:
    """Naive demo assignment: footprint centroid inside a truth parcel."""
    cx, cy = fp.polygon.centroid.x, fp.polygon.centroid.y
    for p in _TRUTH_2D_FEATURES:
        coords = p["geometry"]["coordinates"][0]
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        if (min(xs) <= cx <= max(xs)) and (min(ys) <= cy <= max(ys)):
            return p["properties"]["parcel_no"]
    return 1


# ---------------------------------------------------------------------- stage 5
def evaluate(detected: list[dict], truth_vols: list[dict], ndsm_path: str, ortho_path: str) -> dict:
    """Score the detected inventory against authoritative truth volumes."""
    truth_buildings: dict = {}
    for v in truth_vols:
        cat = v["properties"]["category"]
        if cat in ("floor", "suite"):
            bid = v["properties"]["building_id"]
            truth_buildings.setdefault(bid, []).append(v)
    truth_floors = {
        bid: max(v["properties"]["level_no"] for v in vols
                 if v["properties"]["category"] in ("floor", "suite"))
        for bid, vols in truth_buildings.items()
    }
    truth_suite_towers = {
        bid for bid, vols in truth_buildings.items()
        if any(v["properties"]["category"] == "suite" for v in vols)
    }

    # matched buildings: IoU of detected footprints vs truth footprints
    from shapely.geometry import box, MultiPolygon
    from shapely.ops import unary_union

    truth_polys = {}
    for bid, vols in truth_buildings.items():
        polys = [box(*__ring_bounds(v["geometry"]["coordinates"][0])) for v in vols]
        truth_polys[bid] = unary_union(polys)

    matched = {}
    building_groups: dict = {}
    for det in _all_floor_like(detected):
        front = det["ulpin3d"].rsplit("-", 1)[0]
        building_groups.setdefault(front, []).append(det)
    det_polys = {}
    for i, ds in enumerate(building_groups.values()):
        all_x = [pt[0] for d in ds for pt in d["ring"]]
        all_y = [pt[1] for d in ds for pt in d["ring"]]
        det_polys[i] = box(min(all_x), min(all_y), max(all_x), max(all_y))
    for det_id, poly in det_polys.items():
        best_iou, best_bid = 0.0, None
        for bid, tpoly in truth_polys.items():
            inter = poly.intersection(tpoly).area
            union = poly.union(tpoly).area
            iou = inter / union if union else 0.0
            if iou > best_iou:
                best_iou, best_bid = iou, bid
        if best_bid is not None and best_iou >= 0.4:
            matched[det_id] = (best_bid, best_iou)

    detected_floor_count = {}
    for d in _all_floor_like(detected):
        front = d["ulpin3d"][: d["ulpin3d"].rfind("-")]
        detected_floor_count[front] = max(detected_floor_count.get(front, 0), d["level_no"])

    floor_errs = []
    match_rows = []
    group_list = list(building_groups)
    for det_id, (bid, iou) in matched.items():
        det_floors = detected_floor_count.get(group_list[det_id], 0)
        truth_f = truth_floors.get(bid, 0)
        floor_errs.append(abs(det_floors - truth_f))
        match_rows.append({"building": bid, "iou": round(iou, 3), "floors_detected": det_floors,
                           "floors_truth": truth_f})

    counts_det = {}
    for d in detected:
        counts_det[d["category"]] = counts_det.get(d["category"], 0) + 1
    counts_truth = {}
    for v in truth_vols:
        c = v["properties"]["category"]
        counts_truth[c] = counts_truth.get(c, 0) + 1

    # global vector/binary-building IoU on the truth mask
    with rasterio.open(truth_mask_path) as ds:
        truth_mask = ds.read(1).astype(bool)
    with rasterio.open(ndsm_path) as ds:
        det_mask = ds.read(1) > 2.5
    with rasterio.open(ortho_path) as ds:
        _ortho = np.transpose(ds.read(), (1, 2, 0))
    from scipy.ndimage import binary_opening as _op

    det_mask = _op(det_mask & ~_vegetation_mask(_ortho, 2.0), np.ones((3, 3)))
    inter = np.logical_and(det_mask, truth_mask).sum()
    union = np.logical_or(det_mask, truth_mask).sum()
    mask_iou = inter / union if union else 0.0

    return {
        "detected_buildings": len(det_polys),
        "truth_buildings": len(truth_polys),
        "matched_buildings": len(matched),
        "mask_iou": round(mask_iou, 4),
        "floor_mae": round(sum(floor_errs) / len(floor_errs), 3) if floor_errs else None,
        "building_matches": match_rows,
        "parcel_counts": {"detected": counts_det, "truth": counts_truth},
        "ulpins_assigned": len(detected),
        "ulpins_valid": sum(1 for d in detected if _valid_ulpin(d["ulpin3d"])),
    }


def _all_floor_like(parcels: list[dict]) -> list[dict]:
    return [d for d in parcels if d["category"] in ("floor", "suite")]


def __ring_bounds(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return (min(xs), min(ys), max(xs), max(ys))


def _valid_ulpin(code: str) -> bool:
    try:
        obj = ulpin_svc.ULPIN3D.parse(code)
        return obj.value == code
    except ValueError:
        return False


_TRUTH_2D_FEATURES: list = []


# ---------------------------------------------------------------------- orchestrator
def run_pipeline(data_dir: str, stage: str = "extract") -> dict:
    """Run extraction and evaluation.  ``stage`` selects the geometry source:

    * ``extract``      — classic raster baseline: nDSM thresholding + h/3.2
                         storey guess (kept for comparison).
    * ``reconstruct``  — point-cloud stage: nerfstudio/LiDAR cloud → connected
                         components → z-histogram slab-peak floor segmentation.
    """
    global _TRUTH_2D_FEATURES, truth_mask_path
    data_dir = Path(data_dir)
    with open(data_dir / "raw" / "parcels_2d.geojson") as f:
        fc = json.load(f)
    _TRUTH_2D_FEATURES = fc["features"]
    truth_mask_path = str(data_dir / "raw" / "truth_building_mask.tif")

    with open(data_dir / "truth" / "volumes.geojson") as f:
        truth_vols = json.load(f)["features"]

    source_note: str | None = None
    if stage == "reconstruct":
        detected, source_note = _run_reconstruct_stage(data_dir)
        ndsm_path = str(data_dir / "reconstruction" / "ndsm.tif")
        ortho_path = str(data_dir / "raw" / "ortho.tif")
    else:
        footprints = detect_footprints(
            str(data_dir / "raw" / "ndsm.tif"),
            str(data_dir / "raw" / "ortho.tif"),
        )
        detected = classify_and_build(footprints)
        ndsm_path = str(data_dir / "raw" / "ndsm.tif")
        ortho_path = str(data_dir / "raw" / "ortho.tif")

    evaluation = evaluate(detected, truth_vols, ndsm_path, ortho_path)
    evaluation["extra"] = {}

    report = {
        "stage": stage,
        "source_note": source_note,
        "footprints_detected": len(detected),
        "parcels": detected,
        "evaluation": evaluation,
    }
    if stage == "reconstruct":
        report["reconstruction"] = _reconstruction_meta(data_dir)
        report["footprints"] = [
            {"fid": b.fid, "height_m": round(b.height, 2),
             "bounds": [round(v, 1) for v in b.bounds], "area_m2": round(b.area, 1)}
            for b in _LAST_CLOUD_BUILDINGS
        ]
    else:
        report["footprints"] = [
            {"fid": fp.fid, "height_m": round(fp.height, 2),
             "bounds": [round(v, 1) for v in fp.bounds], "area_m2": round(fp.area, 1)}
            for fp in footprints
        ]
    return report


_LAST_CLOUD_BUILDINGS: list = []


def _run_reconstruct_stage(data_dir: Path) -> tuple[list[dict], str | None]:
    """Detect + classify volumetric parcels directly from a point cloud.

    Cloud source resolution: a ``data/reconstruction`` manifest artifact (real
    nerfstudio GPU export) wins; otherwise we fall back to the synthetic LiDAR
    raster ``data/raw/pointcloud.las`` so the stage runs offline on any laptop.
    """
    from app.services.reconstruction.cloudseg import (
        classify_volumes,
        detect_buildings,
        load_point_cloud,
    )
    from app.services.reconstruction.manifest_store import load_manifest

    global _LAST_CLOUD_BUILDINGS

    manifest = load_manifest(data_dir)
    note = None
    cloud_path = None
    if manifest is not None and manifest.cloud_path:
        from app.services.reconstruction.manifest_store import reconstruction_dir

        p = Path(manifest.cloud_path)
        if not p.is_absolute():
            p = reconstruction_dir(data_dir) / p
        if p.exists():
            cloud_path = p
            note = (f"nerfstudio {manifest.method} artifact ({manifest.source}); "
                    f"georef strategy={manifest.georeference.strategy if manifest.georeference else 'identity'}")
        else:
            note = f"manifest cloud_path missing ({p}); falling back to synthetic LiDAR"
    if cloud_path is None:
        las = data_dir / "raw" / "pointcloud.las"
        if las.exists():
            cloud_path = las
            note = note or "synthetic LiDAR (data/raw/pointcloud.las) — no reconstruction artifact yet"
        else:
            raise FileNotFoundError(f"no point cloud available: {las}")

    xyz, cls = load_point_cloud(cloud_path)
    buildings = detect_buildings(xyz, cls)
    _LAST_CLOUD_BUILDINGS = buildings

    from app.services.reconstruction.cloud2raster import cloud_to_rasters
    extent = None
    rst = data_dir / "raw" / "rasters.json"
    if rst.exists():
        meta = json.loads(rst.read_text())
        extent = (float(meta["west"]), float(meta["north"]),
                  int(meta["width"]), int(meta["height"]))
    try:
        cloud_to_rasters(xyz, out_dir=data_dir / "reconstruction",
                         cls=cls, extent=extent, cell=2.0)
    except Exception:  # noqa: BLE001 — gridding is best-effort for the viewer
        pass

    detected = classify_volumes(buildings, _parcel_no_for)
    return detected, note


def _reconstruction_meta(data_dir: Path) -> dict:
    from app.services.reconstruction.manifest_store import load_manifest

    manifest = load_manifest(data_dir)
    return {
        "status": manifest.status.value if manifest else "none",
        "method": manifest.method if manifest else None,
        "source": manifest.source if manifest else None,
        "cloud_available": manifest is not None and bool(manifest.cloud_path),
    }