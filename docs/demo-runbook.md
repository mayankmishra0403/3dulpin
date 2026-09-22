# Demo Runbook

Two options: **all-Docker** (self-contained) or **local dev** (faster iteration). Ports below assume
local dev; Docker maps `postgis:5432` → host **5433**, backend **8000**, frontend **3000**.

## Prerequisites
- Docker, Node ≥ 22, Python 3.12/uv (or a venv), and PostGIS client tooling (`psql`).
- Host port **5433** free (5432 is reserved for a local brew Postgres on this machine).

## 1 — Start the database
```bash
docker compose up -d postgis      # runs ./db/01_schema.sql on first boot
PGPASSWORD=cadastre psql -h localhost -p 5433 -U cadastre -d ulpin3d -c "\dt cadastre.*"
```

## 2 — Backend
```bash
cd backend
uv sync                                  # if using uv; else: python -m venv .venv && pip install -r requirements.txt
nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 &
```
Rapid same-size edits can leave stale bytecode — before restarting after a small change:
```bash
find app -name "__pycache__" -type d -exec rm -rf {} +   # then kill & restart uvicorn (no --reload)
```

## 3 — Seed + validate
```bash
cd ..   # repo root
PYTHONPATH=backend backend/.venv/bin/python -m app.scripts.seed data
```
Expect: parcels_2d 36 · buildings 28 · parcels_3d 235 · owners 28 · utilities 9, and exactly
**1 conflict** (underground_overlap, high).

## 4 — Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:3000 (uses NEXT_PUBLIC_API_URL ?? http://localhost:8000)
```

## 5 — Smoke test the API
```bash
curl -s localhost:8000/health
curl -s "localhost:8000/api/scene?bounds=0,0,392,362" | head -c 200
curl -s localhost:8000/api/dashboard/stats
curl -s localhost:8000/api/ulpins/parse/06080704000021-U38
curl -s localhost:8000/api/validation/conflicts
curl -s localhost:8000/api/reconstruction/manifest   # 200 once artifacts exist (data/reconstruction/)
curl -s "localhost:8000/api/reconstruction/cloud?limit=5000"
```

## 5a — (Rebuild) the reconstruction artifact
The repo ships `data/reconstruction/` (manifest + PLY) so the reconstruct stage runs everywhere.

- **No GPU (recommended for the demo):** rebuild from synthetic LiDAR
  ```bash
  PYTHONPATH=backend backend/venv/bin/python backend/app/scripts/make_demo_artifact.py
  PYTHONPATH=backend backend/venv/bin/python -c "from app.services.pipeline import run_pipeline; print(run_pipeline('data', stage='reconstruct')['evaluation'])"
  ```
- **With a CUDA/Colab GPU (one-time):** generate drone imagery, then train **splatfacto**
  ```bash
  PYTHONPATH=backend backend/venv/bin/python backend/app/scripts/generate_drone_views.py
  PYTHONPATH=backend backend/venv/bin/python backend/app/scripts/reconstruct_gpu.py \
      --data data/raw/drone_views --method splatfacto --max-iter 20000 \
      --skip-colmap --pose-seed --data-dir data
  ```
  or run `colab/nerfstudio_reconstruct.ipynb` and download `data/reconstruction/` back.
- Either path writes the same contract (`manifest.json`, `pointcloud.ply`); drop in the GPU export to
  demo the true nerfstudio artifact — the app cannot tell the difference.

## 5b — Register a photoreal building (photos → scene)
For a **real building** rendered photoreal in the scene, export the trained splat as an INRIA
`point_cloud.ply` (`ns-export gaussian-splat`) and register it against a cadastral building:

```bash
PYTHONPATH=backend backend/venv/bin/python backend/app/scripts/register_real_building.py \
    --building-id 253 --input exports/splat/point_cloud/iteration_30000/point_cloud.ply \
    --gcps data/raw/site/gcps.json
```

Writes `data/reconstruction/real/253/{scene.splat, pose.json}`; the Focus Area panel flags it and
`GET /api/focus/building/253` returns the splat URL + pose for the scene to render. A registered
demo splat for building 253 is already present in `data/reconstruction/real/`.

## Live demo script (≈5 min)
1. **Dashboard** (`/`) — locality header, KPI cards (235 parcels, ≈904,668 m³, 318,106 m²,
   28 buildings, 1 conflict, 3.29 km utility), category chips, the open conflict card.
2. **Scene** (`/scene`) — orbit the volumetric parcels over the ortho ground plane; click a tower
   to highlight its 3D ULPIN. Show a suite tower (blue), surface lots (olive), parking (pink),
   the underground metro band. Toggle **3D Reconstruction** in the control bar to swap the extruded
   scene for the point-cloud mesh (LiDAR/nerfstudio export) over the same ground — hit the presets to
   fly through the buildings.
   - **Focus Area / real data** — click a building and open the inspector: the **Focus Area · Real Data**
     card shows ortho / nDSM / truth-mask crops (`/api/focus/raster/*`), the parcel stack count, and
     the LiDAR return density inside the footprint. If a registered photoreal splat exists, the badge
     *Photoreal 3D — rendered in scene* appears and the building is drawn photoreal (from photos) on
     its cadastral footprint via drei `Splat`.
3. **ULPIN Lab** (`/ulpin`) — generate `F03.U11` on parcel `…000021`; parse `06080704000021-U38`
   and `06080704900001-MTA17` to show vertical math (level 38 / metro segment A17) + checksum.
4. **AI Pipeline** (`/validation`) — press **Run pipeline**; show mask IoU 0.63, building recall
   18/28, floor MAE 0.0, 253 cooked ULPINs, the per-building IoU table, and the topology conflicts.
   Then press **Run Comparison** → nDSM Baseline 18/28 vs Point-Cloud Reconstruction **28/28**
   (IoU 0.6266 vs 0.6211, floor MAE 0.0 both).
5. Close with the pitch: 3D ULPINs make vertical property parts first-class, topology validation
   catches underground collisions, and the AI pipeline is scored honestly against authoritative data
   across both a classic raster method and a modern point-cloud/nerfstudio method.

## Notes / gotchas
- Docker backend env uses `DATABASE_URL=…@postgis:5432/ulpin3d`; local dev uses `localhost:5433`.
- Port 3000 may already be occupied by an unrelated `next-server` — check `lsof -nP -iTCP:3000 -sTCP:LISTEN`.
- `data/` is regenerable: datagen recreates `data/raw` + `data/truth`; seed reloads PostGIS.
- No SFCGAL in the PostGIS image — all 3D topology is GEOS/bbox math (`see docs/architecture.md`).