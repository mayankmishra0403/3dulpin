"""Reconstruction artifact manifest.

Describes a 3D scene reconstructed from drone imagery and / or LiDAR (e.g. a
nerfstudio splatfacto export, or a processed point cloud) together with the
georeferencing needed to map nerfstudio's local frame back into the cadastral
CRS (EPSG:32643 UTM 43N).

Persisted as ``data/reconstruction/manifest.json`` so the demo can run fully
offline (the GPU reconstruction job itself runs once on a CUDA worker).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum


class ReconStatus(str, Enum):
    """Lifecycle of a reconstruction artifact set."""

    IDLE = "idle"           # nothing reconstructed yet
    RUNNING = "running"     # GPU worker in progress
    DONE = "done"           # artifacts (+ manifest) complete, consumable
    FAILED = "failed"       # worker errored; note carries the reason


@dataclass
class GeoreferenceParams:
    """Similarity transform (scale · rotation + translation) local → cadastral CRS.

    ``apply_transform`` in ``georeference.py`` evaluates it against 3D points.
    """

    scale: float = 1.0
    rotation: float = 0.0                 # yaw about +z, radians
    translation: tuple = field(default_factory=lambda: (0.0, 0.0, 0.0))
    crs: int = 32643
    gcp_count: int = 0
    rmse_m: float = 0.0
    strategy: str = "identity"            # gcp | pose_seed | synthetic_fit | identity

    def to_dict(self) -> dict:
        d = asdict(self)
        d["translation"] = list(d["translation"])
        return d


@dataclass
class ReconstructionManifest:
    method: str = "splatfacto"            # splatfacto | nerfacto | lidar
    source: str = "synthetic_drone"       # synthetic_drone | upload
    status: ReconStatus = ReconStatus.IDLE
    cloud_path: str | None = None         # PLY / LAS point cloud (CRS coords)
    mesh_path: str | None = None          # optional reconstructed mesh
    dsm_path: str | None = None           # optional gridded DSM GeoTIFF
    georeference: GeoreferenceParams | None = None
    stats: dict = field(default_factory=dict)   # points, extent_m, coverage…
    note: str = ""


def manifest_to_dict(m: ReconstructionManifest) -> dict:
    d = asdict(m)
    d["status"] = m.status.value
    if m.georeference is not None:
        d["georeference"] = m.georeference.to_dict()
    return d


def manifest_from_dict(d: dict) -> ReconstructionManifest:
    geo = d.get("georeference")
    if geo is not None:
        d = dict(d)
        d["georeference"] = GeoreferenceParams(
            scale=float(geo.get("scale", 1.0)),
            rotation=float(geo.get("rotation", 0.0)),
            translation=tuple(float(v) for v in geo.get("translation", (0.0, 0.0, 0.0))),
            crs=int(geo.get("crs", 32643)),
            gcp_count=int(geo.get("gcp_count", 0)),
            rmse_m=float(geo.get("rmse_m", 0.0)),
            strategy=str(geo.get("strategy", "identity")),
        )
    return ReconstructionManifest(
        method=str(d.get("method", "splatfacto")),
        source=str(d.get("source", "synthetic_drone")),
        status=ReconStatus(str(d.get("status", ReconStatus.IDLE.value))),
        cloud_path=d.get("cloud_path"),
        mesh_path=d.get("mesh_path"),
        dsm_path=d.get("dsm_path"),
        georeference=d.get("georeference"),
        stats=dict(d.get("stats", {})),
        note=str(d.get("note", "")),
    )