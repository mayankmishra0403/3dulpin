"""3D ULPIN core: deterministic generation, parsing and validation.

Standard
--------
Base 2D ULPIN (14 chars, mirrors the national DoLR ULPIN convention)::

    SS DD SS VV PPPPPP
    ── ── ── ── ──────
    │  │  │  │   └─ parcel serial (6 digits, unique within locality)
    │  │  │  └─ village / locality code (2)
    │  │  └─ sub-district (tehsil) code (2)
    │  └─ district code (2)
    └─ state / UT code (2)

3D ULPIN = `<base14>` + `-` + `<vertical>[.<unit>]` + <checksum>

Vertical identity field encodes the volume:

=====  =============================================================
field  meaning
=====  =============================================================
0      surface / ground parcel
Fnn    floor nn for storey nn (nn >= 01)
U nn   below-ground level nn (level_no = -nn); U1 = first basement
AR     air-rights volume
NDxx   utility network corridor (x = asset code, documented)
MTxx   metro / transit tunnel segment
S      structural element
=====  =============================================================

A suite inside a storey appends `.unit`, e.g. ``…-F03.2B``.
The final checksum character (base36) is derived from the whole code
front so any typo / tampering is detected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SEP = "-"
DOT = "."

# Category keyword -> vertical field mapping
CATEGORY_FIELD: dict[str, str] = {
    "surface": "0",
    "floor": "F",
    "suite": "F",          # suite = floor field + "." + unit
    "underground": "U",
    "parking": "U",        # parking = underground/stack field + "." + slot
    "air_right": "AR",
    "utility_network": "ND",
    "metro_tunnel": "MT",
    "structure": "S",
}

# Unit/asset codes for network corridors (documented extension)
UTILITY_ASSET: dict[str, str] = {
    "water": "01", "sewage": "02", "electric": "03",
    "telecom": "04", "storm": "05", "gas": "06",
}


def _char_value(c: str) -> int:
    return ALPHABET.index(c)


def checksum(front: str) -> str:
    """Base36 checksum over `front` — appends one char for validation.

    Positional separators (the `-`) are skipped; only alphabet characters
    contribute. This keeps the code human-readable while staying tamper-evident.
    """
    alpha_chars = [c for c in front if c in ALPHABET]
    if not alpha_chars:
        raise ValueError("ULPIN front contains no checksumable characters")
    total = sum((i + 1) * _char_value(c) for i, c in enumerate(alpha_chars))
    return ALPHABET[total % 36]


@dataclass
class ULPIN3D:
    base_ulpin: str
    category: str
    level_no: int = 0          # >=1 above ground, <=-1 below ground, 0 surface
    unit_no: Optional[str] = None
    asset: Optional[str] = None  # for utility_network / metro_tunnel

    # ---- construction -------------------------------------------------
    @classmethod
    def for_floor(cls, base: str, floor_no: int) -> "ULPIN3D":
        if floor_no < 1:
            raise ValueError("floor_no must be >= 1 (use 0 for surface, negative for underground)")
        return cls(base_ulpin=base, category="floor", level_no=floor_no)

    @classmethod
    def for_suite(cls, base: str, floor_no: int, unit: str) -> "ULPIN3D":
        if floor_no < 1:
            raise ValueError("suite floor must be >= 1")
        return cls(base_ulpin=base, category="suite", level_no=floor_no, unit_no=unit)

    @classmethod
    def for_underground(cls, base: str, level: int) -> "ULPIN3D":
        if level >= 0:
            raise ValueError("underground level must be negative, e.g. -1")
        return cls(base_ulpin=base, category="underground", level_no=level)

    @classmethod
    def for_parking(cls, base: str, level: int, slot: str) -> "ULPIN3D":
        if level >= 0:
            raise ValueError("parking level must be negative")
        return cls(base_ulpin=base, category="parking", level_no=level, unit_no=slot)

    @classmethod
    def for_surface(cls, base: str) -> "ULPIN3D":
        return cls(base_ulpin=base, category="surface", level_no=0)

    @classmethod
    def for_air_right(cls, base: str) -> "ULPIN3D":
        return cls(base_ulpin=base, category="air_right", level_no=0)

    @classmethod
    def for_utility(cls, base: str, asset: str) -> "ULPIN3D":
        return cls(base_ulpin=base, category="utility_network", level_no=0, asset=asset)

    @classmethod
    def for_metro(cls, base: str, segment: str) -> "ULPIN3D":
        return cls(base_ulpin=base, category="metro_tunnel", level_no=0, asset=segment)

    # ---- serialisation ------------------------------------------------
    @property
    def vertical(self) -> str:
        cat = self.category
        if cat in ("surface", "air_right"):
            return CATEGORY_FIELD[cat]
        if cat == "floor":
            return f"F{self.level_no:02d}"
        if cat == "suite":
            if self.unit_no is None:
                raise ValueError("suite requires unit_no")
            return f"F{self.level_no:02d}{DOT}{self.unit_no}"
        if cat in ("underground", "parking"):
            field = f"U{-self.level_no}"
            if cat == "parking":
                if self.unit_no is None:
                    raise ValueError("parking requires slot/unit_no")
                field += f"{DOT}{self.unit_no}"
            return field
        if cat == "utility_network":
            if self.asset is None or any(c not in ALPHABET for c in self.asset):
                raise ValueError("utility requires a valid asset code")
            return f"ND{self.asset}"
        if cat == "metro_tunnel":
            if self.asset is None or any(c not in ALPHABET for c in self.asset):
                raise ValueError("metro requires a segment code")
            return f"MT{self.asset}"
        if cat == "structure":
            return "S"
        raise ValueError(f"unsupported category {cat!r}")

    @property
    def front(self) -> str:
        return f"{self.base_ulpin}{SEP}{self.vertical}"

    @property
    def value(self) -> str:
        return self.front + checksum(self.front)

    def __str__(self) -> str:
        return self.value

    # ---- parsing ------------------------------------------------------
    @staticmethod
    def parse(code: str) -> "ULPIN3D":
        code = code.strip().upper()
        if SEP not in code:
            raise ValueError("not a 3D ULPIN (missing separator)")
        base, _, rest = code.partition(SEP)
        if len(base) != 14:
            raise ValueError(f"base ULPIN must be 14 chars, got {len(base)}")
        expect_ck = checksum(f"{base}{SEP}{rest[:-1]}")
        if expect_ck != rest[-1]:
            raise ValueError("checksum mismatch — invalid or tampered 3D ULPIN")
        body = rest[:-1]
        return ULPIN3D.parse_body(base, body)

    @staticmethod
    def parse_body(base: str, body: str) -> "ULPIN3D":
        if body == "0":
            return ULPIN3D(base_ulpin=base, category="surface", level_no=0)
        if body == "AR":
            return ULPIN3D(base_ulpin=base, category="air_right", level_no=0)
        if body == "S":
            return ULPIN3D(base_ulpin=base, category="structure", level_no=0)
        if body.startswith("F"):
            floor_part, _, unit = body[1:].partition(DOT)
            level = int(floor_part)
            if unit:
                return ULPIN3D(base_ulpin=base, category="suite", level_no=level, unit_no=unit)
            return ULPIN3D(base_ulpin=base, category="floor", level_no=level)
        if body.startswith("U"):
            level_part, _, slot = body[1:].partition(DOT)
            level = -int(level_part)
            if slot:
                return ULPIN3D(base_ulpin=base, category="parking", level_no=level, unit_no=slot)
            return ULPIN3D(base_ulpin=base, category="underground", level_no=level)
        if body.startswith("ND"):
            return ULPIN3D(base_ulpin=base, category="utility_network", level_no=0, asset=body[2:])
        if body.startswith("MT"):
            return ULPIN3D(base_ulpin=base, category="metro_tunnel", level_no=0, asset=body[2:])
        raise ValueError(f"unknown vertical field {body!r}")


# ---------------------------------------------------------------------
# Base 2D ULPIN helpers
# ---------------------------------------------------------------------

def make_base_ulpin(
    parcel_no: str | int,
    state_code: str,
    district_code: str,
    sub_district_code: str,
    village_code: str,
) -> str:
    """Compose a 14-char base ULPIN. parcel_no is zero-padded to 6 digits."""
    p = str(parcel_no).zfill(6)
    if len(p) > 6 or not p.isdigit():
        raise ValueError("parcel_no must be <= 6 digits")
    return f"{state_code}{district_code}{sub_district_code}{village_code}{p}"


def parse_base_ulpin(ulpin: str) -> dict:
    ulpin = ulpin.strip().upper()
    if len(ulpin) != 14 or not ulpin.isalnum():
        raise ValueError("base ULPIN must be 14 alphanumeric chars")
    return {
        "state_code": ulpin[0:2],
        "district_code": ulpin[2:4],
        "sub_district_code": ulpin[4:6],
        "village_code": ulpin[6:8],
        "parcel_no": ulpin[8:14],
        "value": ulpin,
    }


def is_valid_base(ulpin: str) -> bool:
    try:
        parse_base_ulpin(ulpin)
        return True
    except ValueError:
        return False


@dataclass
class LocalityCodes:
    """DoLR-style administrative codes for the demo locality."""
    state_code: str
    district_code: str
    sub_district_code: str
    village_code: str

    def base(self, parcel_no: int | str) -> str:
        return make_base_ulpin(
            parcel_no, self.state_code, self.district_code,
            self.sub_district_code, self.village_code,
        )


def demo_locality() -> LocalityCodes:
    """Default demo locality — Gurugram, Haryana (see .env)."""
    from app.config import settings

    return LocalityCodes(
        state_code=settings.demo_state_code,
        district_code=settings.demo_district_code,
        sub_district_code=settings.demo_sub_district_code,
        village_code=settings.demo_village_code,
    )