# Deterministic Despar retailer adapter

## Status

Implementation for #102.

## Boundary

```text
captured store-scoped Despar fixture + expected SHA-256
        ↓
adapt_despar_fixture_text(...)
        ↓
retailer source records
        ↓
project_source_evidence(..., retailer="despar")
        ↓
deterministic verification / validation / admission layers
```

The adapter verifies the committed fixture identity before parsing and reuses `despar_fixture.py`; it does not duplicate parsing rules.

## Facts mapped

The adapter maps only source-supported facts:

- retailer identity (`despar`);
- product name;
- current price;
- explicit previous/base price text when present;
- euro currency from the explicit source price notation;
- package text;
- explicit promotion/discount text when present;
- campaign validity;
- store id, name, address and locality from the same captured source chain;
- source URL;
- caller-supplied observation timestamp;
- verified fixture SHA-256 and campaign title.

The previous/base price is deliberately preserved as `base_price_text`. It is **not** reclassified as canonical `reference_price`, because the captured fixture does not establish a unit/reference-price semantic.

## Deliberately not inferred

The captured fixture does not prove all canonical promotion semantics. In particular, absence of a loyalty marker is not proof of `requires_loyalty = false`, and `Sconto extra App -20%` does not by itself justify treating app usage as a canonical loyalty-card requirement.

Therefore the adapter does not invent:

- `promotion.type`;
- `promotion.requires_loyalty`;
- unit/reference price;
- missing prices;
- missing identifiers;
- locality outside the captured store context.

A candidate built only from current Despar evidence can therefore be fully supported by deterministic claim verification while still failing canonical structural validation because required promotion semantics are absent. That failure is intentional and preserves the authority boundary.

## Failure behavior

- wrong fixture SHA-256: reject before mapping;
- malformed fixture: reject through the existing deterministic parser;
- missing observation timestamp: reject;
- unsupported canonical facts: omit rather than complete.

No AI, network dependency, production scraper, schema weakening, admission-policy weakening or inferred locality is introduced by this adapter.
