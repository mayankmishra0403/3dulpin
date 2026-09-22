from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import db
from app.config import settings
from app.routes import cadastre, dashboard, focus, pipeline, reconstruction, scene, ulpins, validation


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="3D ULPIN generation & vertical property mapping — volumetric cadastre prototype",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origins] if settings.cors_origins != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scene.router)
app.include_router(cadastre.router)
app.include_router(ulpins.router)
app.include_router(dashboard.router)
app.include_router(validation.router)
app.include_router(pipeline.router)
app.include_router(reconstruction.router)
app.include_router(focus.router)

# photoreal building splats (real photos → 3DGS) — data/reconstruction/real/{id}/scene.splat
_REAL_DIR = Path(__file__).resolve().parents[2] / "data" / "reconstruction" / "real"
_REAL_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/real", StaticFiles(directory=_REAL_DIR), name="real")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": app.version,
        "endpoints": [
            "/health",
            "/api/scene",
            "/api/cadastre/*",
            "/api/ulpins/*",
            "/api/dashboard/stats",
            "/api/validation/*",
            "/api/pipeline/*",
            "/api/raster/{name}",
        ],
    }


@app.get("/health")
async def health():
    ok = True
    detail = "ok"
    try:
        await db.pool().fetchval("SELECT 1")
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, str(exc)
    return {"status": "ok" if ok else "degraded", "database": detail}