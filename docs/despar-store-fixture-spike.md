# Despar store-scoped fixture spike

## Status

Issue #77.

Recommendation: **promote_to_adapter_implementation**.

## Source

Official public flyer URL:

```text
https://www.despar.it/it/volantino-digitale/191/
```

Observed store identity from the same store/flyer identity:

```text
store_id: 191
store_name: Interspar Montebelluna
store_address: Via Schiavonesca Priula, 64
store_locality: Montebelluna (TV)
```

Observed campaign:

```text
Sconti dal 20% al 50%
valid_from: 2026-08-13
valid_to: 2026-08-26
```

The public flyer source rendered Montebelluna locality together with the store-scoped `/191/` URL and exposed real offer rows for that campaign.

## Captured fixture

Committed fixture:

```text
fixtures/despar/store-191-flyer-2026-08-13.txt
```

SHA-256:

```text
54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17
```

The fixture is a deterministic raw excerpt of observed source facts. It deliberately preserves source text rather than translating the content into the canonical grocery schema.

## Real observed offers in fixture

```text
Riso Carnaroli Scotti | 1 kg | 2,49 € al pz.
Birra Speciale Pedavena | 500 ml | 1,29 € al pz.
Olio Extra Vergine di oliva Grezzo Il Casolare Farchioni | 1 L | 9,49 € | 7,59 € al pz. | Sconto extra App -20%
```

These rows demonstrate deterministic availability of:

- product identity;
- package/quantity text;
- current price text;
- previous/base price text where present;
- explicit promotion text where present;
- campaign validity;
- store/locality scope.

## Parser contract

`grocery_deal_intelligence.despar_fixture` parses only the committed fixture representation.

It does not:

- access the network;
- infer missing values;
- decide canonical promotion semantics;
- decide loyalty requirements;
- perform canonical admission;
- invoke AI.

The parser returns immutable dataclasses and retains price/promotion strings as source evidence. `parse_euro_price()` is deliberately narrow and only converts an explicitly present euro amount to `Decimal`.

## Deterministic boundary

```text
official store-scoped Despar flyer
        ↓
raw source excerpt + SHA-256
        ↓
deterministic parser
        ↓
source evidence only
```

## Verification

Tests cover:

- fixture SHA-256 identity;
- store and campaign metadata;
- real offer parsing;
- previous/current price preservation;
- promotion-text preservation;
- source-text non-mutation;
- malformed/missing input rejection.

## Recommendation

**promote_to_adapter_implementation**

The source surface has now demonstrated all minimum properties required for a real retailer adapter implementation spike:

- publicly addressable store-scoped source;
- explicit store identity/locality;
- explicit campaign validity;
- reproducible real offer evidence;
- deterministic parsing without AI;
- no need to synthesize provenance from separate browsing context.

A production adapter remains a separate issue and must decide retrieval cadence, raw-response preservation, failure behavior, field mapping, and canonical admission independently.
