# Deterministic ingestion result set

## Purpose

`IngestionResultSet` is a deterministic, read-only projection over an existing
batch result from `ingest_deterministic_source_records()`.

It bridges batch ingestion outcomes to canonical consumers without becoming a
new authority layer:

```text
deterministic batch result
  -> IngestionResultSet
       -> outcomes
       -> admitted
       -> canonical_records
       -> rejected
```

## Public Surface

The result set exposes:

```text
retailer
outcomes
admitted
canonical_records
rejected
summary
ai_used
network_required
```

`admitted` and `rejected` contain frozen indexed entries:

```text
record_index
outcome
```

The index is the original deterministic batch position.

## Authority Boundary

Result-set construction deep-copies the incoming batch result once and then
validates the copied snapshot for internal consistency.

It does not:

- ingest source records;
- validate candidates;
- evaluate admission;
- project source evidence;
- call retailer adapters;
- invoke AI;
- require network access;
- rebuild, normalize, repair, or re-authorize canonical records.

`canonical_records` is projected only from already admitted
`outcome["canonical"]` mappings in the copied batch snapshot.

## Read-Only Boundaries

Collections are tuple-backed and preserve deterministic order.

Top-level outcome, summary, and canonical mappings are exposed through read-only
mapping boundaries. Nested diagnostics, evidence, provenance, and canonical
fields are not recursively frozen, so recursive immutability is not guaranteed.

The read-only boundary prevents replacing top-level records through the result
set. The one-time deep copy isolates the result set from later caller mutation.

## Fail-Closed Validation

Malformed or internally inconsistent batch results raise `ValueError`.

The result set requires:

- a mapping batch result;
- a non-empty string retailer;
- the ordered batch `records` list;
- a mapping summary;
- mapping outcomes;
- mapping admission decisions;
- `admission.eligible` as an actual boolean;
- eligible outcomes with non-null canonical mappings;
- ineligible outcomes with `canonical is None`;
- observed outcome, admission, rejection, canonical, and structural counts that
  match the summary.

Rejected and ineligible outcomes remain visible with their existing diagnostics,
evidence, provenance, verification results, and admission reasons.
