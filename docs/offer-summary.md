# Deterministic Canonical Offer Summary

## Purpose

The canonical offer summary layer provides deterministic, retailer-independent
derived facts over canonical grocery offer datasets.

The summary layer consumes canonical records and does not depend on retailer
adapter implementation details.

The summary describes the dataset. It does not evaluate the offers.

## Input

A summary operation receives a collection of retailer-neutral grocery offer
records.

The canonical record structure is defined by:

`schema/grocery-offer-v0.1.schema.json`

## Derived facts

Version 0.1 derives:

- total offer count;
- distinct retailers;
- offer count per retailer;
- distinct currencies;
- minimum price;
- maximum price;
- promotion type distribution;
- loyalty-required offer count;
- locality scope distribution;
- locality verification status distribution;
- evidence verification status distribution;
- count of offers with a reference price;
- count of offers with base-price text.

## Determinism

The same canonical dataset must always produce the same summary.

Source record ordering must not affect the summary.

Where collections are exposed in the summary, their ordering must itself be
deterministic.

## Price semantics

`minimum_price` and `maximum_price` are derived directly from the canonical
`price` field.

They are descriptive numeric extrema only.

They do not represent:

- cheapest product;
- best deal;
- greatest saving;
- better retailer;
- product-to-product price comparison.

If the dataset contains multiple currencies, price extrema must not be
interpreted as comparable across currencies.

## Promotion semantics

Promotion distributions are derived directly from:

`promotion.type`

The loyalty-required count is derived directly from:

`promotion.requires_loyalty`

No interpretation of promotion types is performed.

## Locality semantics

Locality distributions are derived directly from:

`locality.scope`

Locality verification status is derived directly from:

`verification.locality_status`

No additional geographic inference is performed.

## Verification semantics

Evidence verification distribution is derived directly from:

`verification.evidence_status`

The summary does not determine whether evidence is actually trustworthy.
It reports the canonical verification status.

## Optional-value semantics

Reference-price availability is counted when:

`reference_price` is not `null`

Base-price-text availability is counted when:

`base_price_text` is not `null`

No numeric or semantic interpretation of `base_price_text` is performed.

## Read-only boundary

Summary execution:

- must not modify source records;
- must not modify the source dataset;
- must not perform network access;
- must not invoke retailer adapters;
- must not access retailer-specific raw evidence.

## Architectural boundary

Retailer adapters produce canonical data.

The query layer consumes canonical data.

The summary layer consumes canonical data and produces deterministic derived
facts.

The summary layer must remain independent from:

- Lidl adapter implementation;
- Esselunga adapter implementation;
- retailer-specific acquisition endpoints;
- retailer-specific raw evidence;
- campaign/store resolution logic;
- persistence;
- AI services.

## Semantic boundary

The summary layer describes canonical data.

It does not evaluate or interpret offers.

Version 0.1 does not implement:

- product matching;
- fuzzy search;
- semantic search;
- unit normalization;
- price-per-unit comparison;
- cross-product price comparison;
- deal scoring;
- recommendation logic;
- automatic acquisition;
- persistence;
- GUI;
- AI-generated conclusions.

## Future AI integration

A future AI consumer may consume the structured deterministic summary.

Such integration must remain outside the deterministic summary core.

The presence, absence, model, runtime, or configuration of an AI service must
not change the deterministic summary.

AI output is advisory data and is not authoritative over the canonical data
or the deterministic summary.
