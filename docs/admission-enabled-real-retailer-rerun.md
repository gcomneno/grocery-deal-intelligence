# Admission-enabled fixed retailer rerun

This experiment reruns the same four real retailer fixtures used by the previous multi-retailer AI measurements, but now invokes the explicit admission-enabled ingestion path introduced by #36.

The corpus, selectors, order, AI model, backend, canonical schema, source-evidence projection, claim verifier, and admission policy remain unchanged.

For each fixture the runner records:

- `candidate`;
- `validated`;
- `structural_validation`;
- `source_evidence`;
- `claim_verification`;
- `semantic_summary`;
- `admission`;
- `canonical`.

`validated` still means only structural schema validity. `canonical` is present only when `admission.eligible` is true.

The aggregate summary records structural validity, admission eligibility, canonical count, semantic claim counts, and admission reason counts.

The experiment is opt-in. On the local CPU reference runtime, a larger client timeout may be useful:

```bash
GROCERY_DEAL_INTELLIGENCE_RUN_MULTI_RETAILER_EXPERIMENT=1 \
GROCERY_DEAL_INTELLIGENCE_OLLAMA_TIMEOUT=300 \
python -m experiments.run_multi_retailer_ai_ingestion
```

The timeout changes only client tolerance. It does not change model, prompt, schema, verifier, admission policy, or corpus.

The run must measure outcomes rather than encode expected retailer-specific results.
