# Architecture

## Goal
Generate 3D ULPINs for vertical property parts (surface, floors, suites, underground, parking,
air-rights, utilities, metro) and maintain a volumetric 3D cadastre with topology validation.

## Stack
| Layer | Choice |
| --- | --- |
| Database | PostgreSQL + **PostGIS 3.4** (`postgis/postgis:16-3.4-alpine`), no SFCGAL |
| Backend | Python **FastAPI** (uvicorn), `asyncpg`, numpy/scipy/rasterio/shapely |
| Frontend | Next.js 16 (App Router, Tailwind v4) + **react-three-fiber / three.js** |
| Data pipeline | `backend/app/services/pipeline.py` — nDSM thresholding + morphological + ULPIN coding |
| Reconstruction | `backend/app/services/reconstruction/` — nerfstudio/LiDAR point-cloud layer (artifact contract) |
| Orchestration | `docker-compose.yml` (postgis + backend + frontend); local dev uses bare uvicorn + npm |

> Recent Docker images for `postgis:16-3.4` are SFCGAL-free, so all 3D validation is computed
> with GEOS `ST_3DIntersects` + exact bbox-prism math (`dx·dy·dz`) — no `ST_3DDifference`/`ST_3DUnion`.

## Ports
| Service | Internal | Host |
| --- | --- | --- |
| PostGIS | `postgis:5432` (docker network) | `localhost:5433` (host Postgres owns 5432) |
| Backend API | `8000` | `8000` |
| Frontend (dev) | `3000` | `3000` |

Connection defaults in `backend/app/config.py`: `DATABASE_URL=postgresql://cadastre:cadastre@localhost:5433/ulpin3d` (overridable to `@postgis:5432` in docker).

## Data flow
1. **Datagen** (`app/services/datagen/*`) synthesizes the locality: parcels_2d/building footprints,
   storey stacks (3.2 m floors), underground masses, utility centerlines, metro segments, then renders
   ortho/dsm/ndsm rasters + a LAS point cloud into `data/raw` and authority truth into `data/truth`.
2. **Seed** (`app/scripts/seed.py`) truncates and loads the cadastre: `parcels_2d`, `buildings`,
   `owners`, `parcels_3d` (prism `POLYHEDRALSURFACEZ` solids + `zmin`/`zmax`), `utilities`,
   audit trail — then runs topology validation.
3. **API** serves scene JSON, cadastre rows, ULPIN parse/generate, dashboard stats, conflicts,
   pipeline runs, and raster previews (GeoTIFF + PNG).
4. **Pipeline** (`app/services/pipeline.py`) runs AI extraction over the rasters, assigns 3D ULPINs,
   persists a `pipeline_runs` row, and evaluates against truth.
5. **Frontend** renders dashboard, three.js scene, ULPIN lab, and validation/pipeline views, all
   fetching from the FastAPI backend (`NEXT_PUBLIC_API_URL`, default `http://localhost:8000`).
6. **Reconstruction** (optional, on top of the baseline): synthetic drone imagery + a point cloud
   (nerfstudio `splatfacto` export on a CUDA/Colab worker, or the synthetic LiDAR node), packaged as
   self-describing artifacts the app consumes offline.

## Reconstruction layer (drone imagery + LiDAR → 3D extraction)
The classic nDSM baseline (`stage=extract`) is complemented by a point-cloud stage
(`stage=reconstruct`) that mirrors the nerfstudio/LiDAR workflow:

```mermaid
flowchart LR
  A[data/raw/pointcloud.las] -->|"make_demo_artifact.py<br/>(offline PLY + manifest)"| C[(data/reconstruction/)]
  D[data/raw/drone_views/] -->|generate_drone_views.py| E[transforms.json UTM poses]
  E -->|reconstruct_gpu.py / colab notebook| F[(data/reconstruction/)]
  C --> G[load_manifest]
  F --> G[load_manifest]
  G --> H[cloudseg.detect_buildings<br/>+ segment_floors]
  H --> I[pipeline reconstruct stage → parcels + ULPINs]
```

- **Artifact contract** — `data/reconstruction/manifest.json` + `pointcloud.ply` (+ gridded
  `dsm.tif`). The backend never trains; the GPU job runs once and the app reads artifacts, so the
  demo is fully offline.
- **Drone imagery** — `backend/app/scripts/generate_drone_views.py` renders 24 perspective aerial
  views (720×484, orbit radius 300 m at altitude 230 m, FOV 55°, focal 691.6 px) into
  `data/raw/drone_views/` with `camera_poses.json` (local + UTM frames) and `transforms.json`
  (nerfstudio format, UTM poses).
- **GPU worker** — `backend/app/scripts/reconstruct_gpu.py` runs on a CUDA host/Colab (see
  `colab/nerfstudio_reconstruct.ipynb`): `ns-process-data` → `ns-train splatfacto` → `ns-export
  pointcloud` → georeference (GCP similarity fit via `georeference.estimate_similarity`, or
  pose-seed) → manifest. `backend/app/scripts/make_demo_artifact.py` builds the same contract from
  the synthetic LAS so the stage runs on a laptop with no GPU.
- **Consumption** — the reconstruct stage resolves the cloud through `load_manifest` (preferring
  the artifact PLY, falling back to `pointcloud.las`), reuses `cloudseg.detect_buildings`
  (convex-hull footprints) + `segment_floors` (z-histogram slab peaks) + `classify_volumes`
  (floor/suite/underground/parking/air-right envelopes), then the standard ULPIN encoding &
  validation. Metrics (mask IoU, per-building IoU, floor MAE, ULPIN validity) are computed against
  the same truth as the baseline.
