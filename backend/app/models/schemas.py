from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---- ULPIN -----------------------------------------------------------
class BaseULPINOut(BaseModel):
    value: str
    state_code: str
    district_code: str
    sub_district_code: str
    village_code: str
    parcel_no: str


class ULPINGenerateIn(BaseModel):
    """Generate one or a batch of 3D ULPINs for a base parcel."""
    base_ulpin: str
    category: str = Field(
        description="surface|floor|suite|underground|parking|air_right|utility_network|metro_tunnel|structure"
    )
    level_no: int = 0
    unit_no: Optional[str] = None
    asset: Optional[str] = None


class ULPINOut(BaseModel):
    value: str
    front: str
    base_ulpin: str
    category: str
    level_no: int
    unit_no: Optional[str]
    checksum_ok: bool


class ULPINParseOut(ULPINOut):
    state_code: str
    district_code: str
    sub_district_code: str
    village_code: str
    parcel_no: str


# ---- Cadastre --------------------------------------------------------
class Parcel3DOut(BaseModel):
    id: int
    ulpin3d: str
    base_ulpin: Optional[str]
    building_id: Optional[int]
    category: str
    level_no: int
    unit_no: Optional[str]
    zmin: float
    zmax: float
    usage: Optional[str]
    rights_summary: Optional[str]
    status: str
    centroid: list[float]        # [x, y, z] UTM metres
    footprint: Any               # GeoJSON polygon (UTM metres)
    volume_m3: Optional[float]
    built_up_area_m2: Optional[float]


class ScenebuildingOut(BaseModel):
    id: int
    name: Optional[str]
    floor_count: int
    ground_z: float
    height_m: float
    footprint: Any


class SceneOut(BaseModel):
    origin: list[float]          # [utm_x, utm_y, z0] scene origin (world offset)
    buildings: list[ScenebuildingOut]
    parcels: list[dict[str, Any]] = []
    utilities: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    stats: dict[str, Any] = {}


class DashboardStatsOut(BaseModel):
    by_category: dict[str, int]
    total_parcels: int
    total_volume_m3: float
    total_built_up_area_m2: float
    building_count: int
    open_conflicts: int
    utility_km: float


class ConflictOut(BaseModel):
    id: int
    conflict_type: str
    parcel_a: str
    parcel_b: Optional[str]
    volume_m3: Optional[float]
    area_m2: Optional[float]
    severity: str
    description: Optional[str]
    status: str


class PipelineMetricsOut(BaseModel):
    stage: str
    metrics: dict[str, Any]
    run_id: int


class GenerateDatasetIn(BaseModel):
    seed: int = 42
    blocks_x: int = 3
    blocks_y: int = 3
    point_density: float = 0.5
    max_floors: int = 8
    include_metro: bool = True