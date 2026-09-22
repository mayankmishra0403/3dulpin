"""Synthetic demo-locality topology builder.

Builds a georeferenced miniature urban area in UTM metres with:
  * surface parcels (2D) in a 3 x 3 block grid separated by roads
  * buildings (walk-up / tower / commercial) with ground-truth floor counts
  * underground basements (parking) under towers
  * a metro tunnel corridor along the central axis
  * utility duct banks along each vertical road
  * open ground & vegetation in park blocks

All z values are metres above a planar datum (ground z = 0).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, radians, sin

import numpy as np
from pyproj import Transformer

SRID_WGS84 = 4326
SRID_UTM = 32643

STOREY_HT = 3.2      # full storey pitch (floors + slab) metres
SLAB_HT = 0.2
FLOOR_HT = STOREY_HT - SLAB_HT  # clear storey envelope height


def rect(x0: float, y0: float, x1: float, y1: float) -> list[tuple[float, float]]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


@dataclass
class Parcel2D:
    pid: int
    parcel_no: int
    usage: str
    ring: list[tuple[float, float]]      # closed footprint (UTM m)
    building_id: int | None = None

    @property
    def centroid(self) -> tuple[float, float]:
        xs = [p[0] for p in self.ring]
        ys = [p[1] for p in self.ring]
        return (sum(xs) / len(xs), sum(ys) / len(ys))


@dataclass
class Building:
    bid: int
    parcel_id: int
    name: str
    footprint: list[tuple[float, float]]   # closed ring, UTM m
    floor_count: int
    parcel_type: str      # 'floor' per-storey parcels | 'suite' subdivided storeys
    suites_per_floor: int = 1
    commercial: bool = False
    roof_type: str = "flat"

    @property
    def ground_z(self) -> float:
        return 0.0

    @property
    def height_m(self) -> float:
        return self.floor_count * STOREY_HT


@dataclass
class UtilAsset:
    uid: int
    kind: str             # water | sewage | electric | telecom | metro
    operator: str
    ring: list[tuple[float, float]]   # plan footprint rectangle, UTM m
    zmin: float
    zmax: float
    diameter_m: float | None = None

    @property
    def asset_code(self) -> str:
        from app.services.ulpin.ulpin import UTILITY_ASSET

        if self.kind == "metro":
            return "A1"
        return UTILITY_ASSET[self.kind]


@dataclass
class Tree:
    x: float
    y: float
    r: float          # crown radius
    h: float          # crown top height


@dataclass
class LocalityModel:
    parcels: list[Parcel2D] = field(default_factory=list)
    buildings: list[Building] = field(default_factory=list)
    assets: list[UtilAsset] = field(default_factory=list)
    trees: list[Tree] = field(default_factory=list)
    origin_lat: float = 28.4593
    origin_lon: float = 77.0258
    utm_origin: tuple[float, float] = (0.0, 0.0)
    minx: float = 0.0
    miny: float = 0.0
    maxx: float = 0.0
    maxy: float = 0.0

    # convenience look-ups
    parcel_by_pid: dict[int, Parcel2D] = field(default_factory=dict)
    building_by_bid: dict[int, Building] = field(default_factory=dict)

    def index(self) -> None:
        self.parcel_by_pid = {p.pid: p for p in self.parcels}
        self.building_by_bid = {b.bid: b for b in self.buildings}


def build_model(
    *,
    blocks_x: int = 3,
    blocks_y: int = 3,
    block_w: float = 120.0,
    block_h: float = 110.0,
    road: float = 16.0,
    seed: int = 42,
    max_floors: int = 8,
    include_metro: bool = True,
    origin_lat: float = 28.4593,
    origin_lon: float = 77.0258,
) -> LocalityModel:
    rng = np.random.default_rng(seed)

    tf = Transformer.from_crs(SRID_WGS84, SRID_UTM, always_xy=True)
    utm_origin = tf.transform(origin_lon, origin_lat)

    model = LocalityModel(origin_lat=origin_lat, origin_lon=origin_lon, utm_origin=utm_origin)

    total_w = blocks_x * block_w + (blocks_x - 1) * road
    total_h = blocks_y * block_h + (blocks_y - 1) * road
    model.minx, model.miny = 0.0, 0.0
    model.maxx, model.maxy = total_w, total_h

    pid = 0
    bid = 0

    # ---- rectangular parcel helper ------------------------------------
    def add_parcel(x0, y0, x1, y1, usage, building=None) -> Parcel2D:
        nonlocal pid
        pid += 1
        p = Parcel2D(pid=pid, parcel_no=pid, usage=usage, ring=rect(x0, y0, x1, y1))
        if building is not None:
            p.building_id = building
        model.parcels.append(p)
        return p

    # ---- generate blocks ------------------------------------------------
    for j in range(blocks_y):
        for i in range(blocks_x):
            bx = i * (block_w + road)
            by = j * (block_h + road)
            k = j * blocks_x + i

            # block type by pseudo-random pattern (deterministic per seed)
            role = rng.choice(["tower", "mixed", "commercial", "park"])
            if (i + j) % 3 == 0:
                role = "tower"
            elif (i + j) % 3 == 1:
                role = "mixed"
            else:
                role = "commercial"
            if (i == blocks_x // 2 and j == blocks_y // 2) or (blocks_x < 3 and j == 0):
                role = "park"

            inset = 3.0
            gap = 2.0
            cell_w = (block_w - 2 * inset - gap) / 2.0
            cell_h = (block_h - 2 * inset - gap) / 2.0

            cells = [
                (bx + inset, by + inset, bx + inset + cell_w, by + inset + cell_h),
                (bx + inset + cell_w + gap, by + inset, bx + block_w - inset, by + inset + cell_h),
                (bx + inset, by + inset + cell_h + gap, bx + inset + cell_w, by + block_h - inset),
                (bx + inset + cell_w + gap, by + inset + cell_h + gap, bx + block_w - inset, by + block_h - inset),
            ]

            if role == "park":
                # open ground + some trees, one tiny pavilion in a corner cell
                cx0, cy0, cx1, cy1 = cells[0]
                add_parcel(cx0, cy0, cx1, cy1, "open_space")
                for cx0, cy0, cx1, cy1 in cells[1:3]:
                    add_parcel(cx0, cy0, cx1, cy1, "open_space")
                for _ in range(14):
                    tx = bx + rng.uniform(inset + 4, block_w - inset - 4)
                    ty = by + rng.uniform(inset + 4, block_h - inset - 4)
                    model.trees.append(Tree(x=tx, y=ty, r=rng.uniform(2.0, 3.6), h=rng.uniform(5.0, 11.0)))
                # tiny pavilion (1 storey) in cell 3
                px0, py0, px1, py1 = cells[3]
                f = rect(px0 + 2, py0 + 2, px1 - 2, py1 - 2)
                bid += 1
                b = Building(bid=bid, parcel_id=0, name=f"Park Pavilion {k + 1}",
                             footprint=f, floor_count=1, parcel_type="floor")
                model.buildings.append(b)
                add_parcel(px0, py0, px1, py1, "civic", building=b.bid).building_id = b.bid
                b.parcel_id = model.parcels[-1].pid
                continue

            tower_cell = 0
            if role == "tower":
                # one tall tower, remaining cells small shop units
                floors = int(rng.integers(8, max_floors + 3))
                tower_parcel = add_parcel(*cells[0], "residential_highrise")
                t0, t1 = cells[0][0] + 2.5, cells[0][2] - 2.5
                u0, u1 = cells[0][1] + 2.5, cells[0][3] - 2.5
                f = rect(t0, u0, t1, u1)
                bid += 1
                b = Building(bid=bid, parcel_id=tower_parcel.pid,
                             name=f"{'Sky' if floors >= 10 else 'Green'} Tower {k + 1}",
                             footprint=f, floor_count=floors, parcel_type="suite",
                             suites_per_floor=4)
                model.buildings.append(b)
                tower_parcel.building_id = b.bid
                for c in cells[1:]:
                    p = add_parcel(*c, "commercial_retail")
                    f2 = rect(c[0] + 1.5, c[1] + 1.5, c[2] - 1.5, c[3] - 1.5)
                    bid += 1
                    b2 = Building(bid=bid, parcel_id=p.pid, name=f"Shop Row {k + 1}-{c[0]:.0f}",
                                  footprint=f2, floor_count=2, parcel_type="floor",
                                  commercial=True)
                    model.buildings.append(b2)
                    p.building_id = b2.bid
            elif role == "mixed":
                for ci, c in enumerate(cells):
                    if ci == 3:
                        add_parcel(*c, "open_space")
                        for _ in range(6):
                            tx = c[0] + rng.uniform(1, cell_w - 1)
                            ty = c[1] + rng.uniform(1, cell_h - 1)
                            model.trees.append(Tree(x=tx, y=ty, r=rng.uniform(1.8, 3.0), h=rng.uniform(4.0, 9.0)))
                        continue
                    p = add_parcel(*c, "residential_walkup")
                    f2 = rect(c[0] + 2.0, c[1] + 2.0, c[2] - 2.0, c[3] - 2.0)
                    floors = int(rng.integers(2, 4))
                    bid += 1
                    b = Building(bid=bid, parcel_id=p.pid, name=f"WalkUp {k + 1}-{ci + 1}",
                                 footprint=f2, floor_count=floors, parcel_type="floor")
                    model.buildings.append(b)
                    p.building_id = b.bid
            else:  # commercial
                for ci, c in enumerate(cells):
                    if ci == 1:
                        add_parcel(*c, "open_space")
                        continue
                    p = add_parcel(*c, "commercial_retail")
                    f2 = rect(c[0] + 1.2, c[1] + 1.2, c[2] - 1.2, c[3] - 1.2)
                    bid += 1
                    b = Building(bid=bid, parcel_id=p.pid, name=f"Market {k + 1}-{ci + 1}",
                                 footprint=f2, floor_count=1, parcel_type="floor", commercial=True)
                    model.buildings.append(b)
                    p.building_id = b.bid

    # ---- metro tunnel along central y-axis --------------------------------
    if include_metro and blocks_y > 1:
        cy = (blocks_y - 1) * (block_h + road) / 2.0
        cy0, cy1 = cy - 4.0, cy + 4.0
        # span across x with a short jiggle to avoid being perfectly linear
        pts = [(0.0, cy + (sin(radians(x / 40)) * 6.0)) for x in range(0, int(total_w) + 1, 20)]
        z0, z1 = -17.0, -12.0
        ring = rect(0.0, cy - 4.0, total_w, cy + 4.0)
        model.assets.append(UtilAsset(uid=len(model.assets) + 1, kind="metro",
                                      operator="Metro Authority",
                                      ring=ring, zmin=z0, zmax=z1, diameter_m=8.0))

    # ---- utility ducts along vertical roads ------------------------------
    depth = {"water": (2.5, 2.1), "sewage": (3.3, 2.8), "electric": (1.7, 1.4), "telecom": (1.25, 1.05)}
    for i in range(1, blocks_x):
        rx = i * (block_w + road) - road / 2.0
        for kind, (zd, zg) in depth.items():
            ring2 = rect(rx + 0.4, 0.0, rx + 0.55, total_h)
            model.assets.append(UtilAsset(uid=len(model.assets) + 1, kind=kind,
                                          operator={"water": "Water Board", "sewage": "Sewerage Board",
                                                    "electric": "Power Utility", "telecom": "Telecom Co"}[kind],
                                          ring=ring2, zmin=-zd, zmax=-zg, diameter_m=0.3))

    model.index()
    return model