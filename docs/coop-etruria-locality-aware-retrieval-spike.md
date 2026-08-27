# Coop Etruria locality-aware retrieval spike (#80)

## Decision

`watch`

## Objective

Determine whether Coop a Casa / Unicoop Etruria promotions can be retrieved through a deterministic, replayable locality-aware request rather than through unscoped public catalogue HTML.

## Established public facts

The public commerce surface is explicitly operated by Unicoop Etruria SC and supports two locality-bearing service modes:

- `Consegna a Casa`, where the servicing Coop store is selected from the delivery address/CAP;
- `Ritiro in negozio`, where the user selects a specific Coop point of sale.

The published conditions of sale state that the selected point of sale governs the products available for both modes. The rendered catalogue also warns that changing delivery address can make products unavailable and remove them from the cart.

Therefore locality/applicability is real application state and must not be inferred from an unscoped `/promo` or category page.

## Demandware evidence

The rendered catalogue exposes Salesforce Commerce Cloud / Demandware-style request surfaces, including URLs of the form:

```text
/on/demandware.store/Sites-CoopTi-Site/it_IT/Search-Refinebar
```

with deterministic catalogue/query parameters such as:

```text
cgid=...
prefn1=excludeForDelivery
prefv1=false
```

This proves a structured commerce backend and deterministic catalogue request shape, but it does **not** prove locality transport.

## Locality transport investigation

The publicly observable pages expose UI flows for:

```text
Consegna a Casa
  -> CAP
  -> indirizzo
  -> numero civico

Ritiro in negozio
  -> selected Coop store
```

and explicitly state that changing delivery address can change product availability.

However, in the replayable public request surfaces inspected during this spike, the selected delivery/pickup context is not encoded in a stable URL/query parameter that can be independently replayed and verified.

No public evidence was found that would justify treating any of the following as a proven locality identifier:

- the bare `/promo` URL;
- `cgid` catalogue parameters;
- `excludeForDelivery=false`;
- product IDs;
- the cooperative identity alone.

The locality binding therefore appears to depend on state established by the delivery/pickup selection flow, plausibly cookies/session/server-side state. That state was not independently replayed and verified in a deterministic request during this spike.

## Why no raw locality-scoped fixture was committed

#80 requires the same retrieval context to prove applicability.

Capturing a rich public `/promo` or category response and pairing it with a delivery address or store observed elsewhere would create false provenance:

```text
unscoped catalogue response
+
separate locality selection
!=
proven locality-scoped dataset
```

No locality-scoped raw fixture is therefore committed.

## What remains usable

The #69 source findings remain valid for **unscoped source evidence**:

- product identity;
- package quantity;
- current/promotional price;
- previous/base price;
- unit/reference price;
- percentage discount;
- promotion validity text;
- loyalty semantics such as socio/non-socio pricing;
- stable-looking numeric product IDs;
- Demandware commerce-backend provenance.

These facts must not be promoted to store/locality applicability without a replayable context-bound retrieval.

## Recommendation

`watch`

Coop Etruria remains a strong source candidate, but adapter implementation should wait until one of these can be demonstrated:

1. a stable public store/pickup identifier in the retrieval request;
2. a deterministic delivery-context token that can be established and replayed safely;
3. a public endpoint whose response itself carries the selected locality/store identity;
4. another official locality-scoped surface with equivalent promotion detail.

## Architectural invariant

```text
rich promotion data
        +
real locality semantics
        -
replayable locality transport
        =
WATCH, not adapter implementation
```

The canonical validator, Proposal path and admission policy are unchanged by this spike.
