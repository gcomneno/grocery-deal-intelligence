# Grocery Deal Intelligence

Grocery Deal Intelligence is a verification-first learning laboratory for
collecting, interpreting, validating, admitting, and comparing grocery offers
across retailers.

The project is retailer-neutral at the canonical data boundary.

## Deterministic core

The preferred ingestion path is deterministic whenever captured retailer source
records contain sufficient explicit evidence:

    source record
        -> source evidence
        -> claim verification
        -> structural validation
        -> canonical admission
        -> canonical | null

Single-record ingestion owns per-record authority.

Batch ingestion only orchestrates those per-record results and preserves
rejected or ineligible records together with their diagnostics and provenance.

The system is intentionally fail-closed: missing or unsupported facts are not
invented merely to increase canonical output.

## Retailer adapters

Deterministic retailer adapters currently include:

- Lidl
- Esselunga
- Despar
- Carrefour

The investigated retailer source-discovery phase is complete. New source
investigation requires an explicit scoped decision.

## Canonical contract

The canonical normalized schema is:

    schema/grocery-offer-v0.1.schema.json

Canonical data is authorized only by deterministic application logic.

AI-assisted ingestion is optional and advisory. AI output is data, never
authority, and remains subject to deterministic evidence verification,
validation, projection where applicable, and canonical admission.

The deterministic core does not require network access, Ollama, GiadaWare AI,
or a model runtime.

## Verification

The deterministic multi-retailer road test is:

    python -m grocery_deal_intelligence.road_test

It exercises the reusable deterministic ingestion path against committed
evidence fixtures and treats expected fail-closed outcomes as valid behavior.

For repository-wide operational and architectural rules, see `AGENTS.md`.
