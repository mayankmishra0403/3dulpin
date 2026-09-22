"""Headless nerfstudio runner (CUDA workers only).

These helpers drive the nerfstudio CLI as a subprocess: ``ns-process-data``
(images→COLMAP poses), ``ns-train`` (splatfacto/nerfacto/…), ``ns-export``
(point cloud) and ``ns-render``.  They are intentionally *not* imported by the
FastAPI request path — the app consumes only the exported artifacts.  The GPU
job runs once on a worker (Colab/VM) via ``app/scripts/reconstruct_gpu.py``.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class NerfRunnerConfig:
    method: str = "splatfacto"
    data_path: str | Path = "."
    dataset_dir: str | Path = ""          # ns-process-data output
    output_dir: str | Path = "outputs"
    max_iter: int = 10_000
    max_num_images: int | None = None
    num_downscales: int = 3
    colmap_matcher: str = "vocab_tree"    # exhaustive | sequential | vocab_tree
    camera_type: str = "perspective"      # perspective | equirectangular | …
    match_types_across: bool = False


def _require(*cmds: str) -> str:
    for cmd in cmds:
        p = shutil.which(cmd)
        if p:
            return cmd
    raise RuntimeError(
        f"nerfstudio CLI ({', '.join(cmds)}) not found — s: CUDA worker only. "
        "The FastAPI app consumes reconstructed artifacts, it never trains."
    )


def _run(cmd: list[str], cwd: Path | None = None, timeout: int | None = None) -> None:
    log.info("$ %s", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout or "").strip().splitlines()[-20:])
        tail += "\n" + "\n".join((proc.stderr or "").strip().splitlines()[-20:])
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{tail}")
    log.debug("%s", proc.stdout[-4000:])


def process_data(cfg: NerfRunnerConfig) -> Path:
    """images/video → nerfstudio dataset (COLMAP poses) into ``cfg.dataset_dir``."""
    _require("ns-process-data")
    cmd = [
        "ns-process-data", "images",
        "--data", str(cfg.data_path),
        "--output-dir", str(Path(cfg.output_dir) / "dataset"),
        "--camera-type", cfg.camera_type,
        "--matching-method", cfg.colmap_matcher,
        "--num-downscales", str(cfg.num_downscales),
    ]
    if cfg.max_num_images:
        cmd += ["--max-num-images", str(cfg.max_num_images)]
    _run(cmd)
    return Path(cfg.output_dir) / "dataset"


def train(cfg: NerfRunnerConfig) -> Path:
    """Train ``cfg.method`` (splatfacto default) on the prepared dataset."""
    _require("ns-train")
    cmd = [
        "ns-train", cfg.method,
        "--data", str(cfg.dataset_dir or (Path(cfg.output_dir) / "dataset")),
        "--output-dir", str(cfg.output_dir),
        "--max-num-iterations", str(cfg.max_iter),
    ]
    if cfg.max_num_images:
        cmd += ["--max-num-images", str(cfg.max_num_images)]
    if cfg.method != "splatfacto":
        cmd += ["--num-downscales", str(cfg.num_downscales)]
    _run(cmd)
    return Path(cfg.output_dir)


def export_pointcloud(cfg: NerfRunnerConfig, config_path: str | Path) -> Path:
    """scene → PLY point cloud (nerfstudio viewer export)."""
    _require("ns-export")
    out = Path(cfg.output_dir) / "export"
    _run([
        "ns-export", "pointcloud",
        "--load-config", str(config_path),
        "--output-dir", str(out),
        "--num-points", "1000000",
    ])
    return out