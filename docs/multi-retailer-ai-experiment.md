# Deterministic multi-record real-retailer AI experiment

Issue #24 extends the single-record experiment from #20 to a fixed four-record corpus spanning Esselunga and Lidl.

## Fixed corpus

The fixture order is canonical and deterministic:

```text
1. esselunga/all-8400.json
   id = 2_27__8400__1
   code = 531442

2. esselunga/all-8400.json
   id = 2_27__8400__2
   code = 571055

3. lidl/data/output/lidl-lucca-current.json
   index = 0
   product_name = Controfiletti di pollo

4. lidl/data/output/lidl-lucca-current.json
   index = 1
   product_name = Peperone Corno Sweet Palermo
```

Each source identity includes the source-file SHA-256. Selection is never random.

## Per-record path

Every fixture is executed independently through:

```text
real retailer source record
        ↓
GiadaWare AI OllamaBackend
        ↓
ProposeOfferCandidateCapability
        ↓
GiadaWareAIAdapter
        ↓
ingest_offer(validate=True)
        ↓
validate_offers()
        ↓
accepted / rejected
          ↓
diagnose_candidate_rejection()
```

Diagnostics are emitted only for rejected candidates. They are deterministic schema diagnostics from #22 and do not attempt semantic hallucination detection.

## Evidence document

The experiment prints one JSON document containing:

```text
experiment
fixtures[]
summary
runtime_metadata
```

Each fixture contains:

```text
source_identity
source_record
candidate
validated
canonical
diagnostics
```

The deterministic summary contains:

```text
total_records
accepted_records
rejected_records
diagnostic_category_counts
```

The summary aggregates observed validation/diagnostic outcomes only. It does not infer model quality or semantic truth.

## Run locally

Activate the project virtual environment and run:

```bash
GROCERY_DEAL_INTELLIGENCE_RUN_MULTI_RETAILER_EXPERIMENT=1 \
python -m experiments.run_multi_retailer_ai_ingestion
```

Defaults:

```text
Ollama endpoint: http://127.0.0.1:11434
model: qwen2.5:1.5b-instruct
```

Optional overrides:

```bash
GROCERY_DEAL_INTELLIGENCE_OLLAMA_BASE_URL=http://127.0.0.1:11434 \
GROCERY_DEAL_INTELLIGENCE_OLLAMA_MODEL=qwen2.5:1.5b-instruct \
GROCERY_DEAL_INTELLIGENCE_RUN_MULTI_RETAILER_EXPERIMENT=1 \
python -m experiments.run_multi_retailer_ai_ingestion
```

The experiment is intentionally opt-in. Normal CI never requires Ollama.

## Authority boundary

A candidate remains advisory data until deterministic validation accepts it.

```text
AI proposal != canonical fact
```

A rejected candidate remains rejected even if it looks plausible. Diagnostics explain only what the schema can prove; they never repair or authorize candidate data.

## Non-goals

This experiment does not perform live retailer acquisition, random sampling, prompt tuning, auto-repair, scoring, recommendation, production persistence, or semantic hallucination classification.

Design rule:

```text
Sample deterministically.
Let AI propose independently.
Validate every candidate.
Diagnose every rejection deterministically.
Aggregate observations, not assumptions.
```
