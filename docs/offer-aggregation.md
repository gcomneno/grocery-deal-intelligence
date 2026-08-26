# Deterministic Canonical Offer Aggregation

## Purpose

The canonical offer aggregation layer provides deterministic, retailer-independent
grouping and counting of canonical grocery offer records.

The aggregation layer consumes canonical records and does not depend on retailer
adapter implementation details.

Aggregation describes the distribution of canonical records. It does not
evaluate the offers.

## Input

An aggregation operation receives:

- a collection of retailer-neutral grocery offer records;
- one supported canonical dimension.

The canonical record structure is defined by:

`schema/grocery-offer-v0.1.schema.json`

## Supported dimensions

Version 0.1 supports aggregation by:

- `retailer`;
- `currency`;
- `promotion.type`;
- `promotion.requires_loyalty`;
- `locality.scope`;
- `verification.locality_status`;
- `verification.evidence_status`;
- presence of `reference_price`;
- presence of `base_price_text`.

These dimensions are derived directly from canonical record fields.

No additional semantic dimensions are introduced.

## Aggregation semantics

Aggregation counts records for each distinct value of the selected dimension.

For a direct canonical field, the group value is the canonical value itself.

For optional-value presence dimensions:

- `reference_price` is `present` when `reference_price` is not `null`;
- `reference_price` is `absent` when `reference_price` is `null`;
- `base_price_text` is `present` when `base_price_text` is not `null`;
- `base_price_text` is `absent` when `base_price_text` is `null`.

No numeric or semantic interpretation of these optional fields is performed.

## Result

An aggregation operation produces a deterministic structured result containing:

- the selected dimension;
- the groups for that dimension;
- the number of canonical records in each group.

Group ordering must be deterministic.

The result must not depend on source record ordering.

## Multiple values

Each canonical record contributes exactly one count to the selected dimension.

No record is duplicated or discarded by aggregation.

Aggregation does not deduplicate records.

Two records with identical field values remain two records.

## Boolean dimensions

For `promotion.requires_loyalty`, aggregation uses the canonical boolean
values directly.

`true` and `false` are distinct groups.

No interpretation of loyalty requirements is performed.

## Read-only boundary

Aggregation:

- must not modify source records;
- must not modify the source dataset;
- must not perform network access;
- must not invoke retailer adapters;
- must not access retailer-specific raw evidence.

Aggregation is observational only.

## Determinism

The same canonical dataset must always produce the same aggregation result for
the same dimension.

Source record ordering must not affect group counts or group ordering.

The aggregation operation must not depend on incidental dictionary, hash, or
input iteration ordering.

## Semantic boundary

Aggregation answers only:

> How many canonical records belong to each value of this canonical dimension?

It does not answer:

- whether a group is better;
- whether a group is more advantageous;
- whether one retailer is better than another;
- whether a promotion is valuable;
- whether loyalty requirements are preferable;
- whether a price is cheap or expensive;
- whether evidence is trustworthy.

Aggregation is descriptive, not evaluative.

## Architectural boundary

Retailer adapters produce canonical data.

The aggregation layer consumes canonical data.

The aggregation layer must remain independent from:

- Lidl adapter implementation;
- Esselunga adapter implementation;
- retailer-specific acquisition endpoints;
- retailer-specific raw evidence;
- campaign/store resolution logic;
- persistence;
- AI services.

## Relationship with query, filtering, validation, and summary layers

The validation layer verifies structural conformity against the canonical schema.

The query layer performs deterministic text search.

The filtering layer performs deterministic record selection.

The aggregation layer groups and counts records by a supported canonical
dimension.

The summary layer derives deterministic descriptive facts from canonical
records.

These capabilities may be composed without changing the semantics of the
underlying canonical records.

Conceptually:

canonical dataset
→ validate
→ filter
→ aggregate
→ summary

Query may independently select records before aggregation.

Composition does not imply evaluation or recommendation.

## Explicit non-goals

Version 0.1 does not implement:

- product matching;
- deduplication;
- fuzzy search;
- semantic search;
- unit normalization;
- price-per-unit comparison;
- cross-product price comparison;
- price ranking;
- deal scoring;
- recommendation logic;
- temporal validity interpretation;
- automatic data acquisition;
- persistence;
- GUI;
- AI-generated conclusions.

## Future AI integration

A future AI consumer may receive deterministic aggregation results or summaries
derived from them.

Such integration remains outside the deterministic aggregation core.

The presence, absence, model, runtime, or configuration of an AI service must
not change aggregation results.

AI output is advisory data and is not authoritative over canonical records or
deterministic aggregation results.
