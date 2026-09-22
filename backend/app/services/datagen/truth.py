"""Ground-truth 3D cadastre built from the synthetic locality model.

Produces the authoritative volumetric parcels (surface, floors, suites,
basements, parking slots, air rights, utilities, metro) that seed PostGIS
and serve as reference for evaluating the AI pipeline.
"""

from dataclasses import dataclass

from .topology import STOREY_HT, Building, LocalityModel, UtilAsset, rect

INDIAN_NAMES = [
    "Ramesh Gupta", "Sunita Krishnan", "Amitabh Sharma", "Farida Begum",
    "Krishna Iyer", "Manpreet Kaur", "Dinesh Yadav", "Lakshmi Narayanan",
    "Rajesh Kumar", "Ananya Bhattacharya", "Vikram Rathore", "Sushma Devi",
    "Arjun Nair", "Priya Deshpande", "Gopal Chawla", "Neha Saxena",
]


@dataclass
class VolumeParcel:
    key: str
    base_ulpin: str
    category: str
    level_no: int
    unit_no: str | None
    zmin: float
    zmax: float
    ring: list[tuple[float, float]]
    usage: str
    owner: str
    right_type: str = "Owned"
    building_id: int | None = None
    asset: str | None = None

    def __post_init__(self) -> None:
        self.ring = list(self.ring)
        if self.ring[0] != self.ring[-1]:
            self.ring = self.ring + [self.ring[0]]


def _subdivide(ring: list[tuple[float, float]], nx: int, ny: int) -> list[list[tuple[float, float]]]:
    """Split a rectangular footprint into an nx x ny grid of footprint rings."""
    xs0, ys0 = ring[0]
    xs1, ys1 = ring[2]
    out = []
    for gy in range(ny):
        for gx in range(nx):
            x0 = xs0 + (xs1 - xs0) * gx / nx
            x1 = xs0 + (xs1 - xs0) * (gx + 1) / nx
            y0 = ys0 + (ys1 - ys0) * gy / ny
            y1 = ys0 + (ys1 - ys0) * (gy + 1) / ny
            out.append(rect(x0, y0, x1, y1))
    return out


def build_truth_volumes(model: LocalityModel) -> list[VolumeParcel]:
    from app.services.ulpin.ulpin import LocalityCodes

    codes = LocalityCodes(
        state_code="06", district_code="08",
        sub_district_code="07", village_code="04",
    )
    vols: list[VolumeParcel] = []
    owner_it = 0

    def next_owner() -> str:
        nonlocal owner_it
        name = INDIAN_NAMES[owner_it % len(INDIAN_NAMES)]
        owner_it += 1
        return name

    # ---- surface parcels ------------------------------------------------
    for p in model.parcels:
        base = codes.base(p.parcel_no)
        owner = next_owner()
        if p.usage in ("open_space", "civic"):
            owner = "Municipal Corporation"
        b = f"b{p.building_id}" if p.building_id else None
        right = "Civic Trust" if owner == "Municipal Corporation" else "Owned"
        # built parcels: thin land slab just below grade (occupants start at z=0);
        # open parcels: thin surface slab at grade
        if p.building_id is not None:
            surf_z0, surf_z1 = -0.2, 0.0
        else:
            surf_z0, surf_z1 = 0.0, 0.2
        vols.append(VolumeParcel(
            key=f"p{p.pid}-surface", base_ulpin=base, category="surface",
            level_no=0, unit_no=None, zmin=surf_z0, zmax=surf_z1,
            ring=p.ring, usage=p.usage, owner=owner, right_type=right,
            building_id=p.building_id,
        ))

    # ---- building volumes ------------------------------------------------
    for b in model.buildings:
        base = codes.base(model.parcel_by_pid[b.parcel_id].parcel_no)
        floors = b.floor_count

        if b.parcel_type == "suite":
            # full-storey envelopes as suites (2x2 units)
            units = _subdivide(b.footprint, 2, 2)
            letters = ["A", "B", "C", "D"]
            for level in range(1, floors + 1):
                z0 = (level - 1) * STOREY_HT
                z1 = z0 + STOREY_HT
                for idx, ring in enumerate(units):
                    owner = next_owner()
                    vols.append(VolumeParcel(
                        key=f"b{b.bid}-f{level}-u{letters[idx]}", base_ulpin=base,
                        category="suite", level_no=level, unit_no=letters[idx],
                        zmin=z0, zmax=z1, ring=ring,
                        usage="residential_apartment", owner=owner,
                        building_id=b.bid,
                    ))
        else:
            for level in range(1, floors + 1):
                z0 = (level - 1) * STOREY_HT
                z1 = z0 + STOREY_HT
                owner = "Commercial Board" if b.commercial else next_owner()
                right = "Leased" if b.commercial else "Owned"
                vols.append(VolumeParcel(
                    key=f"b{b.bid}-f{level}", base_ulpin=base,
                    category="floor", level_no=level, unit_no=None,
                    zmin=z0, zmax=z1, ring=list(b.footprint),
                    usage="commercial_retail" if b.commercial else "residential",
                    owner=owner, right_type=right, building_id=b.bid,
                ))

        # basements for high-rises
        if b.parcel_type == "suite":
            # U-1 (whole level) + U-2 parking slots
            soc = f"{b.name} Society"
            vols.append(VolumeParcel(
                key=f"b{b.bid}-u1", base_ulpin=base, category="underground",
                level_no=-1, unit_no=None, zmin=-3.6, zmax=-0.2,
                ring=list(b.footprint), usage="car_parking",
                owner="Municipal Corporation", right_type="Leased",
                building_id=b.bid,
            ))
            slots = _subdivide(list(b.footprint), 2, 3)
            for idx, ring in enumerate(slots):
                pno = f"P{idx + 1:02d}"
                vols.append(VolumeParcel(
                    key=f"b{b.bid}-u2-{pno}", base_ulpin=base, category="parking",
                    level_no=-2, unit_no=pno, zmin=-7.0, zmax=-3.7,
                    ring=ring, usage="parking_slot", owner=soc,
                    right_type="Leased", building_id=b.bid,
                ))
            # air rights tower
            vols.append(VolumeParcel(
                key=f"b{b.bid}-air", base_ulpin=base, category="air_right",
                level_no=0, unit_no=None, zmin=b.height_m, zmax=b.height_m + 30.0,
                ring=list(b.footprint), usage="air_space_rights",
                owner="Sky Rights Corp", right_type="Air Right",
                building_id=b.bid,
            ))

    # ---- utility & metro assets ------------------------------------------
    for a in model.assets:
        base = codes.base(f"9{a.uid:05d}")
        if a.kind == "metro":
            cat, usage, right = "metro_tunnel", "transit_corridor", "Transit Easement"
        else:
            cat, usage, right = "utility_network", f"{a.kind}_duct", "Utility Easement"
        vols.append(VolumeParcel(
            key=f"a{a.uid}", base_ulpin=base, category=cat,
            level_no=0, unit_no=None, zmin=a.zmin, zmax=a.zmax,
            ring=a.ring, usage=usage, owner=a.operator, right_type=right,
            asset=a.asset_code,
        ))

    # ---- deliberate topology conflict: lift shaft breasting the tunnel ----
    if len(model.parcels) > 8 and any(a.kind == "metro" for a in model.assets):
        # find the tower whose low-y block abuts the metro corridor axis
        tower = None
        for b in model.buildings:
            if b.parcel_type == "suite" and 100 < b.footprint[0][1] < 140:
                tower = b
                break
        if tower is not None:
            base = codes.base(model.parcel_by_pid[tower.parcel_id].parcel_no)
            x0, y0 = tower.footprint[0]
            # shaft straddles the corridor margin so it intersects the tunnel
            shaft = rect(x0 + 2, y0 - 4, x0 + 12, y0 + 1)
            vols.append(VolumeParcel(
                key=f"b{tower.bid}-shaft", base_ulpin=base, category="underground",
                level_no=-3, unit_no=None, zmin=-15.0, zmax=-11.0,
                ring=shaft, usage="lift_shaft", owner=tower.name,
                right_type="Owned", building_id=tower.bid,
            ))

    return vols


