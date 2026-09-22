"""Georeferencing — bring a reconstruction's local frame into the cadastral CRS.

nerfstudio / COLMAP recover scene geometry up to an arbitrary similarity
transform (scale · rotation + translation).  GNSS/CORS anchors or ground
control points let us recover that transform and apply it to every point
(e.g. a splatfacto point cloud) so volumes land in EPSG:32643 metres.
"""

from __future__ import annotations

import numpy as np

from .manifest import GeoreferenceParams


def estimate_similarity(src: np.ndarray, dst: np.ndarray) -> tuple[float, float, np.ndarray]:
    """Least-squares similarity (Umeyama/Procrustes) mapping ``src`` → ``dst``.

    Args:
        src: (N, 2) control points in the local / reconstruction frame.
        dst: (N, 2) the same points surveyed in the target CRS.

    Returns:
        (scale, rotation_radians, translation) with
        ``dst ≈ scale · R(rotation) · src + translation`` (R acts on 2D xy).
    """
    src = np.asarray(src, dtype=float)
    dst = np.asarray(dst, dtype=float)
    if src.shape != dst.shape or src.ndim != 2 or src.shape[1] != 2 or src.shape[0] < 3:
        raise ValueError("src/dst must be (N, 2) with N >= 3 matching control points")
    src_m = src.mean(axis=0)
    dst_m = dst.mean(axis=0)
    src_c = src - src_m
    dst_c = dst - dst_m

    h = dst_c.T @ src_c
    u, s, vt = np.linalg.svd(h)
    r = u @ vt
    if np.linalg.det(r) < 0:
        vt[-1] *= -1
        r = u @ vt

    scale = float(s.sum() / max(np.sum(src_c * src_c), 1e-12))
    rot = r @ np.diag([scale, scale])
    t = dst_m - rot @ src_m
    theta = float(np.arctan2(r[1, 0], r[0, 0]))
    return scale, theta, t


def make_params(
    src: np.ndarray,
    dst: np.ndarray,
    src_z: np.ndarray | None = None,
    dst_z: np.ndarray | None = None,
    crs: int = 32643,
    strategy: str = "gcp",
) -> GeoreferenceParams:
    """Build georeference from GCP pairs, optionally also fitting the z datum.

    ``dst_z`` z-values are projected through the same 2D scale plus an additive
    vertical offset ``tz = mean(dst_z) - scale · mean(src_z)`` (assumes a level
    local frame, true for airborne/CORS-surveyed captures).
    """
    scale, theta, t = estimate_similarity(src, dst)
    tz = 0.0
    if src_z is not None and dst_z is not None:
        tz = float(np.asarray(dst_z).mean() - scale * np.asarray(src_z).mean())

    residual = apply_transform_xy(src, scale, theta, t) - np.asarray(dst, dtype=float)
    rmse = float(np.sqrt(np.mean(residual ** 2)))

    return GeoreferenceParams(
        scale=scale,
        rotation=theta,
        translation=(float(t[0]), float(t[1]), round(tz, 6)),
        crs=crs,
        gcp_count=int(len(src)),
        rmse_m=round(rmse, 4),
        strategy=strategy,
    )


def apply_transform_xy(
    pts: np.ndarray, scale: float, theta: float, t: np.ndarray
) -> np.ndarray:
    pts = np.asarray(pts, dtype=float)
    c, s = np.cos(theta), np.sin(theta)
    return scale * (pts @ np.array([[c, s], [-s, c]], dtype=float)) + np.asarray(
        t, dtype=float
    )


def apply_transform(
    pts: np.ndarray, geo: GeoreferenceParams
) -> np.ndarray:
    """Apply a manifest transform to a (N, 2) or (N, 3) point array."""
    pts = np.asarray(pts, dtype=float)
    xy = apply_transform_xy(pts[..., :2], geo.scale, geo.rotation, geo.translation[:2])
    if pts.shape[1] == 2:
        return xy
    z = geo.scale * pts[..., 2] + geo.translation[2]
    return np.column_stack([xy, z])