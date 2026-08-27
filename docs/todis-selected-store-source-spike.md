# Todis selected-store flyer source spike (#92)

## Decision

`promote_to_adapter_spike`

## Objective

Evaluate Todis as a deterministic retailer evidence source by selecting one concrete current point of sale and checking whether the official store/flyer relationship can be replayed with locality, validity and promotion evidence intact.

## Concrete point of sale

Official Todis homepage evidence observed on 2026-08-27 identifies a current store/new-opening entry:

- locality: `Baia Domizia (CE)`
- address: `Via delle Pietre Bianche`
- store action: `Sfoglia il volantino`

The retailer-controlled homepage also exposes the generic store-selection contract:

- `Sfoglia il volantino e trova il tuo negozio Todis`
- `Cerca il punto vendita più vicino a te e scopri tutte le offerte`

This establishes that store selection is part of Todis flyer/offer semantics.

## Regional flyer capability

Todis exposes official regional flyer pages and accessible PDF variants under its own domain.

Observed official examples include regional surfaces such as:

- Lazio;
- Umbria/Toscana;
- Abruzzo/Marche/Molise;
- Puglia;
- Sicilia.

The accessible PDFs are machine-readable enough to expose structured product rows containing, depending on the campaign:

- product name and package/quantity text;
- promotion text;
- current price;
- unit/reference price;
- explicit validity intervals;
- APP-only or minimum-spend conditions;
- multi-buy or other conditional mechanics.

## Applicability boundary

Regional publication is not equivalent to store-specific applicability.

Some official flyer rows explicitly state that users must discover which points of sale adhere to an offer. Other campaigns contain store lists for subsets such as meat/fish departments.

Therefore this spike does not infer that every regional flyer row applies to Baia Domizia merely because the store lies in the same broad geographic area.

## Store/flyer retrieval result

The exact deterministic mapping:

```text
Baia Domizia / Via delle Pietre Bianche
        ↓
selected-store identity/context
        ↓
applicable flyer variant
```

was not pinned as a stable replayable URL, request parameter, embedded identifier, or equivalent transport from the public surfaces inspected during this spike.

The homepage proves that a store-specific flyer action exists, but the selected-store binding itself remains unresolved.

Accordingly, no Baia Domizia raw fixture is captured here and no regional flyer is relabeled as store-scoped evidence.

## Promotion semantics

Todis flyer evidence is semantically rich enough to justify deeper work.

Observed official accessible flyer variants expose:

- normal promotional prices;
- explicit validity dates;
- package size and unit/reference price;
- APP-only conditions;
- minimum-spend mechanics;
- multi-buy mechanics;
- store-adherence qualifiers.

These mechanics must remain evidence, not be normalized into canonical fields before the applicability scope has been proven.

## Evidence boundary

Observed and supported:

- Todis has a current retailer-controlled Baia Domizia store entry at Via delle Pietre Bianche;
- the homepage links that store entry to a flyer action;
- Todis explicitly frames flyer discovery around selecting/finding a store;
- official regional flyer surfaces exist;
- accessible flyer PDFs contain rich machine-readable product/promotion/price/validity evidence;
- some campaigns are restricted to subsets of stores or APP/condition-specific mechanics.

Not yet supported:

- a stable Todis store identifier for Baia Domizia;
- a replayable selected-store token or request parameter;
- an exact current Baia Domizia flyer URL/variant;
- a raw current store-scoped Baia Domizia fixture;
- deterministic parser input proven applicable to that store.

## Recommendation

`promote_to_adapter_spike`

The next Todis spike should focus only on pinning the selected-store transport and capturing one raw applicability-proven flyer response before any parser or production adapter is introduced.

Expected boundary:

```text
official Todis store selection
        ↓
replayable store identity/context
        ↓
applicability-proven flyer response
        ↓
raw fixture + SHA-256
        ↓
deterministic parser
```

## Non-goals preserved

No production scraper, adapter, AI change, canonical schema change, admission-policy change, access-control bypass, or inferred store applicability is introduced by #92.
