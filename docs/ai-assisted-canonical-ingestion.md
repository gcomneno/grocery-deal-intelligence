# AI-Assisted Canonical Ingestion

## Purpose

The AI-assisted canonical ingestion boundary defines how optional AI
assistance may participate in the transformation of external retailer data
into candidate canonical grocery offer records.

The boundary exists to allow interpretation and extraction assistance without
delegating canonical authority to an AI system.

The canonical dataset remains governed by deterministic software.

## Core principle

AI assistance may propose canonical record content.

Only deterministic validation may establish canonical schema conformity.

Therefore:

`AI output != canonical record`

AI output is candidate data until it has passed the canonical validation
layer.

## External contract

The canonical record structure is defined by the externally provided
canonical contract:

`schema/grocery-offer-v0.1.schema.json`

The ingestion layer adapts external source data to this contract.

The ingestion implementation must not redefine the canonical schema.

## AI role

GiadaWare AI may be used as an optional read-only advisory component during
ingestion.

AI assistance may perform tasks such as:

- interpreting semi-structured source content;
- extracting candidate field values;
- proposing mappings from source fields to canonical fields;
- interpreting textual descriptions;
- identifying possible structural correspondences;
- identifying ambiguities for subsequent deterministic handling.

AI assistance produces data for the ingestion pipeline.

AI assistance does not establish canonical truth.

## Optionality

AI assistance is optional.

The ingestion system must not require AI when deterministic transformation
is sufficient.

The presence or absence of an AI provider must not change the canonical
schema or the deterministic validation contract.

A future AI provider may replace GiadaWare AI without changing the canonical
validation boundary.

## Read-only boundary

AI assistance must operate through the read-only contract exposed by
GiadaWare AI.

AI assistance must not:

- modify the source dataset;
- modify canonical records in place;
- write to canonical persistence;
- execute retailer operations;
- perform network-side mutations;
- bypass deterministic validation;
- alter the canonical schema.

AI interaction is observational and advisory.

Any resulting candidate data is handled by the ingestion pipeline as data,
not as authority.

## Candidate data

The result of AI-assisted ingestion is candidate canonical data.

Candidate data may be:

- complete;
- incomplete;
- ambiguous;
- structurally incorrect;
- semantically incorrect;
- inconsistent with the canonical schema.

None of these conditions are resolved by treating the AI output as
authoritative.

Candidate data must remain distinguishable from accepted canonical data
until validation succeeds.

## Mandatory deterministic validation gate

Every candidate record produced through AI-assisted ingestion must pass the
canonical validation layer before becoming part of the canonical dataset.

The validation layer defined by:

`docs/offer-validation.md`

is the mandatory acceptance gate.

Conceptually:

external source
→ ingestion
→ optional AI assistance
→ candidate canonical data
→ deterministic validation
→ canonical dataset

No alternative path may promote AI output directly into the canonical
dataset.

## Validation authority

The deterministic validation layer is authoritative for schema conformity.

AI assistance cannot:

- declare a record valid;
- override a validation failure;
- suppress a validation error;
- reinterpret a schema constraint;
- introduce additional canonical schema rules.

A record rejected by deterministic validation remains non-canonical unless
it is explicitly transformed and validated again.

## Determinism

The deterministic portions of ingestion and validation must remain
independent of AI availability.

When AI is not used, deterministic ingestion must retain its defined
semantics.

When AI is used, the AI-produced candidate remains subject to the same
canonical validation contract.

AI availability, provider selection, model selection, model version, or
runtime configuration must not alter the semantics of the canonical schema.

## Provenance and evidence

AI-assisted transformations must preserve sufficient provenance to identify:

- the external source;
- the source observation;
- the ingestion path;
- whether AI assistance was used;
- the candidate transformation where applicable.

AI-generated content must not be represented as source evidence merely
because the AI produced it.

Source evidence and AI-derived candidate content remain distinct.

## Error handling

AI-assisted ingestion must not silently convert uncertainty into canonical
truth.

When AI assistance produces ambiguous or incomplete candidate data, the
ingestion layer must preserve the candidate state or reject it according to
the deterministic ingestion contract.

Validation failures must remain observable.

No automatic repair is implied by AI assistance.

## Semantic boundary

AI-assisted ingestion does not determine:

- whether an offer is economically attractive;
- whether an offer is currently active;
- whether a product is equivalent to another product;
- whether source evidence is trustworthy;
- whether a retailer is preferable;
- whether a candidate should be recommended;
- whether a canonical record is true in the real world.

These concerns remain outside the AI-assisted canonical ingestion boundary.

## Relationship with canonical processing layers

The ingestion boundary precedes deterministic canonical processing.

The intended pipeline is:

external source
→ ingestion
→ candidate canonical records
→ validation
→ canonical dataset
→ filtering
→ aggregation
→ profiling
→ summary or other consumers

Validation establishes structural conformity.

Filtering selects records.

Aggregation groups and counts records.

Profiling describes structural distributions.

None of these downstream layers delegates canonical authority to AI.

## Architectural dependency direction

The dependency direction is:

`external source → ingestion → canonical validation → canonical consumers`

Optional AI assistance is a dependency of ingestion only:

`ingestion → optional GiadaWare AI`

The canonical validation, filtering, aggregation, and profiling layers must
not depend on the AI runtime.

The AI runtime must not become a prerequisite for reading, validating,
filtering, aggregating, or profiling canonical data.

## No direct AI-to-canonical persistence

AI output must never be persisted as canonical data without passing through
the deterministic validation boundary.

The following path is forbidden:

`external source → AI → canonical dataset`

The required path is:

`external source → AI → candidate data → validation → canonical dataset`

The same validation requirement applies when candidate data is produced
without AI assistance.

## Explicit non-goals

This boundary does not implement:

- an AI agent;
- autonomous retailer interaction;
- autonomous data acquisition;
- automatic schema discovery;
- automatic schema modification;
- automatic repair of invalid records;
- semantic truth determination;
- product matching;
- deal scoring;
- recommendation logic;
- persistence;
- GUI;
- AI-generated authoritative conclusions.

## Future implementation contract

An implementation of AI-assisted canonical ingestion must provide a clear
boundary between:

1. source acquisition;
2. deterministic transformation;
3. optional AI assistance;
4. candidate canonical data;
5. deterministic validation;
6. accepted canonical data.

The implementation must make it possible to test the deterministic validation
gate independently of the AI provider.

The system must remain usable and testable without a running AI service when
the selected ingestion path does not require AI assistance.

## Canonical rule

The architectural rule for this boundary is:

> AI may assist ingestion, but AI never establishes canonical authority.

The canonical dataset is established only by deterministic software operating
under the canonical contract.
