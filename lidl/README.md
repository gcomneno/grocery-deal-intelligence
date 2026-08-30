# Lidl Grocery Deal Adapter — Experimental

Experimental adapter for Grocery Deal Intelligence.

## Goal

Produce normalized, locality-aware, verifiable grocery offer records
from official Lidl sources.

## Reference locality

Lucca, Tuscany.

Observed Lidl stores:

- `IT01621` — Via di Tiglio 305
- `IT00302` — Viale Puccini 1561

Both currently resolve to:

- offer region: `600`
- offer region name: `Pontedera - Toscana`
- zone: `IT1`

## Data flow

```text
official campaign pages
        ↓
structured product extraction
        ↓
food classification
        ↓
price normalization
        ↓
store / offer-region resolution
        ↓
regional leaflet verification
        ↓
normalized dataset
```

## Authority boundaries

Campaign HTML is used for:

- product name
- price
- packaging
- promotion metadata
- validity

Store payload is used for:

- store identity
- coordinates
- offer region

Leaflet overview is used for:

- local flyer applicability
- flyer validity
- store coverage

Flyer JSON is used for:

- secondary product evidence
- page-level verification

No single Lidl source is treated as authoritative for every semantic field.

## Offer identity

A product name is not an offer identifier.

The same named product may legitimately appear in multiple concurrent offers.

Example observed during the experiment:

```text
Birra
├── 1.99 EUR — Lidl Plus campaign
└── 1.77 EUR — XXL standard campaign
```

Therefore:

```text
same product name
≠
same offer
```

Offer identity must preserve, at minimum:

- retailer
- product identity
- price
- promotion semantics
- validity
- campaign provenance

Records must not be deduplicated by product name alone.

## Verification semantics

The adapter distinguishes:

- `locality = verified`
- `flyer_match = exact`
- `flyer_match = unmatched`

`unmatched` does not mean invalid.

It only means that the strict deterministic flyer-text matcher did not
find the complete normalized product name in the flyer page evidence.

## Current observed output

Latest experimental build:

- 58 offer records
- 57 unique product names
- 26 exact flyer matches
- 32 unmatched flyer-text records
- 0 FOOD products lost by the builder
- 0 FOOD products without an extractable price variant

The difference between 58 records and 57 unique product names is intentional:
one product name currently has two distinct valid offers.

## Status

The acquisition and dataset-building tooling remains experimental.

One exact committed source-shaped dataset is now also a pinned deterministic
repository acceptance fixture:

`lidl/data/output/lidl-lucca-current.json`

Pinned full-file SHA-256:

`a74d6ffa880b46513f90cbe22b1dccd3a99a21ed80f84680808ea4cb363500df`

That fixture is admitted through the first-class deterministic evidence,
verification, structural-validation, canonical-admission, `IngestionResultSet`,
and corpus-assembly path.

This does not promote the historical retailer-neutral export to canonical
authority and does not make Lidl acquisition/build tooling production-ready.

Not a public data redistribution service.
