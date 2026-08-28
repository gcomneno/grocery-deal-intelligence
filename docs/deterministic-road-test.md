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

The captured Carrefour rows contain enough explicit promotion and loyalty semantics to produce source-supported canonical candidates that are structurally valid and admission-eligible.

### Despar

```text
fixtures/despar/store-191-flyer-2026-08-13.txt
SHA-256: 54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17
```

The Despar rows remain fully source-supported at the claim level, but the captured evidence does not provide all canonical promotion fields required by Grocery Offer v0.1. Their structural rejection is therefore expected fail-closed behavior.

The road test must not invent `promotion.type` or `promotion.requires_loyalty` merely to make Despar pass.

## PASS semantics

A road-test `PASS` means all of the following remain true for the committed fixtures:

- fixture identity is verified through the real adapters;
- no candidate claim is contradicted or unverifiable against projected source evidence;
- Carrefour rows remain structurally valid and admission-eligible;
- Despar rows remain structurally rejected rather than repaired with unsupported facts;
- fixture text is not mutated;
- no network access is required;
- no AI capability is required.

A Despar `0/N eligible` result is not itself a road-test failure. It is the expected consequence of the current source evidence boundary.

## CI smoke gate

The repository CI runs the road test explicitly after pytest:

```bash
python -m grocery_deal_intelligence.road_test
```

This makes the real-fixture deterministic path a smoke gate in addition to the focused unit and integration-style tests.

## Non-goals

The road test does not fetch live retailer data, weaken the schema or admission policy, use AI, repair incomplete evidence, infer locality, or treat a rejected offer as an execution failure when rejection is the expected deterministic outcome.
