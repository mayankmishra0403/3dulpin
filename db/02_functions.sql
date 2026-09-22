-- ============================================================
-- 3D ULPIN — PostGIS helper functions (SFCGAL-free)
-- Volumetric parcels are persisted as closed POLYHEDRALSURFACEZ
-- prisms built in Python (app.services.cadastre.prisms).
-- Overlap *detection* uses core-GEOS ST_3DIntersects; overlap
-- *volumes* are computed exactly in Python (the demo solids are
-- axis-aligned prisms, so dX*dY*dZ of the intersecting extents).
-- ============================================================

-- Convenience: projected area of a 3D parcel in square metres.
CREATE OR REPLACE FUNCTION cadastre.horiz_area3d(p cadastre.parcels_3d)
RETURNS DOUBLE PRECISION LANGUAGE SQL IMMUTABLE AS $$
    SELECT ST_Area(p.footprint)
$$;

-- Candidate pairs that intersect in 3D (core-GEOS boolean test).
-- Volume of the intersection is computed analytically by the API layer.
CREATE OR REPLACE FUNCTION cadastre.intersects_3d(a cadastre.parcels_3d, b cadastre.parcels_3d)
RETURNS BOOLEAN LANGUAGE SQL STABLE AS $$
    SELECT COALESCE(ST_3DIntersects(a.solid, b.solid), false)
$$;