# Deterministic Despar retailer adapter

## Status

Implementation for #102, aligned with the canonical promotion-claim contract from #148.

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

The previous/base price is deliberately preserved as `base_price_text`. It is **not** reclassified as canonical `reference_price`, because the captured fixture does not establish that text as an ordinary/original numeric comparison price.

## Promotion claims remain evidence-only

The captured fixture does not prove universal promotion semantics. In particular, absence of a loyalty marker is not proof of `requires_loyalty = false`, and `Sconto extra App -20%` does not by itself justify a stronger canonical promotion taxonomy.

Therefore the adapter does not invent:

- `promotion.type`;
- `promotion.requires_loyalty`;
- unsupported reference or unit prices;
- missing prices;
- missing identifiers;
- locality outside the captured store context.

Under Grocery Offer v0.1, `promotion` is an optional claim group. Its absence means only that no canonical promotion claim is asserted. It does not mean that the offer is known to be non-promotional.

For the committed fixture this means:

- Riso Carnaroli Scotti: canonical promotion omitted;
- Birra Speciale Pedavena: canonical promotion omitted;
- Olio Extra Vergine: canonical promotion contains only the supported `discount_text` claim.

A non-empty promotion object may contain independently supported `type`, `requires_loyalty`, and/or `discount_text` claims. No missing leaf is defaulted.

## Admission consequence

The three committed Despar records now satisfy canonical structural completeness using only their existing supported evidence. Their admission does not come from adapter repair or schema defaults; it comes from removing the obsolete requirement that every canonical shopper offer assert promotion and loyalty facts.

Claim verification remains unchanged. Every canonical leaf that is present must still match projected source evidence exactly.

## Failure behavior

- wrong fixture SHA-256: reject before mapping;
- malformed fixture: reject through the existing deterministic parser;
- missing observation timestamp: reject;
- unsupported canonical facts: omit rather than complete.

No AI, network dependency, production scraper, inferred loyalty status, source repair, or retailer-specific canonical exception is introduced by this adapter.
