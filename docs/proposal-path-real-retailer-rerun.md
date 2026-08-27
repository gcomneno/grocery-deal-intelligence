# Proposal v0.1 real-retailer rerun

## Status

Experiment for Issue #58.

This experiment reuses the exact fixed four-record corpus already used by the direct-canonical real-retailer experiments and routes it through the Proposal v0.1 end-to-end ingestion path.

It is measurement-only. It does not change Proposal v0.1, prompts, source-evidence extraction, projection, canonical schema, canonical validation, or admission policy.

## Fixed corpus

- Esselunga `2_27__8400__1`
- Esselunga `2_27__8400__2`
- Lidl fixture index 0
- Lidl fixture index 1

Fixture loading and identity checks are reused from `experiments.run_multi_retailer_ai_ingestion`.

## Path under measurement

```text
raw source
    ↓
deterministic source evidence
    ↓
Proposal v0.1 AI capability/adapter
    ↓
proposal validation
    ↓
Proposal claim verification
    ↓
deterministic Proposal→canonical projection
    ↓
canonical structural validation
    ↓
projected-candidate claim verification
    ↓
admission
    ↓
canonical / null
```

## Baseline

Measured direct-canonical grounded baseline from Issue #42:

```text
records:               4
structurally valid:    4
admission eligible:    4
canonical:             4
AI/candidate claims:  71
supported:            42
contradicted:          0
unverifiable:         29
```

The Proposal-path experiment is not required to reproduce `4/4 canonical`. A deterministic `not_projectable` result is correct when required canonical facts are not established by supported Proposal claims or source evidence.

## Execution

```bash
GROCERY_DEAL_INTELLIGENCE_RUN_PROPOSAL_PATH_EXPERIMENT=1 \
GROCERY_DEAL_INTELLIGENCE_OLLAMA_TIMEOUT=300 \
python -m experiments.run_proposal_path_real_retailer_ingestion
```

Optional runtime overrides remain:

```text
GROCERY_DEAL_INTELLIGENCE_OLLAMA_BASE_URL
GROCERY_DEAL_INTELLIGENCE_OLLAMA_MODEL
GROCERY_DEAL_INTELLIGENCE_OLLAMA_TIMEOUT
```

## Interpretation

Primary questions:

1. How many claims does Proposal v0.1 emit compared with the 71 direct-canonical claims?
2. How many emitted claims are supported, contradicted, or unverifiable?
3. Which records are deterministically projectable?
4. Which required canonical paths prevent projection?
5. For projected records, do canonical validation and admission still behave independently?

No migration decision should be made before recording the real run evidence.