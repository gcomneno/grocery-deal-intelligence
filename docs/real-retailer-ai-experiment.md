# First controlled real-retailer AI ingestion experiment

Issue #20 introduces a controlled evidence-producing experiment over one real retailer record already versioned in this repository.

## Fixed source identity

The experiment always selects:

```text
path: esselunga/all-8400.json
record id: 2_27__8400__1
record code: 531442
```

Selection is by stable record id, not by random choice. The runner also records the SHA-256 of the source file used for the execution.

## Authority boundary

The experiment records three distinct layers:

```text
retailer source record
        ↓
AI candidate proposal
        ↓
deterministic validation decision
```

The candidate is evidence of what the AI proposed. It is not evidence that the offer is canonical or valid.

The experiment deliberately does not enrich the raw retailer record with facts that are absent from it merely to help the model pass validation. A real run may therefore end in either:

```text
validated=true  → canonical contains the deterministic-accepted record
validated=false → canonical is null
```

Both outcomes are valid experiment results.

## Run locally

Run the experiment as a Python module from the repository root. This preserves the repository root on Python's import path and allows the application package to be imported correctly.

Create/activate the project virtual environment and install development dependencies if needed, then run:

```bash
GROCERY_DEAL_INTELLIGENCE_RUN_REAL_RETAILER_EXPERIMENT=1 \
python -m experiments.run_real_retailer_ai_ingestion
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
GROCERY_DEAL_INTELLIGENCE_RUN_REAL_RETAILER_EXPERIMENT=1 \
python -m experiments.run_real_retailer_ai_ingestion
```

The command prints one JSON evidence document containing:

```text
source_identity
source_record
candidate
validated
canonical
runtime_metadata
```

Redirect stdout to a file if a local run artifact is desired. Generated runtime evidence is not automatically persisted by the application.

## Non-goals

This experiment performs no retailer acquisition, crawling, scoring, recommendation, persistence, or production automation.

Design rule:

```text
Observe the source.
Let AI propose.
Let deterministic validation decide.
Record all three separately.
```
