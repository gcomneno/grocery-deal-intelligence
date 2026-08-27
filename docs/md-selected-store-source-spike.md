# MD selected-store digital flyer source spike (#86)

## Decision

`promote_to_adapter_spike`

## Objective

Evaluate MD as a deterministic retailer evidence source by selecting one concrete point of sale and checking whether the official selected-store digital flyer can be replayed with locality, validity, offer and loyalty evidence intact.

## Concrete point of sale

Official MD store evidence identifies:

- locality: `LUCCA`
- address: `STRADA PROVINCIALE ROMANA snc`

The store appears in MD-controlled point-of-sale material and in the retailer's own point-of-sale listing surface.

## Current flyer surface

MD's official flyer page states that users must select a point of sale to see the dedicated flyer:

`https://www.mdspa.it/volantino/`

At observation time (2026-08-27), the current campaign shown on that official surface was:

- valid from: `2026-08-25`
- valid to: `2026-09-06`

This proves that selected-store context is part of the product semantics of the flyer experience. It does not by itself prove how that context is transported to the dedicated flyer request.

## Structured promotion evidence

Public MD-controlled `volantino.mdspa.it` variants expose structured promotion rows containing, where applicable:

- product/package text;
- base/current price texts;
- unit/reference price;
- percentage discount;
- multi-buy mechanics such as `3x2`;
- `Prezzo Speciale` markers;
- minimum-spend conditions;
- `Buona Spesa Card` loyalty semantics.

A current publicly reachable variant observed during the spike was:

`https://volantino.mdspa.it/m_sud_atm_nogas.html`

This surface is strong evidence for promotion richness, but it is not sufficient to assert applicability to the selected Lucca store.

## Store-specific flyer capability

MD also publishes store-specific flyer PDFs where locality and promotion data coexist in the same authoritative source. Historical official examples include flyers whose text explicitly states `Solo nel punto vendita di:` followed by a concrete store identity and address.

This demonstrates that store-scoped flyer publication exists as a retailer-controlled capability. Historical examples are retained only as capability evidence and are not treated as current Lucca data.

## Retrieval result

The exact deterministic mapping:

```text
LUCCA / STRADA PROVINCIALE ROMANA snc
        ↓
selected-store identity/context token
        ↓
dedicated current flyer variant
```

was not pinned from the publicly replayable surfaces available during this spike.

The selected-store context may be transported through frontend/session state, a hidden request parameter, a store identifier, or another mechanism. No such mechanism is asserted without direct evidence.

Therefore this spike does **not** capture a Lucca fixture and does **not** claim that any generic or regional `volantino.mdspa.it` variant applies to Lucca.

## Evidence boundary

Observed and supported:

- MD requires store selection for a dedicated flyer;
- current campaign validity is explicit;
- MD has a real Lucca point of sale at Strada Provinciale Romana snc;
- MD-controlled digital flyer variants expose rich promotion and loyalty semantics;
- MD has official store-specific flyer publication capability.

Not yet supported:

- the exact current Lucca flyer URL/variant;
- a replayable selected-store identifier or request parameter for Lucca;
- a raw current Lucca store-scoped fixture;
- deterministic parser input for Lucca.

## Recommendation

`promote_to_adapter_spike`

The next spike should focus only on pinning the selected-store transport and capturing one current raw store-scoped response before any parser or production adapter is introduced.

Expected boundary:

```text
official MD store selection
        ↓
replayable store identity/context
        ↓
dedicated current flyer response
        ↓
raw fixture + SHA-256
        ↓
deterministic parser
```

## Non-goals preserved

No production scraper, adapter, AI change, canonical schema change, admission-policy change, access-control bypass, or inferred store applicability is introduced by #86.