def volumes_to_geojson(vols: list[VolumeParcel]) -> dict:
    from app.services.ulpin.ulpin import ULPIN3D

    feats = []
    for v in vols:
        ulpin3d = (
            ULPIN3D(
                base_ulpin=v.base_ulpin, category=v.category,
                level_no=v.level_no, unit_no=v.unit_no, asset=v.asset,
            ).value
        )
        coords = [list(pt) for pt in v.ring]
        feats.append({
            "type": "Feature",
            "properties": {
                "key": v.key,
                "ulpin3d": ulpin3d,
                "base_ulpin": v.base_ulpin,
                "category": v.category,
                "level_no": v.level_no,
                "unit_no": v.unit_no,
                "zmin": v.zmin,
                "zmax": v.zmax,
                "usage": v.usage,
                "owner": v.owner,
                "right_type": v.right_type,
                "asset": v.asset,
                "building_id": v.building_id,
            },
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        })
    return {"type": "FeatureCollection", "features": feats}


def parcels_to_geojson(model: LocalityModel) -> dict:
    feats = []
    for p in model.parcels:
        feats.append({
            "type": "Feature",
            "properties": {
                "pid": p.pid,
                "parcel_no": p.parcel_no,
                "usage": p.usage,
                "building_id": p.building_id,
            },
            "geometry": {"type": "Polygon", "coordinates": [[list(pt) for pt in p.ring]]},
        })
    return {"type": "FeatureCollection", "features": feats}


def buildings_to_geojson(model: LocalityModel) -> dict:
    feats = []
    for b in model.buildings:
        feats.append({
            "type": "Feature",
            "properties": {
                "bid": b.bid,
                "name": b.name,
                "parcel_id": b.parcel_id,
                "floor_count": b.floor_count,
                "parcel_type": b.parcel_type,
                "commercial": b.commercial,
                "roof_type": b.roof_type,
                "ground_z": b.ground_z,
                "height_m": b.height_m,
            },
            "geometry": {"type": "Polygon", "coordinates": [[list(pt) for pt in b.footprint]]},
        })
    return {"type": "FeatureCollection", "features": feats}


def utilities_to_geojson(model: LocalityModel) -> dict:
    feats = []
    for a in model.assets:
        feats.append({
            "type": "Feature",
            "properties": {
                "uid": a.uid, "kind": a.kind, "operator": a.operator,
                "zmin": a.zmin, "zmax": a.zmax, "diameter_m": a.diameter_m,
            },
            "geometry": {"type": "Polygon", "coordinates": [[list(pt) for pt in a.ring]]},
        })
    return {"type": "FeatureCollection", "features": feats}