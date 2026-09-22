-- ============================================================
-- 3D ULPIN cadastre schema — volumetric land administration
-- SRID: 32643 (UTM 43N, metres) for Gurugram demo locality.
-- All z offsets are metres above ellipsoid-derived orthometric datum
-- (DEM base plane set to z=0 in the synthetic dataset).
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS cadastre;

-- ---- 2D surface parcels (official-style base ULPIN) ---------
CREATE TABLE IF NOT EXISTS cadastre.parcels_2d (
    id              BIGSERIAL PRIMARY KEY,
    ulpin           VARCHAR(14) UNIQUE NOT NULL,          -- base 2D ULPIN (14 chars)
    state_code      VARCHAR(2)  NOT NULL,
    district_code   VARCHAR(2)  NOT NULL,
    sub_district_code VARCHAR(2) NOT NULL,
    village_code    VARCHAR(2)  NOT NULL,
    parcel_no       VARCHAR(6)  NOT NULL,
    geom            GEOMETRY(POLYGON, 32643) NOT NULL,
    area_m2         NUMERIC,
    usage           VARCHAR(64),
    land_class      VARCHAR(32) DEFAULT 'urban',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---- Buildings ----------------------------------------------
CREATE TABLE IF NOT EXISTS cadastre.buildings (
    id               BIGSERIAL PRIMARY KEY,
    name             VARCHAR(120),
    parcel2d_id      BIGINT REFERENCES cadastre.parcels_2d(id),
    footprint        GEOMETRY(POLYGON, 32643) NOT NULL,
    floor_count      INT NOT NULL,
    ground_z         DOUBLE PRECISION NOT NULL DEFAULT 0,
    height_m         DOUBLE PRECISION NOT NULL,
    roof_type        VARCHAR(24) DEFAULT 'flat',
    source           VARCHAR(16) NOT NULL DEFAULT 'truth',  -- truth | ai
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---- 3D volumetric parcels ----------------------------------
CREATE TYPE cadastre.category AS ENUM (
    'surface',          -- ground-level parcel volume
    'floor',            -- one storey envelope
    'suite',            -- apartment / office unit within a floor
    'underground',      -- basement / below-ground parcel
    'parking',          -- parking stack / space
    'air_right',        -- air-space rights above a footprint
    'utility_network',  -- utility corridor / duct / ductbank
    'metro_tunnel',     -- transit tunnel / station void
    'structure'         -- structural element (slab, column, shaft)
);

CREATE TABLE IF NOT EXISTS cadastre.parcels_3d (
    id              BIGSERIAL PRIMARY KEY,
    ulpin3d         TEXT UNIQUE NOT NULL,
    base_ulpin      VARCHAR(14) REFERENCES cadastre.parcels_2d(ulpin) ON DELETE SET NULL,
    building_id     BIGINT REFERENCES cadastre.buildings(id),
    category        cadastre.category NOT NULL,
    level_no        INT NOT NULL DEFAULT 0,        -- F floors >=1, 0 ground/surface, underground <0
    unit_no         VARCHAR(8),                    -- suite/unit within a floor
    zmin            DOUBLE PRECISION NOT NULL,
    zmax            DOUBLE PRECISION NOT NULL,
    footprint       GEOMETRY(POLYGON, 32643) NOT NULL,
    solid           GEOMETRY(POLYHEDRALSURFACEZ, 32643),  -- closed 3D prism for ST_3D* ops
    centroid        GEOMETRY(POINTZ, 32643),
    built_up_area_m2 NUMERIC,
    volume_m3       NUMERIC,
    usage           VARCHAR(64),
    rights_summary  TEXT,                          -- human-readable ownership rights descriptor
    status          VARCHAR(16) NOT NULL DEFAULT 'active',  -- active | conflict | merged | pending
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (zmax > zmin)
);

CREATE INDEX IF NOT EXISTS idx_p3d_ulpin        ON cadastre.parcels_3d (ulpin3d);
CREATE INDEX IF NOT EXISTS idx_p3d_category     ON cadastre.parcels_3d (category);
CREATE INDEX IF NOT EXISTS idx_p3d_building     ON cadastre.parcels_3d (building_id);
CREATE INDEX IF NOT EXISTS idx_p3d_solid_gist   ON cadastre.parcels_3d USING GIST (solid);
CREATE INDEX IF NOT EXISTS idx_p3d_footprint_gist ON cadastre.parcels_3d USING GIST (footprint);
CREATE INDEX IF NOT EXISTS idx_p2d_ulpin        ON cadastre.parcels_2d (ulpin);
CREATE INDEX IF NOT EXISTS idx_p2d_geom_gist    ON cadastre.parcels_2d USING GIST (geom);

-- ---- Utility infrastructure --------------------------------
CREATE TABLE IF NOT EXISTS cadastre.utilities (
    id          BIGSERIAL PRIMARY KEY,
    type        VARCHAR(32) NOT NULL,             -- water | sewage | electric | telecom | metro
    operator    VARCHAR(120) NOT NULL,
    parcel3d_id BIGINT REFERENCES cadastre.parcels_3d(id),
    service_geometry GEOMETRY(MULTILINESTRINGZ, 32643),  -- pipe/track axis
    solid       GEOMETRY(POLYHEDRALSURFACEZ, 32643),
    depth_m     DOUBLE PRECISION,                 -- top of asset below grade
    diameter_m  DOUBLE PRECISION,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_util_geom ON cadastre.utilities USING GIST (service_geometry);
CREATE INDEX IF NOT EXISTS idx_util_solid ON cadastre.utilities USING GIST (solid);

-- ---- Owners & ownership rights ----------------------------
CREATE TABLE IF NOT EXISTS cadastre.owners (
    id          BIGSERIAL PRIMARY KEY,
    full_name   VARCHAR(160) NOT NULL,
    id_type     VARCHAR(16)  NOT NULL DEFAULT 'UIDAI',
    id_value    VARCHAR(30),
    contact     VARCHAR(60)
);

CREATE TABLE IF NOT EXISTS cadastre.ownership (
    parcel3d_id BIGINT NOT NULL REFERENCES cadastre.parcels_3d(id) ON DELETE CASCADE,
    owner_id    BIGINT NOT NULL REFERENCES cadastre.owners(id),
    share       NUMERIC(5,4) NOT NULL DEFAULT 1,
    right_type  VARCHAR(32) NOT NULL DEFAULT 'Owned',  -- Owned | Leased | Easement | Right-of-Way | Air Right | Parapet Easement
    valid_from  DATE,
    valid_to    DATE,
    PRIMARY KEY (parcel3d_id, owner_id)
);

-- ---- Topology / validation conflicts ----------------------
CREATE TYPE cadastre.conflict_type AS ENUM (
    '3D_overlap',           -- two 3D parcels intersect volumetrically
    'underground_overlap',  -- underground asset collides with tunnel/duct/parking
    'vertical_gap',         -- unassigned void between stacked floors
    'duplicate_ulpin',      -- same 3D ULPIN on two geometries
    'height_exceed',        -- parcel zmax exceeds building declared height
    'slab_discontinuity'    -- floor slab float / gap detected
);

CREATE TABLE IF NOT EXISTS cadastre.conflicts (
    id           BIGSERIAL PRIMARY KEY,
    conflict_type cadastre.conflict_type NOT NULL,
    parcel_a     TEXT NOT NULL,
    parcel_b     TEXT,
    geometry     GEOMETRY(POLYHEDRALSURFACEZ, 32643),
    volume_m3    DOUBLE PRECISION,
    area_m2      DOUBLE PRECISION,
    severity     VARCHAR(16) NOT NULL DEFAULT 'high',   -- high | medium | low
    description  TEXT,
    status       VARCHAR(16) NOT NULL DEFAULT 'open',   -- open | acknowledged | resolved
    resolved_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_conflict_type  ON cadastre.conflicts (conflict_type);
CREATE INDEX IF NOT EXISTS idx_conflict_parcel ON cadastre.conflicts (parcel_a, parcel_b);
CREATE INDEX IF NOT EXISTS idx_conflict_geom ON cadastre.conflicts USING GIST (geometry);

-- ---- Audit trail -------------------------------------------
CREATE TABLE IF NOT EXISTS cadastre.audit (
    id         BIGSERIAL PRIMARY KEY,
    ulpin3d    TEXT,
    action     VARCHAR(32) NOT NULL,   -- create | update | validate | merge
    actor      VARCHAR(64),
    detail     JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---- AI pipeline runs --------------------------------------
CREATE TABLE IF NOT EXISTS cadastre.pipeline_runs (
    id          SERIAL PRIMARY KEY,
    dataset     VARCHAR(120),
    stage       VARCHAR(32),
    metrics     JSONB,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);