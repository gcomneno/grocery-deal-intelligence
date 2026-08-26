# Canonical Offer Query Layer

## Purpose

The canonical offer query layer provides deterministic, read-only queries over
retailer-neutral grocery offer datasets.

The query layer consumes canonical records and does not depend on retailer
adapter implementation details.

## Input

A query operation receives:

- a collection of retailer-neutral grocery offer records;
- a non-empty text query;
- an optional retailer filter.

The canonical record structure is defined by:

`schema/grocery-offer-v0.1.schema.json`

## Text search semantics

Version 0.1 searches only the canonical:

`product_name`

field.

Matching is:

- case-insensitive;
- substring-based;
- deterministic.

No fuzzy matching, token ranking, stemming, semantic similarity, or product
matching is performed.

Examples:

`ananas` matches:

`F.lli Orsero Ananas Tronchetto 500 g`

A query such as:

`orsero 500g`

does not imply that the implementation must match the same record.

## Retailer filtering

The optional retailer filter is an exact, case-sensitive match against the
canonical `retailer` field.

When omitted, records from all retailers are eligible.

The query layer must use the same semantics for Lidl, Esselunga, and future
retailers.

## Result ordering

Results must be returned in deterministic order.

Version 0.1 orders results lexicographically by:

1. `retailer`
2. `product_name`
3. `price`
4. `currency`

The source dataset ordering must not affect the result ordering.

## Read-only boundary

Query execution:

- must not modify source records;
- must not modify the source dataset;
- must not perform network access;
- must not invoke retailer adapters;
- must not access retailer-specific raw evidence.

## Explicit non-goals

Version 0.1 does not implement:

- product matching;
- fuzzy search;
- semantic search;
- unit normalization;
- price-per-unit comparison;
- price comparison;
- deal scoring;
- recommendation;
- data acquisition;
- persistence;
- GUI.

## Architectural boundary

Retailer adapters produce canonical data.

The query layer consumes canonical data.

The query layer must remain independent from retailer-specific acquisition,
resolution, extraction, verification, and normalization implementations.
