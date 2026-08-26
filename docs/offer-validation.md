# Deterministic Canonical Offer Dataset Validation

## Purpose

The canonical offer dataset validation layer provides deterministic validation
of retailer-neutral grocery offer records against the canonical offer contract.

The validation layer verifies structural and schema conformity.

Validation reports conformity. It does not evaluate the meaning or quality of
an offer.

## Input

A validation operation receives a collection of retailer-neutral grocery offer
records.

The canonical record structure is defined by:

`schema/grocery-offer-v0.1.schema.json`

## Validation semantics

Version 0.1 validates each record against the canonical schema.

Validation includes the constraints defined by the schema, including:

- required properties;
- property types;
- nested object structure;
- allowed additional properties;
- string constraints;
- numeric constraints;
- enumerated values;
- array constraints;
- nullable fields;
- required nested properties.

The validation layer must use the canonical schema as its authoritative
structural contract.

No additional semantic rules are introduced.

## Result

Validation produces a deterministic structured result containing:

- whether the dataset is valid;
- total record count;
- valid record count;
- invalid record count;
- structured validation errors.

A valid dataset contains zero validation errors.

An invalid dataset contains one or more validation errors.

Validation errors identify, where available:

- the record position;
- the canonical field path;
- the violated schema constraint.

Error ordering must be deterministic and must not depend on incidental source
ordering beyond the identity of the records being validated.

## Dataset ordering

Validation must not change the ordering of the source dataset.

The validation result must not depend on source record ordering when the same
records are supplied in a different order, except for record-position
information used to identify the location of an invalid record.

The validation operation must not sort, rewrite, or otherwise transform the
source records.

## Read-only boundary

Validation:

- must not modify source records;
- must not modify the source dataset;
- must not perform network access;
- must not invoke retailer adapters;
- must not access retailer-specific raw evidence.

Validation is observational only.

## No automatic repair

Version 0.1 does not modify invalid records.

The validation layer must not:

- normalize values;
- repair missing fields;
- coerce types;
- remove unknown properties;
- rewrite invalid values;
- infer missing information.

An invalid record remains unchanged.

## Semantic boundary

Validation answers only:

> Does this record conform to the canonical schema?

It does not answer:

- whether an offer is good;
- whether an offer is valid in the real world;
- whether an offer is currently active;
- whether evidence is trustworthy;
- whether a price is advantageous;
- whether two products are equivalent;
- whether one retailer is better than another.

Schema conformity must not be confused with real-world correctness.

## Architectural boundary

Retailer adapters produce canonical data.

The validation layer verifies canonical data.

The validation layer must remain independent from:

- Lidl adapter implementation;
- Esselunga adapter implementation;
- retailer-specific acquisition endpoints;
- retailer-specific raw evidence;
- campaign/store resolution logic;
- persistence;
- AI services.

## Relationship with query, filtering, and summary layers

The validation layer establishes structural conformity of canonical records.

The query layer performs deterministic text search.

The filtering layer performs deterministic record selection.

The summary layer derives deterministic descriptive facts.

These capabilities operate on the same canonical contract and may be composed
without changing the semantics of the canonical records.

Conceptually:

canonical dataset
→ validate
→ conforming dataset
→ query / filter / summary

Validation does not alter the dataset.

## Explicit non-goals

Version 0.1 does not implement:

- automatic repair;
- normalization;
- type coercion;
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

A future AI consumer may consume validated canonical records or deterministic
validation results.

Such integration remains outside the deterministic validation core.

The presence, absence, model, runtime, or configuration of an AI service must
not change validation results.

AI output is advisory data and is not authoritative over the canonical schema,
canonical records, or deterministic validation results.
