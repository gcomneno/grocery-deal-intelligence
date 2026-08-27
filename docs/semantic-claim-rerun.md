# Fixed-corpus semantic claim rerun

This experiment reruns the same four retailer fixtures used by the prior multi-retailer AI experiment and adds deterministic source-support classification from the source-evidence layer introduced by #30.

The experiment remains opt-in and keeps the same fixture order, selectors, backend, model, canonical schema, and deterministic structural validator.

For each fixture the evidence records:

- `source_identity`;
- `source_record`;
- `candidate`;
- `validated`;
- `canonical`;
- structural `diagnostics`;
- deterministic `source_evidence`;
- leaf-level `claim_verification`;
- per-record `semantic_summary`.

Aggregate output adds:

- `total_claims`;
- `supported_claims`;
- `contradicted_claims`;
- `unverifiable_claims`.

The three statuses mean:

- `supported`: the candidate leaf equals a deterministically projected source-evidence leaf at the same canonical path;
- `contradicted`: the source projects a value for the same path and the candidate value differs;
- `unverifiable`: the deterministic projection contains no evidence for that candidate path.

`unverifiable` does not mean false. Semantic classifications do not change canonical admission in this experiment.

Run from the repository root with the project virtual environment active:

```bash
GROCERY_DEAL_INTELLIGENCE_RUN_MULTI_RETAILER_EXPERIMENT=1 \
python -m experiments.run_multi_retailer_ai_ingestion
```

The evidence from this rerun is intended to inform the later canonical admission policy issue. It must not be used to tune the prompt or alter validation during the measurement itself.