- **Viewer & audit** — `routes/reconstruction.py` serves the manifest + subsampled cloud
  (`/api/reconstruction/*`); the three.js scene has a **3D Reconstruction** point-cloud overlay
  toggle; `/validation` compares **nDSM Baseline vs Point-Cloud Reconstruction** side by side.

### Photoreal buildings (real photos → 3D Gaussian splat → scene)
A real building captured by drone/phone is rendered photoreal inside the cadastre:

```mermaid
flowchart LR
  P[real photos + GCP survey] -->|Colab: ns-train splatfacto| T[INRIA PLY]
  T -->|register_real_building.py<br/>PLY→.splat + pose fit| S[(data/reconstruction/real/{id}/<br/>scene.splat + pose.json)]
  S -->|/api/real (static) + /api/focus/building/{id}| M[Splat (drei) mesh @ pose]
  M --> V[3D scene · on cadastral footprint]
```

- **Training** — nerfstudio `splatfacto` on CUDA/Colab (same worker as the reconstruction layer),
  then `ns-export gaussian-splat` produces an INRIA-style `point_cloud.ply`.
- **Register** — `backend/app/scripts/register_real_building.py` (`--building-id`, `--input`,
  `--gcps` [{local,target} coordinate pairs]) converts the PLY to the 32-byte-per-splat `.splat`
  row format (center f32×3, scale f32×3, rgba u8×4, quat i8×4) and solves the similarity transform
  (scale, yaw, translation) that snaps the splat onto the building's cadastral footprint, writing
  `scene.splat` + `pose.json`.
- **Serve & render** — FastAPI mounts `data/reconstruction/real/` at `/api/real` (static); the
  Focus Area endpoint returns the splat URL + pose when registered. The scene renders it with
  drei's `Splat` (`rotation`/`position`/`scale` = pose), so the photoreal mesh, the cadastral
  prism, and the extracted parcels all align in one coordinate frame.

## Repository map
```
backend/
  app/
    main.py                 # FastAPI app, lifespan db pool, routers, CORS
    config.py               # settings (locality codes, database_url, data_dir)
    db.py                   # asyncpg pool connect/close
    routes/                 # scene, cadastre, ulpins, dashboard, validation, pipeline
    services/
      datagen/              # synthetic locality generation (topology, truth)
      cadastre/             # prisms (solid geometry), validation (conflicts)
      pipeline.py           # AI extraction + ULPIN assignment + evaluation
      reconstruction/       # manifest/georef/gridding/cloudseg/nerfrunner (artifact layer)
      ulpin/                # 3D ULPIN format codec (ULPIN3D, checksum)
    scripts/
      seed.py               # idempotent reseed + validation
      generate_drone_views.py   # synthetic drone imagery + UTM poses
      make_demo_artifact.py     # LAS → PLY + manifest (offline, no GPU)
      reconstruct_gpu.py        # CUDA worker: ns-train splatfacto → PLY + manifest
    models/schemas.py       # pydantic schemas
colab/nerfstudio_reconstruct.ipynb   # one-time GPU/Colab reconstruction run
db/01_schema.sql            # cadastre schema (DDL init for postgis container)
data/
  raw/                      # geojson footprints/utilities, ortho/dsm/ndsm .tif, las, mask
                            #   + drone_views/ (24 PNGs, camera_poses.json, transforms.json)
  reconstruction/           # manifest.json, pointcloud.ply, dsm.tif (artifact contract)
  truth/                    # volumes.geojson, floor_counts.json, building masks
docs/                       # this documentation set
frontend/
  app/                      # / , /scene, /ulpin, /validation (App Router)
  components/Scene.tsx      # three.js volumetric viewer over ortho ground plane
  lib/api.ts                # typed fetch client for the backend
```

## API surface
| Route | Method | Purpose |
| --- | --- | --- |
| `/health` | GET | app + DB health |
| `/api/scene` | GET | GeoJSON scene with `?bounds=` |
| `/api/cadastre/parcels`, `/parcels/{id}`, `/buildings`, `/parcels/by-ulpin/{ulpin3d}` | GET | cadastre lookups |
| `/api/ulpins/parse/{code}` | GET | validate + decode 3D ULPIN |
| `/api/ulpins/generate` | POST | compose 3D ULPIN from base + descriptor |
| `/api/ulpins/base/{parcel_no}` | GET | compose base 14-char ULPIN |
| `/api/dashboard/stats` | GET | aggregate counts, volume, area, conflicts |
| `/api/validation/run`, `/conflicts` | POST / GET | run / list topology conflicts |
| `/api/pipeline/run?stage=extract|reconstruct`, `/last`, `/parcels` | POST / GET | run + fetch extraction results / overlay GeoJSON |
| `/api/reconstruction/manifest`, `/cloud`, `/run` | GET / GET / POST | nerfstudio/LiDAR artifact manifest, subsampled cloud, re-run stage |
| `/api/focus/building/{id}`, `/api/focus/raster/{name}` | GET | Focus Area dossier (bbox, parcel stack, cloud density, raster crops, photoreal splat) / cropped raster PNG |
| `/api/real/{id}/scene.splat` | GET | registered photoreal building splat (static) |
| `/api/raster/{name}`, `/api/raster/{name}/png` | GET | raw GeoTIFF / preview PNG (`ndsm`, `ortho`, …) |

Frontend API base: `frontend/lib/api.ts` → `process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"`.