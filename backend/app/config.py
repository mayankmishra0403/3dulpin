from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "3D ULPIN Cadastre"
    database_url: str = "postgresql://cadastre:cadastre@localhost:5433/ulpin3d"
    data_dir: str = "./data"

    # Reconstruction artifacts live under data_dir/reconstruction (see
    # app/services/reconstruction/); GPU nerfstudio jobs run on a worker.
    reconstruction_method: str = "splatfacto"
    reconstruction_source: str = "synthetic_drone"

    # Demo locality ULPIN coding (DoLR-style codes)
    demo_state_code: str = "06"          # Haryana
    demo_district_code: str = "08"       # Gurugram
    demo_sub_district_code: str = "07"   # Gurugram tehsil
    demo_village_code: str = "04"        # demo locality
    demo_utm_zone: int = 32643           # UTM 43N
    demo_epsg_wgs84: int = 4326

    # CORS
    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()