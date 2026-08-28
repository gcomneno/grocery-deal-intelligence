# Deterministic Carrefour retailer adapter

## Status

Implementation for #104.

## Boundary

```text
captured store-scoped Carrefour fixture + expected SHA-256
        ↓
adapt_carrefour_fixture_text(...)
        ↓
retailer source records
        ↓
project_source_evidence(..., retailer="carrefour")
        ↓
deterministic verification / validation / admission
```

The adapter verifies fixture identity before parsing and reuses `carrefour_fixture.py`; it does not duplicate fixture parsing rules.

## Facts mapped

The captured Carrefour fixture distinguishes three price roles in source order:

```text
base price | current promotional price | unit/reference price
```

The adapter therefore maps:

- product name;
- current promotional price;
- previous/base price as `base_price_text`;
- unit/reference price as canonical `reference_price`;
- EUR currency from explicit euro notation;
- explicit discount text;
- explicit `SPESAMICA PAYBACK` loyalty marker;
- `requires_loyalty = true` only when that positive marker exists;
- campaign validity;
- store id/name/address/locality;
- flyer id;
- source URL;
- caller-supplied observation timestamp;
- verified fixture SHA-256 and campaign title.

## Promotion semantics

The adapter does not invent a cross-retailer promotion taxonomy. When the fixture explicitly contains `SPESAMICA PAYBACK`, that exact source wording is preserved as `promotion_type` and the positive loyalty requirement is mapped as `requires_loyalty = true`.

Absence of a loyalty marker is not converted to `requires_loyalty = false`.

## Price semantics

Unlike the Despar fixture, Carrefour provides an explicit unit/reference-price row. Therefore `reference_price` is justified here.

The previous/base price remains text evidence (`base_price_text`) and is not conflated with the unit/reference price.

## Failure behavior

- wrong fixture SHA-256: reject before mapping;
- malformed fixture: reject through the existing parser;
- missing observation timestamp: reject;
- fewer than two price values: reject because current-price role is not deterministically distinguishable;
- unsupported promotion/locality semantics: omit rather than manufacture.

## Admission

For the captured PAYBACK rows, the fixture contains enough explicit evidence to build a structurally valid canonical candidate whose critical claims are all deterministically supported. The test suite verifies that this candidate passes the existing admission policy without weakening validation or admission rules.

No AI, network dependency, production scraper, schema weakening, admission-policy weakening or inferred locality is introduced.
