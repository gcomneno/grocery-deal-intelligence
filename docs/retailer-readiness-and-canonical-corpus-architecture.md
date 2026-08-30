# Retailer readiness and canonical corpus architecture

## Status

This document records the repository-grounded architecture recovery performed for
Issue #164.

It describes:

- the current retailer readiness state;
- the distinction between retailer research, implementation, admission, corpus
  presence, and current-offer availability;
- the smallest target architecture for assembling a unified canonical corpus;
- the migration sequence that should guide follow-up implementation issues.

This is a statement of the current verified repository architecture. It is not a
claim about retailer availability in the external market.

## Executive finding

Grocery Deal Intelligence currently has two retailers demonstrated end-to-end as
corpus-ready under the current canonical authority model:

- Carrefour;
- Despar.

Both have:

- committed store-scoped captured evidence;
- expected SHA-256 fixture identity;
- deterministic retailer adapters;
- source-evidence projection;
- deterministic claim verification;
- structural validation;
- canonical admission;
- deterministic road-test coverage.

Lidl is the closest next integration candidate.

Its committed source-shaped dataset can pass the current deterministic ingestion
and admission path, but Lidl is not yet part of the first-class deterministic
corpus path and its current fixture/adapter organization remains experimental.

Esselunga has substantial captured data, retailer-specific tooling, and
schema-valid retailer-neutral outputs, but those outputs have not been
demonstrated to carry current canonical admission authority. Raw source
projection currently lacks enough evidence for required canonical fields such as
locality, verification, provenance, and currency.

The remaining investigated retailers are research/watch cases rather than
canonical-corpus-ready integrations.

The principal architectural gap is therefore not query capability and not a lack
of studied retailers.

It is the absence of one explicit deterministic assembly boundary between
per-retailer ingestion results and the canonical corpus consumed by first-class
queries.

## Canonical authority model

The current authority chain remains:

```text
source record
    -> source evidence
    -> candidate / proposal
    -> claim verification
    -> structural validation
    -> canonical admission
    -> canonical | null
```

Canonical authority belongs only to deterministic application logic.

A retailer adapter, source registry, retailer-neutral JSON export, schema-valid
record, historical experiment, or AI result is not independently authoritative.

## Critical distinctions

The following states are intentionally distinct:

```text
retailer studied
    != retailer source can be acquired

retailer source can be acquired
    != retailer adapter exists

retailer adapter exists
    != retailer-neutral output exists

retailer-neutral output exists
    != deterministic canonical admission

deterministic canonical admission
    != retailer present in an assembled corpus

retailer present in an assembled corpus
    != retailer has a current offer at as_of
```

First-class queries operate only on the facts represented by the canonical
records supplied to them.

In particular:

```python
list_available_retailers(records)
```

answers which retailer identities are represented in those admitted canonical
records.

It must never derive availability from a source/adapter registry.

Likewise:

```python
list_current_offers(records, as_of=...)
```

answers which offers in the supplied canonical corpus are current at the
requested date.

It does not establish external-market completeness.

## Recovered current architecture

The authoritative deterministic ingestion path is implemented by
`grocery_deal_intelligence/ingestion.py`.

Conceptually:

```text
deterministic source record
        |
        v
project_source_evidence(...)
        |
        v
candidate copied from evidenced facts
        |
        v
verify_candidate_claims(...)
        |
        v
validate_offers(...)
        |
        v
evaluate_canonical_admission(...)
        |
        +----> canonical
        |
        `----> rejected + diagnostics
