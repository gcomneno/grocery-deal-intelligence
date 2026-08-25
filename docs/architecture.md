# Architecture

## Retailer adapters

Each retailer has its own discovery, resolution, extraction, semantic
verification, normalization, and export logic.

Retailer-specific implementation details must not leak into the canonical
retailer-neutral contract.

## Canonical boundary

All retailer-neutral offers are validated against:

`schema/grocery-offer-v0.1.schema.json`

The canonical validator uses:

`jsonschema.Draft202012Validator`

## Verification principle

The project follows:

`discover → resolve → extract → verify → normalize → validate`

The normalized dataset is an output of verified retailer-specific processing,
not a substitute for that verification.

## Cross-retailer regression

The canonical contract must be testable against datasets produced by more
than one retailer adapter.

The regression suite therefore verifies that different retailer datasets
satisfy the same schema and preserve their expected retailer identity.
