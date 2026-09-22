"""Reconstruction layer — drone imagery / LiDAR point clouds into cadastral geometry.

Wraps the external GPU reconstruction stack (nerfstudio splatfacto/nerfacto on a
CUDA worker) behind a manifest-based artifact contract so the FastAPI app itself
needs no CUDA.  Also provides CPU-side tools to georeference the reconstructed
cloud into the cadastral CRS (EPSG:32643) and to grid it back into DSM/nDSM.
"""

from __future__ import annotations

from .cloud2raster import cloud_to_rasters
from .cloudseg import classify_volumes, detect_buildings, load_point_cloud, segment_floors
from .georeference import apply_transform, estimate_similarity, make_params
from .manifest import (
    GeoreferenceParams,
    ReconStatus,
    ReconstructionManifest,
    manifest_from_dict,
    manifest_to_dict,
)
from .manifest_store import (
    load_manifest,
    reconstruction_dir,
    save_manifest,
    set_status,
)
from .nerfrunner import NerfRunnerConfig, export_pointcloud, process_data, train

__all__ = [
    "GeoreferenceParams",
    "NerfRunnerConfig",
    "ReconStatus",
    "ReconstructionManifest",
    "apply_transform",
    "classify_volumes",
    "cloud_to_rasters",
    "detect_buildings",
    "estimate_similarity",
    "export_pointcloud",
    "load_manifest",
    "load_point_cloud",
    "make_params",
    "manifest_from_dict",
    "manifest_to_dict",
    "process_data",
    "reconstruction_dir",
    "save_manifest",
    "segment_floors",
    "set_status",
    "train",
]