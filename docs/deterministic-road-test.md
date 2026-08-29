# Deterministic multi-retailer road test

## Purpose

The road test exercises the real deterministic ingestion/evidence/admission path over committed retailer fixtures that were captured from official store-scoped sources.

Run it from the repository root:

```bash
python -m grocery_deal_intelligence.road_test
```

Machine-readable output is available with:

```bash
python -m grocery_deal_intelligence.road_test --json
```

## Pipeline exercised

```text
captured fixture + expected SHA-256
        ↓
retailer adapter
        ↓
source evidence projection
        ↓
claim verification
        ↓
structural validation
        ↓
canonical admission
```

The road test uses the existing Despar and Carrefour adapters. It does not duplicate parser, evidence, validation, or admission rules.

## Fixtures

### Carrefour

```text
fixtures/carrefour/store-5190-flyer-56879.txt
SHA-256: 25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571
```

The captured Carrefour rows contain explicit promotion and loyalty claims that remain source-supported, structurally valid, and admission-eligible.

### Despar

```text
fixtures/despar/store-191-flyer-2026-08-13.txt
SHA-256: 54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17
```

The Despar rows contain source-supported shopper-offer facts but different amounts of promotion evidence. Grocery Offer v0.1 no longer requires a promotion claim when the source does not prove one, and it no longer requires unrelated promotion leaves when only one promotion claim is evidenced.

Therefore:

- Riso and Pedavena are admitted with no canonical `promotion` field;
- Olio is admitted with only `promotion.discount_text = "Sconto extra App -20%"`;
- no `promotion.type` or `promotion.requires_loyalty` value is synthesized.

All three Despar records are now structurally valid and admission-eligible from their existing evidence.

## PASS semantics

A road-test `PASS` means all of the following remain true for the committed fixtures:

- fixture identity is verified through the real adapters;
- no candidate claim is contradicted or unverifiable against projected source evidence;
- Carrefour rows remain structurally valid and admission-eligible;
- Despar rows remain structurally valid and admission-eligible without synthetic promotion claims;
- omitted promotion means no claim, never evidence of no promotion;
- fixture text is not mutated;
- no network access is required;
- no AI capability is required.

Fail-closed semantics are preserved because admission still requires every asserted canonical leaf to be source-supported and structurally valid. The corrected schema removes an obsolete completeness requirement; it does not relax claim verification.

## CI smoke gate

The repository CI runs the road test explicitly after pytest:

```bash
python -m grocery_deal_intelligence.road_test
```

This makes the real-fixture deterministic path a smoke gate in addition to the focused unit and integration-style tests.

## Non-goals

The road test does not fetch live retailer data, invent promotion or loyalty facts, weaken admission policy, use AI, repair evidence, infer locality, or add retailer-specific schema exceptions.
