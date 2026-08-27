# Eurospin selected-store flyer source spike (#90)

## Decision

`promote_to_adapter_spike`

## Objective

Evaluate Eurospin as a deterministic retailer evidence source by selecting one concrete point of sale and checking whether the official store/flyer relationship can be replayed with locality, validity and promotion evidence intact.

## Concrete point of sale

Official Eurospin store evidence identifies:

- locality: `Lucca`
- address: `Via Sarzanese, 673`
- postal code: `55100`
- public store URL: `https://www.eurospin.it/punti-vendita/lucca-via-sarzanese/`

The store page is public and URL-addressable and exposes opening hours, services and departments.

## Official flyer semantics

Eurospin's official store-finder page states that, after selecting a point of sale, users can download the flyer for that store.

The official flyer page likewise asks the user to select a point of sale to discover the promotions for that selected store.

This proves that store selection is part of the flyer semantics. It does not by itself prove how the selected-store context is transported to the flyer request.

## Current promotion surface

Eurospin's official promotion surface publishes the current campaign with explicit validity and product rows:

- campaign observed: `2026-08-24` through `2026-09-06`;
- product name and brand;
- base/current price texts;
- package quantity;
- unit/reference price where applicable.

Examples observed on the official promotion page include:

- `LATTE PARZIALMENTE SCREMATO UHT` — `0,89` → `0,69 €`, `1 l`;
- `BURRO BAVARESE` — `1,85` → `1,35 €`, `250 g`, `5,40 €/kg`;
- `LINGUINE TRAFILATE AL BRONZO` — `0,85` → `0,65 €`, `500 g`, `1,30 €/kg`.

The promotion surface is therefore strong evidence for current price/promotion richness.

## Store/flyer retrieval result

The exact deterministic mapping:

```text
Lucca / Via Sarzanese 673
        ↓
selected-store identity/context
        ↓
dedicated flyer variant
```

was not pinned from the publicly replayable surfaces available during this spike.

The selected-store context may be transported through frontend state, geolocation, an internal store identifier, a request parameter, or another mechanism. No such mechanism is asserted without direct evidence.

Therefore this spike does **not** claim that the generic promotion listing is necessarily identical to the flyer applicable to Via Sarzanese 673, and it does **not** capture a Lucca-specific raw fixture yet.

## App boundary

Eurospin also documents an app experience where location is used to identify the nearest store/offers and where users can save a preferred store. This confirms that locality affects the offer experience, but app/geolocation behavior is capability evidence only and is not treated as a deterministic web retrieval recipe.

## Evidence boundary

Observed and supported:

- Eurospin has a real, public Via Sarzanese 673 store page;
- the retailer states that users select a point of sale to obtain the corresponding flyer;
- current campaign validity is explicit;
- the official promotion page exposes rich product, base/current price and unit-price data;
- locality is part of both website and app offer semantics.

Not yet supported:

- a stable store identifier for Via Sarzanese 673 beyond the public slug;
- a replayable request parameter or URL that binds Via Sarzanese 673 to one flyer variant;
- a raw current store-scoped fixture for Via Sarzanese 673;
- deterministic parser input proven to be scoped to that store.

## Recommendation

`promote_to_adapter_spike`

The next spike should focus only on pinning the selected-store transport and capturing one raw store-scoped flyer/promotion response before any parser or production adapter is introduced.

Expected boundary:

```text
official Eurospin store selection
        ↓
replayable store identity/context
        ↓
dedicated flyer/promotion response
        ↓
raw fixture + SHA-256
        ↓
deterministic parser
```

## Non-goals preserved

No production scraper, adapter, AI change, canonical schema change, admission-policy change, access-control bypass, or inferred store applicability is introduced by #90.
