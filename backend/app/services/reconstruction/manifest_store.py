"""Manifest persistence around ``data/reconstruction/``.

The directory holds the artifact contract: ``manifest.json`` + optional
``pointcloud.ply`` (CRS-aligned), ``mesh.ply``, and gridded ``dsm/ndsm/dem.tif``.
Writing the manifest is the only way the pipeline knows a reconstruction exists.
"""

from __future__ import annotations

import json
from pathlib import Path

from .manifest import ReconStatus, ReconstructionManifest, manifest_from_dict, manifest_to_dict


def reconstruction_dir(data_dir: str | Path) -> Path:
    return Path(data_dir) / "reconstruction"


def manifest_path(data_dir: str | Path) -> Path:
    return reconstruction_dir(data_dir) / "manifest.json"


def load_manifest(data_dir: str | Path) -> ReconstructionManifest | None:
    p = manifest_path(data_dir)
    if not p.exists():
        return None
    with open(p) as f:
        return manifest_from_dict(json.load(f))


def save_manifest(manifest: ReconstructionManifest, data_dir: str | Path) -> Path:
    p = manifest_path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(manifest_to_dict(manifest), f, indent=2, sort_keys=True)
    return p


def set_status(data_dir: str | Path, status: ReconStatus, **fields) -> ReconstructionManifest:
    """Create / update a manifest, flipping its lifecycle status."""
    current = load_manifest(data_dir)
    manifest = current if current is not None else ReconstructionManifest()
    manifest.status = status
    for k, v in fields.items():
        setattr(manifest, k, v)
    save_manifest(manifest, data_dir)
    return manifest