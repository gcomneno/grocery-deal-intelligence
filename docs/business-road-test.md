# Business road test

The business road test is a read-only composition over committed real retailer
evidence. Its purpose is not to force a shopping answer. Its purpose is to show
how far the current GDI authority chain can proceed before an existing
fail-closed boundary correctly stops the scenario.

## Principle

A business road test treats `unknown` as a valid successful outcome when the
available evidence and implemented contracts do not authorize a stronger result.

```text
source evidence
    -> canonical admission
    -> normalized product attributes
    -> semantic comparability
    -> economic normalization
    -> exact bilateral price comparison
```

The composition must never repair rejected data, invent missing evidence, use a
non-canonical candidate downstream, or introduce new semantic or economic
authority merely to reach a later stage.

## Initial real-offer scenario

The first scenario uses two committed fixture records:

- Carrefour: `Raffo Birra Raffo Originale Conf. 3 pz da 330 ml Cad. 990 ml`,
  current price `2.49 EUR`;
- Despar: `Birra Speciale Pedavena`, current price `1.29 EUR`.

Both fixtures are verified against their expected SHA-256 identities before
being interpreted.

Today both selected records reach deterministic source evidence successfully.
Carrefour also reaches canonical admission. Despar fails canonical admission
with the existing `structural_invalid` reason because available source evidence
does not satisfy the required canonical `promotion` contract.

That failure is the authorized stopping point of the scenario.

Therefore the current road-test result is:

```text
SOURCE EVIDENCE
Carrefour: PASS
Despar:    PASS

CANONICAL ADMISSION
Carrefour: PASS
Despar:    FAIL_CLOSED
Reason: structural_invalid

NORMALIZED ATTRIBUTES
NOT REACHED

SEMANTIC COMPARABILITY
NOT REACHED

ECONOMIC NORMALIZATION
NOT REACHED

PRICE COMPARISON
NOT REACHED

FINAL
UNKNOWN
Authorized stopping boundary: canonical_admission
```

Downstream stages are not called with synthetic inputs. In particular, the
rejected Despar candidate is never treated as canonical data.

## Relationship to the deterministic road test

The existing deterministic road test remains the multi-retailer ingestion and
canonical-admission acceptance boundary:

```text
python -m grocery_deal_intelligence.road_test
```

The business road test is complementary. It asks an explicit cross-retailer
business question and records where authority stops:

```text
python -m grocery_deal_intelligence.business_road_test
```

For stable machine-readable output:

```text
python -m grocery_deal_intelligence.business_road_test --json
```

An expected fail-closed `unknown` returns success when it matches the scenario
contract.

## What this road test does not authorize

The current scenario does not add or imply:

- missing Despar promotion facts;
- downstream use of rejected canonical candidates;
- a `beer` product-family vocabulary entry;
- a beer comparison policy;
- repaired or reinterpreted Carrefour quantity evidence;
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

Future domain changes may allow this exact same scenario to move farther through
the authority chain. The road-test philosophy must not change when that happens.
Each newly reached stage must consume only evidence and decisions already
authorized by the preceding stage, and any later unsupported boundary must still
fail closed.