```

`ingest_deterministic_source_record()` owns per-record authority.

`ingest_deterministic_source_records()` is orchestration only. It must not create
new authority or repair one record using another.

`project_source_evidence()` currently contains deterministic retailer-specific
projection for Carrefour, Despar, Lidl, and Esselunga.

The deterministic acceptance road test currently exercises Carrefour and Despar.

The first-class canonical consumers, including current-offer and retailer
listing, consume caller-provided canonical records and perform no acquisition or
canonical admission.

## Retailer readiness matrix

Statuses in this matrix describe demonstrated repository state, not business or
external retailer status.

| Retailer | Discovery | Capture | Adaptation | Evidence projection | Verification | Structural validation | Canonical admission | Reproducible corpus input | Corpus-ready |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Carrefour | READY | READY | READY | READY | READY | READY | READY | READY | READY |
| Despar | READY | READY | READY | READY | READY | READY | READY | READY | READY |
| Lidl | READY | PARTIAL | PARTIAL | READY | READY | READY | READY | PARTIAL | PARTIAL |
| Esselunga | READY | PARTIAL | HISTORICAL / PARALLEL | PARTIAL | PARTIAL | PARTIAL | BLOCKED | PARTIAL | BLOCKED |
| Aldi | RESEARCH-ONLY | BLOCKED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | BLOCKED |
| Bennet | RESEARCH-ONLY | BLOCKED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | BLOCKED |
| Conad | RESEARCH-ONLY | BLOCKED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | BLOCKED |
| Coop Etruria | RESEARCH-ONLY | BLOCKED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | BLOCKED |
| Eurospin | RESEARCH-ONLY | BLOCKED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | BLOCKED |
| MD | RESEARCH-ONLY | BLOCKED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | BLOCKED |
| Pam | RESEARCH-ONLY | BLOCKED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | BLOCKED |
| Penny | RESEARCH-ONLY | BLOCKED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | BLOCKED |
| Todis | RESEARCH-ONLY | PARTIAL | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | NOT DEMONSTRATED | BLOCKED | BLOCKED |

## Carrefour

Evidence:

- `docs/carrefour-source-spike.md`
- `docs/carrefour-store-scoped-fixture-spike.md`
- `fixtures/carrefour/store-5190-flyer-56879.txt`
- `grocery_deal_intelligence/carrefour_fixture.py`
- `grocery_deal_intelligence/carrefour_adapter.py`
- Carrefour projection in `grocery_deal_intelligence/source_evidence.py`
- deterministic ingestion and road-test tests

Expected fixture SHA-256:

```text
25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571
```

Current deterministic road-test evidence demonstrates three parsed offers,
three structurally valid offers, three admission-eligible canonical offers,
zero contradicted claims, and zero unverifiable claims.

Classification: corpus-ready.

## Despar

Evidence:

- `docs/despar-source-surface-spike.md`
- `docs/despar-store-fixture-spike.md`
- `fixtures/despar/store-191-flyer-2026-08-13.txt`
- `grocery_deal_intelligence/despar_fixture.py`
- `grocery_deal_intelligence/despar_adapter.py`
- Despar projection in `grocery_deal_intelligence/source_evidence.py`
- deterministic ingestion, source-evidence, and road-test tests

Expected fixture SHA-256:

```text
54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17
```

Current deterministic road-test evidence demonstrates three parsed offers,
three structurally valid offers, three admission-eligible canonical offers,
zero contradicted claims, and zero unverifiable claims.

Classification: corpus-ready.

`docs/deterministic-batch-ingestion.md` still records the historical Despar
fail-closed structural outcome. That document must not be treated as current
truth where it conflicts with current deterministic code, tests, and road-test
evidence.

## Lidl

Relevant repository evidence includes:

- `lidl/README.md`
- `lidl/adapter/`
- `lidl/flyer-api/`
- `lidl/data/output/lidl-lucca-current.json`
- `lidl/data/output/lidl-lucca-current-retailer-neutral.json`
- `docs/lidl-deterministic-completion-rules.md`
- Lidl projection in `grocery_deal_intelligence/source_evidence.py`
- source-evidence verification tests

The source-shaped committed dataset:

```text
lidl/data/output/lidl-lucca-current.json
```

has been demonstrated locally through the current deterministic ingestion path
with:

```text
58 / 58 structurally valid
58 / 58 admission eligible
0 contradicted claims
0 unverifiable claims
```

The result is reproducible from the committed source-shaped dataset with:

```bash
python - <<'PY'
import json
from pathlib import Path

from grocery_deal_intelligence.ingestion import ingest_deterministic_source_records

records = json.loads(
    Path("lidl/data/output/lidl-lucca-current.json").read_text(encoding="utf-8")
)

batch = ingest_deterministic_source_records(records, retailer="lidl")

