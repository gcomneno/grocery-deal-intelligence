# Deterministic batch source-record ingestion

## Purpose

`ingest_deterministic_source_records()` is the orchestration layer for multiple deterministic retailer source records.

It does not introduce new authority. Every input record is delegated to the already established single-record primitive:

```text
retailer adapter records
        ↓
ingest_deterministic_source_records(...)
        ↓
for each record:
    ingest_deterministic_source_record(...)
        ↓
per-record evidence → verification → validation → admission
        ↓
ordered per-record results + aggregate summary
```

## Contract

```python
ingest_deterministic_source_records(source_records, *, retailer)
```

The batch function:

- requires a non-empty retailer;
- accepts an iterable of deterministic source records;
- preserves record order;
- never mutates caller records;
- delegates each record to the first-class single-record deterministic ingestion path;
- keeps ineligible records visible instead of dropping them;
- aggregates structural, admission, canonical, claim-verification, and rejection-reason counts;
- performs no cross-record evidence repair;
- performs no synthetic fact completion;
- invokes no AI;
- requires no network access.

## Result shape

The returned object contains:

```text
retailer
records[]
summary
ai_used = false
network_required = false
```

`records[]` preserves the complete per-record authority layers returned by `ingest_deterministic_source_record()`.

The deterministic `summary` contains:

```text
total_records
structurally_valid
structurally_invalid
admission_eligible
admission_ineligible
canonical_records
claims.supported
claims.contradicted
claims.unverifiable
rejection_reasons
```

The aggregate summary is observational only. It never changes the outcome of an individual record.

## Fail-closed semantics

An ineligible record remains present in `records[]` with `canonical = None` and its admission reasons intact.

The batch layer does not:

- drop failed records;
- repair them from neighboring records;
- borrow evidence between products;
- fill required canonical facts;
- convert aggregate confidence into per-record authority.

## Real-fixture acceptance

The committed deterministic fixtures exercise both outcomes.

### Carrefour

```text
3 records
3 structurally valid
3 admission eligible
3 canonical
0 contradicted claims
0 unverifiable claims
```

### Despar

```text
3 records
0 structurally valid
3 structurally invalid
0 admission eligible
0 canonical
structural_invalid = 3
0 contradicted claims
0 unverifiable claims
```

The Despar result remains a successful fail-closed outcome: its source-supported claims are preserved, but structurally incomplete canonical offers are not admitted.

## Road-test integration

The deterministic road test now calls the batch primitive once per retailer and consumes its aggregate summary.

This keeps the executable smoke gate aligned with the same reusable core path that application code can call:

```text
adapter
  ↓
batch ingestion
  ↓
single-record deterministic ingestion
  ↓
road-test assertions over observed outcomes
```

The road test verifies the batch path; it does not reimplement batch semantics.

## Non-goals

This change introduces no:

- schema modification;
- admission-policy modification;
- source-evidence projection change;
- retailer-adapter semantic change;
- locality inference;
- AI behavior;
- network dependency;
- source repair;
- cross-record evidence completion.
