# 3D ULPIN Cadastre — Prototype Docs

Demo prototype for SIH-style problem **"3D ULPIN Generation and vertical Property Mapping System"**:
a volumetric, 3D-ULPIN-based cadastre built on a synthetic locality, an AI footprint-extraction
pipeline, topology validation, and a browser 3D viewer.

| Doc | Contents |
| --- | --- |
| [architecture.md](architecture.md) | System overview, stack, data flow, endpoints, directory map |
| [ulpin-spec.md](ulpin-spec.md) | 3D ULPIN format, vertical descriptors, checksum, examples |
| [evaluation.md](evaluation.md) | Truth dataset, validation slate, AI pipeline metrics |
| [demo-runbook.md](demo-runbook.md) | Step-by-step setup and live demo script |

Quick reference:

- Locality: state `06` · district `08` · sub-district `07` · village `04` (Haryana / Gurugram demo)
- CRS: **EPSG:32643 (UTM 43N)**, world origin `[698353.56, 3149754.55]`, demo bounds `0–392 × 0–362 m`
- PostGIS on host port **5433** (host Postgres owns 5432); backend **8000**; Next.js dev **3000**
- Seeded truth: 36 parcels_2d · 28 buildings · 235 volumetric parcels · 28 owners · 9 utilities
- Validation: **1 open conflict** (deliberate): metro `06080704900001-MTA17` × lift shaft `06080704000021-U38`
- Pipeline baseline: mask IoU **0.6266**, building recall **18/28**, floor MAE **0.0**, 253 ULPINs valid
- Reconstruction stage (point-cloud artifact): building recall **28/28 (100%)**, mask IoU **0.6211**, floor MAE **0.0**, 217 ULPINs valid

## Problem-statement mapping

| Statement ingredient | Where it lives |
| --- | --- |
| 3D ULPIN generation | `app/services/ulpin/` (codec), `routes/ulpins.py`, `/ulpin` lab |
| Vertical property mapping | 3D volumetric parcels (`parcels_3d` prisms) + category mix (floor/suite/underground/parking/air-right) |
| Surface parcels | 36 `parcels_2d`, encoded as base 14-char ULPIN |
| Multi-storey apartments | 12-storey suite towers, quad-split per suite with ULPIN per unit |
| Underground infrastructure | utility centerlines + metro tunnel, z < 0 prisms, collision audit |
| Drone imagery | `scripts/generate_drone_views.py` ↔ `data/raw/drone_views/` |
| LiDAR / point cloud | `data/raw/pointcloud.las` + `services/reconstruction/cloudseg.py` |
| GNSS / CORS | UTM-seeded camera poses (`camera_poses.json`), EPSG:32643 world origin |
| DEM / DSM | `data/raw/dsm/ndsm.tif` (+ reconstruction DSM), extracted in `pipeline.py` |
| AI/ML building extraction | nDSM + morph (baseline) vs convex-hull on point cloud (reconstruction) |
| Floor segmentation | z-histogram slab peaks (`segment_floors`) with per-storey envelopes |
| Vertical parcel delineation | `classify_volumes` → floor/suite/underground/parking/air-right prisms |
| Topology validation | `ST_3DIntersects` + bbox-prism volume, deliberate conflict surfaced on dashboard |