print("total:", batch["summary"]["total"])
print("structurally_valid:", batch["summary"]["structurally_valid"])
print("admission_eligible:", batch["summary"]["admission_eligible"])
print("claims_contradicted:", batch["summary"]["claims_contradicted"])
print("claims_unverifiable:", batch["summary"]["claims_unverifiable"])
PY
```

Expected evidence:

```text
total: 58
structurally_valid: 58
admission_eligible: 58
claims_contradicted: 0
claims_unverifiable: 0
```

This is strong evidence that Lidl can bridge into the current canonical
pipeline.

However:

- the Lidl area is still described as experimental;
- Lidl is not yet part of the deterministic corpus/acceptance road test;
- the source-shaped dataset does not yet have a first-class pinned fixture spec
  equivalent to Carrefour and Despar;
- rebuilding parts of the existing Lidl dataset uses current time;
- locality semantics between legacy retailer-neutral export and current source
  projection require an explicit decision.

The existing retailer-neutral export is useful evidence but is not the correct
source input to current deterministic ingestion.

Classification: admission-capable but not yet corpus-ready.

## Esselunga

Relevant evidence includes:

- `esselunga/adapter/`
- `esselunga/all-*.json`
- `esselunga/ari-*.json`
- `esselunga/data/output/esselunga-porcari-current-retailer-neutral.json`
- consumer real-data tests
- direct deterministic projection audit documentation
- Esselunga projection in `grocery_deal_intelligence/source_evidence.py`

The retailer-neutral output is structurally valid and useful to consumer tests.

That fact is not canonical admission.

Raw source projection currently does not establish enough evidence for required
canonical fields including currency, locality, verification, and provenance.

Some standalone Esselunga scripts also show internal drift relative to their
current dataclass/function shapes, so they must be treated as historical or
parallel architecture until reconciled.

Classification: substantial reusable evidence and tooling, but canonical
admission is blocked.

## Other investigated retailers

The following retailer investigations remain research/watch cases:

- Aldi;
- Bennet;
- Conad;
- Coop / Unicoop Etruria;
- Eurospin;
- MD;
- Pam / Panorama;
- Penny;
- Todis.

The recurring blocker is not necessarily absence of offer data.

It is the lack of one demonstrated reproducible evidence chain binding:

```text
selected store / locality
        +
exact offer or campaign payload
        +
capture identity
        +
parser
        +
deterministic evidence projection
        +
canonical admission
```

Typical documented blockers include session-dependent transport, unresolved
store-to-flyer mapping, unpinned payload bytes, missing SHA identity, incomplete
locality proof, or unresolved delivery/legal constraints.

These retailers must not be promoted to corpus-ready merely because source
research exists.

## Duplicated patterns recovered

The audit identified several recurring patterns:

- repeated retailer fixture and dataset loading;
- repeated SHA checking;
- retailer dispatch embedded directly in source-evidence projection;
- standalone retailer scripts with their own JSON/output conventions;
- parallel retailer-neutral export paths outside current canonical admission;
- inconsistent capture/freshness metadata handling;
- absence of one common fixture/source identity descriptor.

These observations justify a small orchestration boundary.

They do not justify a generalized ETL framework.

## Retailer-specific semantics that must remain local

A common architecture must not erase source-specific semantics.

Examples include:

- Carrefour current/base/unit price ordering;
- Despar raw base-price text semantics;
- Lidl `flyer_match` conservative interpretation;
- Lidl store-vs-regional locality evidence;
- Esselunga Fidaty and mechanic-code semantics;
- retailer-specific loyalty programs;
- cooperative/banner boundaries such as Pam/Panorama and Coop/Unicoop Etruria;
- store applicability and campaign binding.

No generic layer may infer these facts from similarity across retailers.

## Architectural gap

The missing boundary is:

```text
per-retailer deterministic ingestion results
                    |
                    v
          canonical corpus assembly
                    |
          +---------+---------+
          |                   |
          v                   v
 admitted canonical       rejected evidence
     records               + diagnostics
          |
          v
 immutable/queryable corpus
          |
          +--> list_available_retailers(...)
          +--> list_current_offers(...)
          +--> shopping consumers
```

The assembler must not become a new authority layer.

## Target architecture

The smallest professional target is:

```text
CAPTURED SOURCE ARTIFACT
        |
        v
RETAILER-SPECIFIC ADAPTER / ACL
        |
        v
DETERMINISTIC SOURCE RECORDS
        |
        v
EXISTING DETERMINISTIC INGESTION
        |
        v
INGESTION RESULT SET
        |
        +-------------------+
        |                   |
        v                   v
ADMITTED CANONICAL       REJECTED OUTCOMES
        |                   |
        +---------+---------+
                  |
                  v
         CANONICAL CORPUS ASSEMBLER
                  |
                  v
          TOP-LEVEL READ-ONLY CORPUS SNAPSHOT
                  |
                  v
          FIRST-CLASS CONSUMERS
