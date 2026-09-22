"""Construct closed 3D prism solids (POLYHEDRALSURFACEZ) for PostGIS.

PostGIS 3D intersection operations (ST_3DIntersects / ST_3DIntersection /
ST_3DVolume) behave reliably when parcels are represented as *closed*
polyhedral surfaces, so every volcanic parcel is persisted as a vertical
prism between [zmin, zmax].
"""

from __future__ import annotations

from typing import Sequence

SQRT = None  # (placeholder to keep module header tidy)


def prism_wkt(coords: Sequence[tuple[float, float]], zmin: float, zmax: float) -> str:
    """WKT of a closed POLYHEDRALSURFACEZ prism for a 2D footprint ring.

    `coords` is the closed exterior ring (first == last). The surface is
    composed of: bottom face, top face, and one side face per edge.
    """
    if len(coords) < 4:
        raise ValueError("footprint must have at least one closed ring of 3 distinct points")
    # normalise: force closed ring
    ring = list(coords)
    if ring[0] != ring[-1]:
        ring = ring + [ring[0]]

    faces: list[str] = []

    # bottom & top caps
    def cap(z: float) -> str:
        pts = ", ".join(f"{x} {y} {z}" for x, y in ring[:-1])
        x0, y0 = ring[0]
        return f"(({pts}, {x0} {y0} {z}))"

    faces.append(cap(zmin))
    faces.append(cap(zmax))

    # side faces
    for (x1, y1), (x2, y2) in zip(ring[:-1], ring[1:]):
        faces.append(
            f"(({x1} {y1} {zmin}, {x2} {y2} {zmin}, "
            f"{x2} {y2} {zmax}, {x1} {y1} {zmax}, {x1} {y1} {zmin}))"
        )

    return "POLYHEDRALSURFACEZ (" + ", ".join(faces) + ")"


def prism_ewkt(coords: Sequence[tuple[float, float]], zmin: float, zmax: float, srid: int = 32643) -> str:
    return f"SRID={srid};{prism_wkt(coords, zmin, zmax)}"


def footprint_ring_wkt(coords: Sequence[tuple[float, float]], srid: int = 32643) -> str:
    ring = list(coords)
    if ring[0] != ring[-1]:
        ring = ring + [ring[0]]
    pts = ", ".join(f"{x} {y}" for x, y in ring)
    return f"SRID={srid};POLYGON(({pts}))"