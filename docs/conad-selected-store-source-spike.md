# Conad selected-store offer source spike (#71)

## Decision

`promote_to_adapter_spike`

## Target store

Official Conad store page:

`https://www.conad.it/ricerca-negozi/conad-via-di-tiglio-420-55012-capannori--008997`

Observed store identity:

- banner: Conad
- address: Via Di Tiglio 420, 55012 Capannori (LU)
- cooperative: Conad Nord Ovest
- public store identifier in URL: `008997`
- telephone: `0583 907906`

The store page is public, unauthenticated, and directly URL-addressable.

## Store-scoped semantics

The official store page explicitly presents:

- `Volantini disponibili`;
- `In questo negozio`;
- `In offerta nel negozio`;
- a selection of products described as being in offer from the preferred store.

The public Conad store finder also documents that users select a city/address/CAP and then a point of sale to discover active offers and flyers for the selected store.

This establishes that store selection is part of Conad's public offer semantics.

## Flyer applicability evidence

Conad Nord Ovest publishes public flyer PDFs under stable-looking paths such as:

`/assets/common/volantini/cno/...`

Observed flyer documents include an explicit applicability list containing:

`CAPANNORI - Via di Tiglio 420/A - tel. 0583 907906`

The same telephone number appears on the selected-store page, linking the flyer applicability entry to the concrete public store identity without inventing locality.

The observed flyer scope is multi-store/regional rather than one-store-only. This is acceptable source evidence for applicability, but it is not yet a pinned selected-store retrieval recipe.

## Promotion evidence

Public Conad product/promotion surfaces expose structured textual rows containing product identity, package quantity, price, and validity intervals. For example, the public `Bassi e Fissi` surface exposes hundreds of rows with product names, quantities, prices and explicit validity text.

The selected-store page also exposes loyalty/promotion semantics such as Carta Insieme / Carta Insieme Più Conad Card and dated discount campaigns.

These observations show that Conad has rich canonical-relevant facts, but this spike does not claim that the generic product surface is itself scoped to store `008997`.

## Unresolved technical boundary

The key unresolved question is the exact deterministic transport from the selected-store page to the current flyer/offer payload:

```text
store page / public store id
        ↓
selected-store offer/flyer retrieval
        ↓
current raw payload
```

The public store identity is pinned, and flyer applicability is independently evidenced, but the exact request/endpoint or stable current flyer identifier used by the selected-store UI has not yet been pinned.

Therefore this spike must not manufacture a store-scoped fixture by joining a generic offer page with store metadata.

## Source assessment

| Property | Result |
| --- | --- |
| official source | strong |
| public access | yes |
| store identity | strong |
| stable-looking store id | `008997` |
| cooperative boundary | Conad Nord Ovest |
| store-specific offer semantics | explicit |
| flyer locality/applicability | explicit in public PDFs |
| product identity/quantity/price | rich on public surfaces |
| loyalty semantics | explicit |
| exact selected-store payload retrieval | unresolved |
| raw store-scoped fixture | not yet captured |

## Required next spike

Pin one deterministic retrieval chain for store `008997` (or another equally concrete Conad Nord Ovest store):

1. identify the exact flyer/offer request emitted for the selected store;
2. prove how store identity is carried in the request or response;
3. capture the raw public response/fixture;
4. record request identity, retrieval timestamp and SHA-256;
5. verify at least one offer row whose applicability is proven by the same retrieval context;
6. end with `promote_to_adapter_implementation`, `watch`, or `reject`.

## Non-goals preserved

- no production scraper;
- no access-control bypass;
- no canonical schema changes;
- no AI changes;
- no admission-policy changes;
- no assumption that regional flyer applicability equals a replayable one-store API.

## Recommendation

Conad has enough public, deterministic store identity and flyer applicability evidence to justify the next technical investment, but not enough to implement an adapter yet.

Therefore the decision is `promote_to_adapter_spike`.
