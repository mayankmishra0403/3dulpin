# 3D ULPIN Specification

A 3D ULPIN identifies a vertical property part unambiguously. It is composed of a **14-character
base ULPIN** (DoLR-style cadastral code + parcel), a **vertical descriptor**, and a single
base-36 **checksum** character.

## Structure

```
LLLLLLLLLLLLLL - VVVVVV C
└─ base (14)  ─┘ └vert┘ └─
```

| Piece | Length | Contents |
| --- | --- | --- |
| Base ULPIN | 14 | `06080704` (state 06 · district 08 · sub-district 07 · village 04) + 6-digit parcel no. Demo assets use `9xxxxx` |
| Vertical field | variable, `-` separated | descriptor below (no `-` inside → checksum never ambiguous) |
| Checksum | 1 | base36 of the vertical field (Luhn-like weighted sum, skips `-`) |

## Vertical descriptors

| Kind | Format | Example |
| --- | --- | --- |
| Surface parcel | `0` | `06080704000021-0` |
| Floor | `Fnn` | `06080704000021-F03` |
| Suite on a floor | `Fnn.UNIT` | `06080704000021-F03.U11` |
| Underground level | `Un` | `06080704000021-U38` (e.g. depth index 38) |
| Parking slot | `Un.SLOT` | `06080704000001-U2.P01E` |
| Air right | `AR` | `06080704000021-ARK` |
| Utility network segment | `NDxx` | `06080704900002-ND016` |
| Metro segment | `MTxx` | `06080704900001-MTA17` |
| Structure / lintel member | `S` | (reserved; not seeded) |

## Checksum
- Alphabet: `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ` (base36).
- Computed over the vertical field **with `-` excluded** so that the separator never influences it.
- `checksum_ok` is returned by `/api/ulpins/parse/{code}` and `/api/ulpins/generate`.

## Service API
- `GET /api/ulpins/parse/{code}` → decodes base, `category`, `level_no`, `unit_no`, `front`,
  `checksum_ok`, plus cadastral fields (state/district/sub-district/village/parcel). Invalid codes return **400**.
- `POST /api/ulpins/generate` body `{ base_ulpin, category, level_no?, unit_no?, asset? }` → composed value.
- `GET /api/ulpins/base/{parcel_no}` → 14-char base ULPIN for the demo locality.

Examples from the seeded database:

- `06080704000021-U38` — lift-shaft underground parcel (z −15…−11 m) that conflicts with metro
- `06080704900001-MTA17` — metro tunnel segment (z −17…−12 m)
- `06080704000002-F01S` — first floor of a residential walk-up
- `06080704000001-F01.AE` — suite **A** on floor 1 of tower `06080704000001`
- `06080704000001-U2.P01E` — parking slot **P01** on underground level −2 of the same tower