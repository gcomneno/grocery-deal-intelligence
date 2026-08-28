# Conad selected-store transport spike (#107)

## Verdict

`watch`

## Objective

This spike followed #71 and tested the remaining Conad promotion gate: whether one public selected-store context can be reduced to a deterministic, replayable request/response chain that proves applicability of an exact flyer or offer payload to that store.

The target remained:

```text
retailer: Conad
store id: 008997
store: Conad
address: Via Di Tiglio 420, 55012 Capannori (LU)
cooperative: Conad Nord Ovest
telephone: 0583 907906
```

## Store-scoped semantics remain strong

The official public store page for the target point of sale exposes all of the following in the same retailer-controlled page:

- `Volantini disponibili`;
- `In questo negozio`;
- `In offerta nel negozio`;
- `Una selezione di prodotti in offerta dal tuo negozio preferito`;
- the store address and telephone number;
- `Cooperativa Conad Nord Ovest`.

The public store URL itself contains the stable-looking store suffix `008997`.

This confirms that store selection is a real Conad offer semantic. It does **not** by itself establish the transport used to obtain the current offer payload.

## Independent flyer applicability evidence

Official Conad Nord Ovest flyer PDFs continue to expose explicit point-of-sale applicability lists. Observed documents include:

```text
CAPANNORI - Via di Tiglio 420/A - tel. 0583 907906
```

The telephone number matches the public target-store page. This remains valid deterministic evidence that those flyer documents apply to the concrete Capannori point of sale.

This evidence is useful, but it does not reveal a selected-store request contract. The PDF is a multi-store/cooperative flyer with its own applicability list.

## Transport investigation

The store page exposes a `Scopri tutte le offerte` action under the store-scoped section. During this spike, the public destination observable from that action resolved to the general Conad `Bassi e Fissi` product surface rather than to a store-bound payload carrying `008997` or another explicit target-store identifier.

The general product surface exposes rich deterministic facts such as:

- product identity;
- package/quantity in product titles;
- price;
- validity intervals.

However, the observed public representation does not prove those rows to be applicable specifically to store `008997`.

No public, replayable selected-store retrieval contract was pinned during this spike in the form of a stable:

- request path;
- query parameter;
- request body field;
- embedded flyer identifier tied to the store;
- store-bound JSON response;
- cookie-independent/session-independent transport.

The public store page demonstrates that the UI has store-aware semantics, but the underlying current-offer transport remains opaque from the reproducible public evidence captured here.

## Why no fixture was manufactured

A fixture could be assembled by combining:

1. the Capannori store page;
2. a generic Conad product/offers page; or
3. a cooperative flyer PDF whose applicability list includes Capannori.

That would violate the GDI evidence boundary if presented as one selected-store offer payload.

Therefore this spike deliberately does **not** create a synthetic store-scoped offer fixture and does not introduce a parser.

Canonical rule preserved:

```text
visible offer != store applicability
selected store elsewhere != provenance for a global offer
```

## Decision against the #107 gate

### `promote_to_adapter_implementation`

Not satisfied.

The source still lacks a pinned replayable transport whose same evidence chain binds store identity to the exact offer/flyer payload consumed by an adapter.

### `reject`

Not justified.

Conad remains a valuable source:

- public store identity is strong;
- selected-store offer semantics are explicit;
- official flyer applicability can be proven;
- product, price, validity and loyalty data are rich;
- no access-control bypass is required to observe those surfaces.

The remaining problem is transport reproducibility, not absence of useful evidence.

## Final verdict

`watch`

Conad should remain on watch until one of the following becomes deterministically observable:

```text
store id/context
        ↓
public replayable retrieval contract
        ↓
exact applicable flyer/offer payload
        ↓
raw fixture + SHA-256
        ↓
deterministic parser
```

A future promotion to `promote_to_adapter_implementation` must be triggered by new transport evidence, not by richer generic offer pages or by manually joining separate locality and offer observations.

## Non-goals preserved

This spike introduces no production scraper, adapter, parser, schema change, AI change, admission-policy change, personalized-offer harvesting, loyalty harvesting, inferred locality or access-control bypass.