```

This corresponds to a deliberately small use of established architectural
patterns.

### Ports and Adapters

Retailer pipelines are adapters around heterogeneous source systems.

The internal port is narrow: produce deterministic source records or
deterministic ingestion results that the existing core understands.

### Anti-Corruption Layer

Retailer-specific translation remains at the retailer boundary.

External price, loyalty, campaign, locality, and source structures do not leak
into canonical consumers.

### Explicit pipeline

The deterministic ingestion pipeline already exists and must be reused rather
than replaced.

### Registry

A future registry may describe which retailer pipelines the current build knows
how to invoke.

It is orchestration metadata only.

Registry membership is never proof of canonical retailer availability.

### Corpus assembler

The corpus assembler is implemented in
`grocery_deal_intelligence/corpus.py`.

Its first-class API is:

```python
snapshot = assemble_corpus(result_sets)
```

`CorpusSnapshot` exposes:

- `canonical_records`;
- `rejected`;
- `result_set_retailers`;
- aggregate `summary`;
- `ai_used`;
- `network_required`.

It consumes existing `IngestionResultSet` values, selects only canonical records
already exposed by those result sets, preserves rejected outcomes, and exposes a
deterministic corpus to canonical consumers.

`result_set_retailers` is orchestration observability only. It preserves the
exact retailer identity and order of input result sets, including duplicates.

Canonical retailer availability remains derived from:

```python
list_available_retailers(snapshot.canonical_records)
```

The assembler performs no new canonical authority work.

## Corpus assembler contract

The preferred input is an existing `IngestionResultSet` rather than a bare
list of canonical records.

Reason:

A bare canonical list loses:

- rejected records;
- diagnostics;
- source evidence;
- verification result;
- structural-validation result;
- admission reasons;
- the distinction between zero admitted records and pipeline failure.

GDI already exposes `IngestionResultSet` in
`grocery_deal_intelligence/ingestion_result_set.py` as a deterministic
projection boundary for one batch result.

The implemented abstraction is therefore not another batch-result projection
type. It is the multi-retailer assembly layer above existing deterministic
batch results.

The assembler consumes deterministic ingestion result sets and must:

1. never acquire network data;
2. never invoke AI;
3. never project source evidence;
4. never validate or revalidate canonical records;
5. never perform canonical admission;
6. select canonical records only from already-admitted outcomes;
7. preserve rejected outcomes separately;
8. preserve exact retailer identity and provenance;
9. allow one retailer to fail without discarding successful retailer results;
10. remain deterministic over captured inputs;
11. never use registry membership as evidence of retailer availability;
12. never repair or synthesize missing source facts.

## Failure isolation

Retailer pipeline outcomes are independent.

One retailer failure must not invalidate successfully assembled retailers.

A retailer may produce:

```text
SUCCESS WITH CANONICAL RECORDS

SUCCESS WITH ZERO CANONICAL RECORDS

SUCCESS WITH REJECTED RECORDS

PIPELINE FAILURE
```

These outcomes must remain distinguishable.

A failed or rejected retailer must never be silently retried by weakening
evidence, borrowing facts from another record, or invoking AI repair.

## Corpus snapshot metadata

A future persisted corpus snapshot may contain non-authoritative operational
metadata such as:

- `assembled_at`;
- source capture identity;
- source SHA-256;
- source URL where applicable;
- retailer pipeline identity;
- source `observed_at`;
- validity range summaries;
- canonical count;
- rejected count;
- failed-pipeline count;
- `ai_used`;
- `network_required`.

These fields describe the snapshot and its construction.

They do not authorize offer truth.

## Recommended migration sequence

The migration should remain incremental:

1. implement the corpus assembler over existing deterministic batch results;
2. prove that registry/orchestration metadata cannot define retailer
   availability;
3. assemble the existing Carrefour + Despar deterministic results through it;
4. add deterministic snapshot metadata;
5. bridge Lidl source-shaped captured records into the assembled corpus;
6. resolve Lidl locality semantics explicitly;
7. clean stale documentation where current deterministic behavior supersedes it;
8. establish an Esselunga acquisition-context evidence contract;
9. admit Esselunga only after source-backed canonical authority is demonstrated;
10. revisit research/watch retailers one at a time when their documented
    blockers are resolved.

## Explicit non-goals

This architecture must not introduce:

- a generalized ETL framework;
- a plugin framework;
- a dependency-injection container;
- a workflow engine;
- an event bus;
- generic retailer aliasing;
- automatic retailer-family normalization;
- AI-based source repair;
- relaxed canonical validation;
- market-completeness claims.

## Implemented corpus assembly

The first multi-retailer corpus assembly boundary is implemented over existing
deterministic `IngestionResultSet` values.

The initial acceptance path assembles:

```text
Carrefour: 3 admitted canonical records
Despar:    3 admitted canonical records
Total:     6 admitted canonical records
```

This implementation intentionally does not increase retailer count or introduce
new authority.

The next retailer-integration step is to bridge Lidl source-shaped captured
records through the same deterministic ingestion and corpus assembly path,
without treating its legacy retailer-neutral export as canonical authority.

## Durable principle

The architecture recovered by this audit can be summarized as:

```text
heterogeneous sources
    -> retailer-specific evidence boundaries
    -> shared deterministic authority pipeline
    -> admitted outcomes
    -> deterministic corpus assembly
    -> retailer-neutral consumers
```

When completeness and verifiability conflict, the canonical corpus remains
defined by what deterministic evidence and admission can prove.
