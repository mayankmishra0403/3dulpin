"""Simulate an airborne LiDAR point cloud from the synthetic locality.

Generates classified points:
    class 2 — ground (roads / open ground, z≈0)
    class 5 — vegetation (tree canopies)
    class 6 — building (roof tops, facades, and per-storey slab ledges)

Storey ledges intentionally emit a dense band at each slab top so that a
z-histogram of building points yields measurable peaks for the AI floor
segmentation stage.
"""

from __future__ import annotations

import numpy as np
import laspy

from .topology import STOREY_HT, LocalityModel


def _crown_atmosphere(t: "Tree") -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(1)
    n = int(140 * t.r)
    pts = rng.normal(0, 1, (n, 3))
    r = np.sqrt((pts ** 2).sum(axis=1))
    keep = r <= 1.0
    pts = pts[keep]
    # pancake the crown slightly, centre crown at z = t.h*0.6
    pts[:, 2] = pts[:, 2] * 0.55 + t.h * 0.6
    x = t.x + pts[:, 0] * t.r
    y = t.y + pts[:, 1] * t.r
    z = pts[:, 2]
    return x, y, z


def build_point_cloud(
    model: LocalityModel,
    *,
    ground_density: float = 0.6,     # points per m²
    roof_density: float = 1.4,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (x, y, z, classification) arrays in UTM metres."""
    rng = np.random.default_rng(seed)
    xs, ys, zs, cls = [], [], [], []

    w = model.maxx - model.minx
    hh = model.maxy - model.miny

    # ---- ground ----------------------------------------------------------
    n_ground = int(w * hh * ground_density)
    gx = rng.uniform(model.minx, model.maxx, n_ground)
    gy = rng.uniform(model.miny, model.maxy, n_ground)

    # building footprints (as shapely polygons) to keep ground points out
    import shapely.geometry as sg

    footprints = [sg.Polygon(b.footprint) for b in model.buildings]
    pts_mask = np.array(
        [not any(fp.contains(sg.Point(x, y)) for fp in footprints) for x, y in zip(gx, gy)],
        dtype=bool,
    )
    gx, gy = gx[pts_mask], gy[pts_mask]
    xs.append(gx)
    ys.append(gy)
    zs.append(np.zeros_like(gx) + rng.normal(0, 0.02, gx.size))
    cls.append(np.full(gx.size, 2, dtype=np.uint8))

    # ---- buildings -------------------------------------------------------
    for b in model.buildings:
        ring = np.array(b.footprint, dtype=float)
        minx, miny = ring[:, 0].min(), ring[:, 1].min()
        maxx, maxy = ring[:, 0].max(), ring[:, 1].max()
        area = (maxx - minx) * (maxy - miny)

        # roof top
        n_roof = max(int(area * roof_density), 30)
        rx = rng.uniform(minx, maxx, n_roof)
        ry = rng.uniform(miny, maxy, n_roof)
        rz = rng.normal(b.height_m, 0.02, n_roof)
        # roof clutter (AC units) — small bumps
        n_bump = n_roof // 6
        if n_bump:
            bx = rng.uniform(minx + 2, maxx - 2, n_bump)
            by = rng.uniform(miny + 2, maxy - 2, n_bump)
            rz[:n_bump] += 0.9 * rng.random(n_bump)
            rx = np.concatenate([rx[:n_bump], rx[n_bump:]])
            ry = np.concatenate([ry[:n_bump], ry[n_bump:]])
            rz = np.concatenate([rz[:n_bump], rz[n_bump:]])
            # (keep arrays aligned simply)
            rx, ry, rz = rx, ry, rz

        xs.append(rx)
        ys.append(ry)
        zs.append(rz)
        cls.append(np.full(rx.size, 6, dtype=np.uint8))

        # per-storey slab ledges (dense band around the facade at slab top)
        for level in range(1, b.floor_count + 1):
            slab_z = (level - 1) * STOREY_HT
            ledges = []
            for (x1, y1), (x2, y2) in zip(ring[:-1], ring[1:]):
                seg_len = float(np.hypot(x2 - x1, y2 - y1))
                n_ledge = max(int(seg_len / 1.3), 2)
                for t in np.linspace(0, 1, n_ledge, endpoint=False):
                    lx = (x1 * (1 - t) + x2 * t) + 0.05 * np.sign((y2 - y1) or 1)
                    ly = (y1 * (1 - t) + y2 * t) + 0.05 * np.sign((x1 - x2) or 1)
                    ledges.append((lx, ly))
                    ledges.append((x1 * (1 - t) + x2 * t, y1 * (1 - t) + y2 * t))
            if ledges:
                lx = np.array([p[0] for p in ledges])
                ly = np.array([p[1] for p in ledges])
                xs.append(lx)
                ys.append(ly)
                zs.append(rng.normal(slab_z, 0.02, lx.size))
                cls.append(np.full(lx.size, 6, dtype=np.uint8))

        # facades (sparse, vectorised)
        wall_pts_per_face = 24
        f_x, f_y, f_z = [], [], []
        for (x1, y1), (x2, y2) in zip(ring[:-1], ring[1:]):
            t = rng.random(wall_pts_per_face)
            z = rng.uniform(0.2, b.height_m - 0.2, wall_pts_per_face)
            off = 0.05 if max(abs(x2 - x1), abs(y2 - y1)) > 0 else 0
            f_x.append(x1 * (1 - t) + x2 * t + off * np.sign((y2 - y1) or 1))
            f_y.append(y1 * (1 - t) + y2 * t + off * np.sign((x1 - x2) or 1))
            f_z.append(z)
        if f_x:
            xs.append(np.concatenate(f_x))
            ys.append(np.concatenate(f_y))
            zs.append(np.concatenate(f_z))
            cls.append(np.full(np.concatenate(f_x).size, 6, dtype=np.uint8))

    # ---- vegetation ------------------------------------------------------
    for t in model.trees:
        tx, ty, tz = _crown_atmosphere(t)
        xs.append(tx)
        ys.append(ty)
        zs.append(tz)
        cls.append(np.full(tx.size, 5, dtype=np.uint8))

    x = np.concatenate(xs)
    y = np.concatenate(ys)
    z = np.concatenate(zs)
    cl = np.concatenate(cls)
    return x, y, z, cl


def write_las(path: str, x: np.ndarray, y: np.ndarray, z: np.ndarray, cls: np.ndarray) -> None:
    header = laspy.LasHeader(point_format=0, version="1.2")
    header.offsets = (x.min(), y.min(), 0.0)
    header.scales = (0.001, 0.001, 0.001)
    las = laspy.LasData(header)
    las.x = x
    las.y = y
    las.z = z
    las.classification = cls
    las.intensity = np.where(cls == 6, 90, np.where(cls == 5, 60, 30)).astype(np.uint16)
    las.write(path)