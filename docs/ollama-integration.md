# Opt-in Ollama integration

Grocery Deal Intelligence keeps real AI execution outside the deterministic core and outside the default test path.

The real integration exercises:

```text
Ollama
  ↓
GiadaWare AI OllamaBackend
  ↓
ProposeOfferCandidateCapability
  ↓
GiadaWareAIAdapter
  ↓
ingest_offer(..., validate=True)
  ↓
validate_offers()
```

The AI result is advisory candidate data only. Deterministic validation remains the sole authority for canonical promotion.

## Requirements

Install the development dependencies, which include the optional GiadaWare AI integration dependency:

```bash
python -m pip install -e '.[dev]'
```

A local Ollama service must be running and the selected model must be available.

Default integration values:

```text
endpoint: http://127.0.0.1:11434
model:    qwen2.5:1.5b-instruct
```

## Run the real integration

```bash
GROCERY_DEAL_INTELLIGENCE_RUN_OLLAMA_INTEGRATION=1 \
python -m pytest -q tests/integration/test_real_ollama_ingestion.py
```

Optional overrides:

```bash
GROCERY_DEAL_INTELLIGENCE_RUN_OLLAMA_INTEGRATION=1 \
GROCERY_DEAL_INTELLIGENCE_OLLAMA_BASE_URL=http://127.0.0.1:11434 \
GROCERY_DEAL_INTELLIGENCE_OLLAMA_MODEL=qwen2.5:1.5b-instruct \
python -m pytest -q tests/integration/test_real_ollama_ingestion.py
```

## Default behavior

Without the explicit opt-in environment variable, the real-runtime test is skipped.

Therefore normal execution remains runtime-independent:

```bash
python -m pytest -q
```

No Ollama service, installed model, or network access is required for the standard regression suite.
