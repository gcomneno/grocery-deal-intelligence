# Business road test

The business road test is a read-only composition over committed real retailer evidence. Its purpose is not to force a shopping answer. Its purpose is to show how far the current GDI authority chain can proceed before an existing fail-closed boundary correctly stops the scenario.

## Principle

A business road test treats `unknown` as a valid successful outcome when the available evidence and implemented contracts do not authorize a stronger result.

```text
source evidence
    -> canonical admission
    -> normalized product attributes
    -> semantic comparability
    -> economic normalization
    -> exact bilateral price comparison
```

The composition must never repair rejected data, invent missing evidence, use a non-canonical candidate downstream, or introduce new semantic or economic authority merely to reach a later stage.

## Initial real-offer scenario

The scenario uses two committed fixture records:

- Carrefour: `Raffo Birra Raffo Originale Conf. 3 pz da 330 ml Cad. 990 ml`, current price `2.49 EUR`;
- Despar: `Birra Speciale Pedavena`, current price `1.29 EUR`.

Both fixtures are verified against their expected SHA-256 identities before being interpreted.

## Current authority progression

After the canonical promotion-claim correction in #148, both selected records reach canonical admission from their existing source evidence.

That does not imply that they are already comparable.

The business road test now executes the next existing boundary, `normalize_product_attributes()`, over both admitted canonical offers.

### Pedavena

Despar preserves `packaging_text = "500 ml"`. Deterministic quantity normalization therefore supports:

```text
volume_ml = 500
```

No product-family claim is invented.

### Raffo

The Carrefour source name contains multiple quantity expressions:

```text
3 pz da 330 ml Cad. 990 ml
```

The current canonical offer does not contain a separate `packaging_text`, and the existing deterministic parser does not authorize one unique quantity from the multiple expressions in the product name. It therefore returns fail-closed:

```text
quantity_evidence_unavailable
```

The business road test must not choose `330 ml`, `990 ml`, or calculate a package quantity merely to advance the scenario.

## Current road-test result

```text
SOURCE EVIDENCE
Carrefour: PASS
Despar:    PASS

CANONICAL ADMISSION
Carrefour: PASS
Despar:    PASS

NORMALIZED ATTRIBUTES
Carrefour: FAIL_CLOSED
Reason: quantity_evidence_unavailable
Despar:    PASS

SEMANTIC COMPARABILITY
NOT REACHED

ECONOMIC NORMALIZATION
NOT REACHED

PRICE COMPARISON
NOT REACHED

FINAL
UNKNOWN
Authorized stopping boundary: normalized_attributes
```

Downstream stages are not called with synthetic inputs.

## Promotion correction and authority

The scenario advances beyond canonical admission because Grocery Offer v0.1 no longer requires promotion facts unrelated to the evidence actually asserted by a shopper offer.

This means:

```text
promotion omitted
    -> no canonical promotion claim
```

It does not mean:

```text
promotion omitted
    -> promotion is false
    -> requires_loyalty is false
```

Pedavena becomes canonical without any promotion object because its source does not authorize one. This is a structural contract correction, not source completion or retailer-specific repair.

## Relationship to the deterministic road test

The deterministic road test remains the multi-retailer ingestion and canonical-admission acceptance boundary:

```text
python -m grocery_deal_intelligence.road_test
```

The business road test is complementary. It asks an explicit cross-retailer business question and records where downstream authority stops:

```text
python -m grocery_deal_intelligence.business_road_test
```

For stable machine-readable output:

```text
python -m grocery_deal_intelligence.business_road_test --json
```

An expected fail-closed `unknown` returns success when it matches the current scenario contract.

## What this road test does not authorize

The current scenario does not add or imply:

- missing Despar promotion facts;
- `requires_loyalty = false` from absence;
- repaired or reinterpreted Carrefour quantity evidence;
- a `beer` product-family vocabulary entry;
- a beer comparison policy;
- semantic comparability merely because both product names describe beer;
- source unit price as derived economic authority;
- ranking or recommendation;
- AI-generated authority.

The distinctions remain explicit:

```text
same_product
!= comparable
!= economically normalizable
!= cheaper
!= recommended
```

## Future progression

Future domain changes may allow this exact same scenario to move farther through the authority chain. The road-test philosophy must not change when that happens.

Each newly reached stage must consume only evidence and decisions already authorized by the preceding stage, and any later unsupported boundary must still fail closed.
