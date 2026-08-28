# MD selected-store transport spike (#109)

## Verdict

`watch`

## Objective

This spike followed #86 and tested the remaining MD promotion gate: whether the official selected-store flow for one concrete point of sale can be reduced to a deterministic, replayable request/response chain that proves applicability of an exact current digital flyer payload to that store.

Target point of sale:

```text
retailer: MD
store id: 1015
locality: LUCCA (LU)
address: STRADA PROVINCIALE ROMANA snc
```

## New deterministic evidence

The spike established a material improvement over #86: MD exposes a public, replayable selected-store identifier in an official URL:

```text
https://www.mdspa.it/sfogliatore/?id_pv=1015
```

That URL resolves to an MD-controlled page which explicitly renders:

```text
LUCCA (LU) - STRADA PROVINCIALE ROMANA snc
```

The same store is also publicly addressable through the retailer-controlled store URL:

```text
https://www.mdspa.it/punti-vendita/Toscana/LU-Lucca/1015-LUCCA/
```

This means the selected point of sale no longer depends only on an opaque frontend/session choice: `1015` is a concrete public store identifier and the store context can be replayed from a fresh URL.

## Store-page flyer semantics

The official Lucca store page exposes an `Offerte in corso` section with the actions:

- `SFOGLIA ONLINE`;
- `Scarica volantino`.

This proves that the concrete store page is connected by MD's own application semantics to current flyer content.

MD's general official flyer page also continues to state that users must select a point of sale to see the dedicated flyer.

## Digital flyer richness

MD-controlled `volantino.mdspa.it` variants remain publicly reachable and expose deterministic promotion evidence including, depending on the row:

- product/package text;
- base/current price;
- unit/reference price;
- percentage discount;
- multi-buy mechanics such as `3x2`;
- `Prezzo Speciale`;
- minimum-spend conditions;
- `Buona Spesa Card` semantics.

Current publicly reachable examples include variants such as:

```text
https://volantino.mdspa.it/m_sud_atm_nogas.html
https://volantino.mdspa.it/m_sud_atm_gas.html
https://volantino.mdspa.it/m_nord_atm_gas.html
```

These prove source richness, not Lucca applicability.

## Remaining transport gap

The key gate for `promote_to_adapter_implementation` is stricter than proving a public store id.

The required chain is:

```text
store id 1015
        ↓
exact public flyer transport for store 1015
        ↓
concrete current volantino.mdspa.it variant or raw flyer payload
        ↓
offer rows whose applicability is proven by that same chain
```

During this spike, the first step was pinned but the second was not.

The publicly observable/crawlable representation of the Lucca store page confirms `SFOGLIA ONLINE` and flyer-download semantics, but it does not expose a stable target URL, query parameter, response field, or raw payload that deterministically identifies which current `volantino.mdspa.it` variant is selected for `id_pv=1015`.

Searches for a direct public association between store id `1015` / the Lucca store URL and a specific current digital-flyer variant did not produce a reproducible retailer-controlled mapping.

Therefore no generic `m_nord_*`, `m_sud_*`, gas/nogas, ATM, meat/fish, or other flyer variant is assigned to Lucca by inference.

## Why no fixture/parser was created

A synthetic fixture could be made by combining:

1. the replayable Lucca store identity (`id_pv=1015`); and
2. one rich public `volantino.mdspa.it` variant.

That would still fail the GDI evidence rule because the same source chain would not prove that the chosen variant applies to store `1015`.

Accordingly this spike does not:

- capture a purported Lucca offer fixture;
- add an MD parser;
- add an MD adapter;
- infer north/south, gas/nogas, ATM, meat/fish, or campaign-variant membership from geography or naming.

Canonical boundary preserved:

```text
public store id != exact flyer applicability
rich flyer variant != selected-store evidence
```

## Decision against the #109 gate

### `promote_to_adapter_implementation`

Not yet satisfied.

MD now has a pinned replayable public store identifier, but the exact store-id → current flyer-variant transport remains unpinned. Without that final mapping, a raw Lucca-scoped fixture cannot be captured without inference.

### `reject`

Not justified.

MD is a strong source candidate because:

- the public store id is now pinned (`1015`);
- the store page is directly replayable;
- current flyer semantics are explicitly attached to that store page;
- official digital flyer variants expose rich deterministic promotion/loyalty evidence;
- no access-control bypass is necessary to observe these surfaces.

The remaining blocker is narrow: exposing or reproducing the exact flyer-target mapping used by the store page.

## Final verdict

`watch`

This is a stronger `watch` than the state recorded by #86: the selected-store identity transport has been pinned, but the final flyer-variant transport has not.

A future promotion to `promote_to_adapter_implementation` should require one new piece of evidence:

```text
id_pv=1015
        ↓
public reproducible current flyer target
        ↓
raw Lucca-applicable fixture + SHA-256
        ↓
deterministic parser
```

Once that exact target becomes directly observable, MD should be re-evaluated immediately because the remaining source facts are already rich enough for adapter work.

## Non-goals preserved

This spike introduces no production scraper, adapter, parser, canonical schema change, AI change, admission-policy change, inferred locality, loyalty harvesting, personalized-offer harvesting, or access-control bypass.
