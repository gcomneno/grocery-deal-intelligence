# Canonical admission policy

Structural JSON Schema validity is necessary for canonical admission but is not sufficient.

The deterministic admission policy consumes two already-separated evidence layers:

```text
candidate
  ↓
canonical JSON Schema validation
  ↓
structurally_valid

candidate + deterministic source evidence
  ↓
claim verification
  ↓
supported / contradicted / unverifiable
```

It then decides only whether the candidate is eligible for canonical authority.

## Policy v0.1

A candidate is eligible only when all of the following hold:

1. the candidate is structurally valid;
2. no candidate claim is deterministically `contradicted`;
3. every critical claim is positively `supported`.

Critical claim paths are:

```text
retailer
product_name
price
validity.from
validity.to
```

These claims identify the merchant, product, effective deal price and offer time window.

## Unverifiable claims

`unverifiable` does not mean false.

For non-critical claims, `unverifiable` is tolerated by v0.1 and remains visible as evidence debt.

For critical claims, `unverifiable` blocks admission because canonical authority requires positive source support for the essential offer facts.

## Contradictions

Any deterministic contradiction blocks admission, including contradictions on non-critical fields. A system that knowingly admits a contradicted claim would be granting canonical authority to information it already has evidence against.

## Machine-readable reasons

The policy returns stable reason codes:

- `structural_invalid`;
- `contradicted_claim`;
- `critical_claim_unsupported`.

The policy does not repair candidates, change evidence, or invoke AI.

## Separation from ingestion

This issue introduces the policy as an independent deterministic layer. It does not silently alter the existing `ingest_offer()` semantics.

The explicit composition target is:

```text
source
  ↓
optional AI proposal
  ↓
candidate
  ↓
structural validation
  ↓
source-evidence projection + claim verification
  ↓
canonical admission policy
  ↓
eligible / ineligible
```

A later integration change may compose these layers while keeping each result separately observable.

## Evidence basis

The fixed four-record semantic rerun that preceded this policy observed:

```text
4 structurally accepted records
70 total claims
35 supported
7 contradicted
28 unverifiable
```

The two Esselunga candidates contained deterministic contradictions on essential offer facts. The two Lidl candidates contained no contradictions and strong positive support on the critical identity, price and validity claims.

This policy is therefore evidence-driven but intentionally conservative. Tightening additional fields into the critical set requires further evidence and a separate change.
