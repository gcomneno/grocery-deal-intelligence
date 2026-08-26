# Deterministic Canonical Offer Filtering

## Purpose

The canonical offer filtering layer provides deterministic, retailer-independent
selection of canonical grocery offer records.

The filtering layer consumes canonical records and does not depend on retailer
adapter implementation details.

Filtering selects records. It does not evaluate the selected offers.

## Input

A filtering operation receives:

- a collection of retailer-neutral grocery offer records;
- zero or more exact filters over canonical fields.

The canonical record structure is defined by:

`schema/grocery-offer-v0.1.schema.json`

## Supported filters

Version 0.1 supports exact filtering by:

- `retailer`;
- `locality.scope`;
- `verification.locality_status`;
- `verification.evidence_status`;
- `promotion.requires_loyalty`.

Filters are optional.

When a filter is omitted, that attribute places no restriction on the result.

## Filter semantics

All supported filters are exact comparisons against the corresponding
canonical value.

No:

- fuzzy matching;
- normalization;
- inference;
- ranking;
- scoring;
- recommendation;
- semantic interpretation

is performed.

The same filter semantics apply to Lidl, Esselunga, and future retailers.

## Multiple filters

When multiple filters are supplied, they are combined conjunctively.

A record is included only when it satisfies every supplied filter.

For example, a filter requiring:

- `retailer = "lidl"`;
- `locality.scope = "regional"`;
- `promotion.requires_loyalty = true`;

selects only records satisfying all three canonical conditions.

## Result ordering

The source dataset ordering must not affect the result ordering.

Results use the deterministic ordering established by the canonical query layer:

1. `retailer`;
2. `product_name`;
3. `price`;
4. `currency`.

Filtering therefore preserves no semantic meaning from source ordering.

## Validity

Version 0.1 does not define temporal filtering.

The canonical record contains:

`validity.from`

and:

`validity.to`

but these fields are not interpreted by the filtering layer.

In particular, Version 0.1 does not introduce:

- `active_at`;
- active-offer semantics;
- date-range overlap semantics;
- timestamp parsing;
- timezone conversion;
- calendar interpretation.

A future validity-filter capability requires a separate explicit contract.

## Read-only boundary

Filtering:

- must not modify source records;
- must not modify the source dataset;
- must not perform network access;
- must not invoke retailer adapters;
- must not access retailer-specific raw evidence.

The returned records remain canonical records.

## Architectural boundary

Retailer adapters produce canonical data.

The filtering layer consumes canonical data.

The filtering layer must remain independent from:

- Lidl adapter implementation;
- Esselunga adapter implementation;
- retailer-specific acquisition endpoints;
- retailer-specific raw evidence;
- campaign/store resolution logic;
- persistence;
- AI services.

## Relationship with query and summary layers

The filtering layer is a deterministic selection primitive.

The query layer performs deterministic text search.

The summary layer derives deterministic facts from canonical records.

These capabilities may be composed without changing the semantics of the
underlying canonical records.

Conceptually:

canonical records
→ filter
→ selected canonical records
→ query or summary

Composition does not imply evaluation or recommendation.

## Explicit non-goals

Version 0.1 does not implement:

- temporal validity interpretation;
- product matching;
- fuzzy search;
- semantic search;
- unit normalization;
- price-per-unit comparison;
- cross-product price comparison;
- deal scoring;
- recommendation logic;
- automatic data acquisition;
- persistence;
- GUI;
- AI-generated conclusions.

## Future AI integration

A future AI consumer may receive filtered canonical records or deterministic
summaries derived from them.

Such integration remains outside the deterministic filtering core.

The presence, absence, model, runtime, or configuration of an AI service must
not change filtering results.

AI output is advisory data and is not authoritative over canonical records or
deterministic filtering.
