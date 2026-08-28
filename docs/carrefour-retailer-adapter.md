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
base/original displayed price | current promotional price | unit price
```

The adapter therefore maps:

- product name;
- current promotional price;
- previous/base price as raw `base_price_text`;
- the same previous/base price, parsed numerically, as canonical `reference_price`;
- unit price preserved only in the raw fixture/parser evidence;
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

Carrefour explicitly distinguishes the displayed base/original price from the current promotional price and the unit price.

Canonical `price` is the current promotional price. Canonical `reference_price` is the numeric form of the displayed base/original comparison price. `base_price_text` preserves that same source value as raw text.

The separate unit-price row (for example `€2,10 al Kg` or `€2,52 al Lt`) is not a canonical `reference_price`. It remains available in the raw fixture/parser evidence until a deliberate retailer-neutral unit-price contract is introduced.

## Failure behavior

- wrong fixture SHA-256: reject before mapping;
- malformed fixture: reject through the existing parser;
- missing observation timestamp: reject;
- fewer than two price values: reject because current-price role is not deterministically distinguishable;
- unsupported promotion/locality semantics: omit rather than manufacture.

## Admission

For the captured PAYBACK rows, the fixture contains enough explicit evidence to build a structurally valid canonical candidate whose critical claims are all deterministically supported. The test suite verifies that this candidate passes the existing admission policy without weakening validation or admission rules.

No AI, network dependency, production scraper, schema weakening, admission-policy weakening or inferred locality is introduced.
