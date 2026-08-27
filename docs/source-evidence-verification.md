# Deterministic source-evidence verification

Issue #30 introduces a deterministic layer for comparing schema-valid AI candidate claims with facts actually supported by retailer source evidence.

This layer does **not** change canonical admission policy. It only records semantic evidence classifications for later analysis.

## Pipeline

```text
raw retailer source + trusted retailer context
        ↓
project_source_evidence()
        ↓
partial canonical-shaped evidence
        ↓
AI candidate
        ↓
verify_candidate_claims()
        ↓
supported / contradicted / unverifiable
```

## Status semantics

- `supported`: the candidate leaf claim equals an explicitly projected evidence value;
- `contradicted`: the source projection provides an explicit value for that same claim path and the candidate differs;
- `unverifiable`: no deterministic evidence value is available for that claim path.

`unverifiable` never means false.

## Conservative projection

Projection deliberately emits only mappings that can be justified directly from the versioned source representation or trusted source context.

For example, the Esselunga fixture context can deterministically establish the retailer as `esselunga`, while `FORST` appearing in a product title cannot be reinterpreted as the retailer. Conversely, an Esselunga record that contains no locality evidence does not produce locality claims merely because the model can generate structurally valid locality data.

The Lidl projection reuses direct fields such as product name, prices, promotion type, validity, stores, explicit verification values, and provenance values where the source representation exposes an unambiguous mapping.

Ambiguous mappings are intentionally omitted.

## Authority boundary

This issue does not modify:

- `schema/grocery-offer-v0.1.schema.json`;
- `validate_offers()`;
- `GiadaWareAIAdapter`;
- the schema-constrained AI proposal contract;
- canonical admission semantics.

Therefore a candidate may still be structurally canonical according to the current validator while having `contradicted` or `unverifiable` semantic claims. Issue #31 will measure that behavior on the fixed four-record real-retailer corpus. Issue #32 will decide whether and how semantic evidence participates in canonical admission.

## Design rule

```text
Project only what the source proves.
Unknown is not false.
Classification is evidence, not admission policy.
```
