"""Generate deterministic drone imagery over the synthetic locality.

Renders perspective aerial views of the extruded 3D building city from an
orbiting drone (painter's-algorithm software rasterizer — no GPU needed),
persisting them as PNGs plus full camera poses twice:

  * ``camera_poses.json`` — keyframes in the *local* frame AND UTM 43N
    (world origin 698353.56, 3149754.55), for GNSS/CORS-style georeferencing;
  * ``transforms.json``   — nerfstudio-format pinhole poses in UTM, so a CUDA
    run can `--skip-colmap` and still get a coherent, near-CRS frame.

Output: ``data/raw/drone_views/``.  This is the drone-imagery *input* to the
nerfstudio reconstruction stage (Phase 3); the pipeline itself never sees it.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data"
OUT = DATA / "raw" / "drone_views"

ORIGIN_UTM = (698353.56, 3149754.55, 0.0)   # local (0,0,0) → UTM 43N
W, H = 720, 484                             # render resolution (px)
FOV_H = 55.0                                # horizontal field of view, degrees
ALT = 230.0                                 # drone altitude +z (m)
RADIUS = 300.0                              # orbit radius (m)
FRAMES = 24


def look_at_matrix(eye, target, up=(0, 0, 1)):
    eye = np.asarray(eye, float)
    f = np.asarray(target, float) - eye
    f = f / np.linalg.norm(f)
    r = np.cross(f, np.asarray(up, float))
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)
    return r, u, f, eye


def project(points, r, u, f, eye, focal):
    rel = points - eye
    camz = rel @ f
    invalid = camz <= 1.0
    x = focal * (rel @ r) / np.maximum(camz, 1e-9) + W / 2
    y = focal * (rel @ u) / np.maximum(camz, 1e-9) + H / 2
    return np.column_stack([x, y]), invalid | (camz <= 1.0)


def load_scene():
    buildings = json.loads((DATA / "raw" / "buildings.geojson").read_text())
    feats = []
    for ft in buildings["features"]:
        p = ft["properties"]
        ring = ft["geometry"]["coordinates"][0][:-1]
        feats.append({
            "bid": p["bid"], "floors": p["floor_count"],
            "height": float(p["height_m"]), "parcel_type": p["parcel_type"],
            "commercial": p.get("commercial", False),
            "ring": [(x, y) for (x, y) in ring],
        })
    return feats


def roof_color(f):
    t = f["parcel_type"]
    return (150, 155, 168) if t == "suite" else (198, 184, 148) if t == "walkup" else (172, 192, 212) if t == "commercial" else (190, 190, 190)


def wall_color(f):
    return (116, 124, 142) if f["parcel_type"] == "suite" else (186, 178, 152)


def render_frame(feats, eye, target) -> Image.Image:
    r, u, f, eye = look_at_matrix(eye, target)
    focal = (W / 2) / math.tan(math.radians(FOV_H) / 2)
    img = Image.new("RGB", (W, H), (206, 198, 182))
    draw = ImageDraw.Draw(img)

    # back-to-front so nearer buildings overdraw
    def cam_depth(b):
        xs = [p[0] for p in b["ring"]]
        ys = [p[1] for p in b["ring"]]
        c = np.array([(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0.0])
        return float(np.dot(c - eye, f))

    order = sorted(feats, key=cam_depth, reverse=True)

    for b in order:
        ring = b["ring"]
        base = np.array(ring + [ring[0]], dtype=float)          # z=0
        base = np.column_stack([base, np.zeros(len(base))])
        top = base.copy() + np.array([0, 0, b["height"]])
        pts, inval = project(np.vstack([base, top]), r, u, f, eye, focal)
        n = len(base)
        b_pts, t_pts = pts[:n], pts[n:]
        if inval.any():
            continue

        # walls
        for i in range(n - 1):
            quad = np.array([b_pts[i], b_pts[i + 1], t_pts[i + 1], t_pts[i]])
            if np.all(np.isfinite(quad)):
                draw.polygon([tuple(p) for p in quad], fill=wall_color(b))
        # floor bands on the near wall (storey lines)
        for i in range(n - 1):
            a0, a1 = b_pts[i], b_pts[i + 1]
            for fl in range(1, b["floors"]):
                zfrac = fl * (3.2 / b["height"])
                draw.line(
                    [(a0[0], a0[1] + zfrac * (t_pts[i][1] - a0[1])),
                     (a1[0], a1[1] + zfrac * (t_pts[i + 1][1] - a1[1]))],
                    fill=(60, 66, 82), width=1)
        # roof
        if np.all(np.isfinite(t_pts)):
            draw.polygon([tuple(p) for p in t_pts], fill=roof_color(b))
    return img


def utm(local):
    return (local[0] + ORIGIN_UTM[0], local[1] + ORIGIN_UTM[1], alt_or_z(local))


def alt_or_z(local):
    return local[2] if len(local) > 2 else 0.0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    feats = load_scene()
    center = np.array([196.0, 181.0, 0.0])
    focal = (W / 2) / math.tan(math.radians(FOV_H) / 2)

    poses = []
    for i in range(FRAMES):
        ang = 2 * math.pi * i / FRAMES
        eye = np.array([center[0] + RADIUS * math.cos(ang),
                        center[1] + RADIUS * math.sin(ang), ALT])
        img = render_frame(feats, eye, center)

        fname = f"view_{i:03d}.png"
        img.save(OUT / fname)

        # camera_to_world (nerfstudio): column-major flatten of 4x4
        r, u, f, _ = look_at_matrix(eye, center)
        rot = np.column_stack([r, u, f])          # rotation of camera axes
        c2w = np.eye(4)
        c2w[:3, :3] = rot
        c2w[:3, 3] = utm(eye)

        poses.append({
            "frame": i,
            "file_path": fname,
            "position_local": [float(v) for v in eye],
            "position_utm": [float(v) for v in utm(eye)],
            "look_at_local": [float(v) for v in center],
            "camera_to_world": c2w.flatten().tolist(),
        })

    (OUT / "camera_poses.json").write_text(
        json.dumps({"focal_uv": focal, "resolution": [W, H], "frames": poses}, indent=2))

    tf = {
        "camera_model": "OPENCV",
        "fl_x": focal, "fl_y": focal,
        "cx": W / 2, "cy": H / 2,
        "w": W, "h": H,
        "frames": [{
            "file_path": p["file_path"],
            "transform_matrix": p["camera_to_world"],
        } for p in poses],
    }
    (OUT / "transforms.json").write_text(json.dumps(tf, indent=2))
    print(f"wrote {FRAMES} drone views -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())