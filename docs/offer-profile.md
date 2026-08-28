# Deterministic Canonical Offer Dataset Profiling

## Purpose

The canonical offer dataset profiling layer provides a deterministic,
retailer-independent structural profile of a canonical grocery offer dataset.

The profiling layer consumes canonical records and describes their structural
distribution.

Profiling describes the dataset. It does not evaluate the offers.

## Input

A profiling operation receives a collection of retailer-neutral grocery offer
records.

The canonical record structure is defined by:

`schema/grocery-offer-v0.1.schema.json`

## Profile

Version 0.1 provides the following deterministic profile dimensions:

- total record count;
- retailer distribution;
- currency distribution;
- promotion type distribution;
- loyalty requirement distribution;
- locality scope distribution;
- locality verification status distribution;
- evidence verification status distribution;
- reference price presence distribution;
- base price text presence distribution.

These dimensions are derived directly from canonical record fields or from
deterministic presence checks defined by the canonical contract.

## Semantics

`total_records` is the number of records supplied to the profiling operation.

Distribution dimensions count records according to their canonical values.

`reference_price` means an ordinary/original numeric comparison price for the current offer price; unit prices are a distinct concept.

For optional-value presence dimensions:

- `reference_price` is `present` when `reference_price` is not `null`;
- `reference_price` is `absent` when `reference_price` is `null`;
- `base_price_text` is `present` when `base_price_text` is not `null`;
- `base_price_text` is `absent` when `base_price_text` is `null`.

No normalization, inference, interpretation, or semantic classification is
performed.

## Result

The profile is a deterministic structured result containing the total record
count and the supported distributions.

Distribution group ordering must be deterministic.

The profile must not depend on source record ordering.

Each distribution must account for every input record exactly once.

Therefore, for every distribution:

`sum(group counts) == total_records`

## Empty datasets

An empty canonical dataset is a valid input to the profiling operation.

For an empty dataset:

- `total_records` is `0`;
- every distribution contains zero groups.

No synthetic category is introduced to represent an empty dataset.

## Determinism

The same canonical dataset must always produce the same profile.

Changing the source record ordering must not change:

- total record count;
- group counts;
- group ordering.

The profiling operation must not depend on incidental dictionary, hash, or
input iteration ordering.

## Read-only boundary

Profiling:

- must not modify source records;
- must not modify the source dataset;
- must not perform network access;
- must not invoke retailer adapters;
- must not access retailer-specific raw evidence.

Profiling is observational only.

## Semantic boundary

Profiling answers only:

> What is the deterministic structural distribution of this canonical dataset?

It does not answer:

- whether an offer is good;
- whether an offer is currently active;
- whether a retailer is better;
- whether a promotion is valuable;
- whether a price is advantageous;
- whether evidence is trustworthy;
- whether two products are equivalent;
- whether the dataset is commercially successful.

Schema conformity must not be confused with real-world correctness, and
structural distribution must not be confused with evaluation.

## Architectural boundary

Retailer adapters produce canonical data.

The validation layer verifies canonical data.

Query, filtering, aggregation, summary, and profiling operate on canonical
data without depending on retailer-specific implementation details.

The profiling layer must remain independent from:

- Lidl adapter implementation;
- Esselunga adapter implementation;
- retailer-specific acquisition endpoints;
- retailer-specific raw evidence;
- campaign/store resolution logic;
- persistence;
- AI services.

## Relationship with existing deterministic layers

The validation layer establishes structural conformity against the canonical
schema.

The query layer performs deterministic text search.

The filtering layer performs deterministic record selection.

The aggregation layer groups and counts records by a supported canonical
dimension.

The summary layer derives deterministic descriptive facts.

The profiling layer provides a deterministic structural overview of the
dataset.

These capabilities may be composed without changing the semantics of the
underlying canonical records.

Conceptually:

canonical dataset
→ validate
→ filter / query
→ aggregate
→ profile / summary

Profiling does not alter the dataset.

## Explicit non-goals

Version 0.1 does not implement:

- quality scoring;
- deal scoring;
- retailer ranking;
- price ranking;
- recommendation logic;
- product matching;
- deduplication;
- fuzzy search;
- semantic search;
- unit normalization;
- price-per-unit comparison;
- cross-product price comparison;
- temporal validity interpretation;
- automatic data acquisition;
- persistence;
- GUI;
- AI-generated conclusions.

## Future AI integration

A future AI consumer may receive deterministic dataset profiles or summaries
derived from canonical records.

Such integration remains outside the deterministic profiling core.

The presence, absence, model, runtime, or configuration of an AI service must
not change profiling results.

AI output is advisory data and is not authoritative over canonical records,
canonical schema, or deterministic profiling results.
