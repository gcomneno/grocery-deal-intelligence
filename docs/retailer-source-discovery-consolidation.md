# Retailer source-discovery consolidation

## Status

Final consolidation for #98 and parent discovery #64.

The retailer-discovery phase is complete for the investigated cohort. No additional retailer discovery is required before adapter work.

## Decision classes

### `promote_to_adapter_implementation`

These retailers already have store-scoped captured evidence plus deterministic parser work sufficient to move directly into adapter implementation:

- **Despar**
- **Carrefour**

### `promote_to_adapter_spike`

These retailers have promising official source surfaces and sufficiently strong locality/promotion semantics to justify focused adapter/retrieval spikes, but not yet production adapter implementation:

- **Conad**
- **MD**
- **Eurospin**
- **Todis**
- **Pam / Panorama**
- **Bennet**

For each of these, the missing gate is a reproducible source contract proving the store/locality binding of one offer/flyer response without inference.

### `watch`

These retailers remain valuable but are blocked by unresolved retrieval, locality, or usage-contract questions:

- **ALDI** — rich public product and weekly-offer data; selected-store semantics are real, but the exact replayable store-context transport is still unresolved.
- **Coop / Unicoop Etruria** — strong locality-aware promotion semantics, but a replayable locality-context transport has not been pinned.
- **PENNY** — unusually rich public product/offer data and explicit loyalty-aware pricing, but the stable delivery/locality contract and usage/legal boundary remain unresolved.

## Evidence hierarchy reached

The discovery work now distinguishes three materially different engineering states:

```text
captured store-scoped evidence + deterministic parser
        -> promote_to_adapter_implementation

strong official locality/source semantics, retrieval not yet pinned
        -> promote_to_adapter_spike

valuable source, but a fundamental source-contract/locality/usage gate remains
        -> watch
```

No retailer is promoted merely because its public page is rich or scrapeable.

## Canonical boundaries preserved

The following invariants remain binding for all future adapter work:

```text
visible offer != store applicability
selected store elsewhere != provenance for a global offer
publicly accessible != automatically reusable
AI output != authority
```

A store-scoped source requires one deterministically reproducible evidence chain connecting store identity/context to the exact offer/flyer payload.

No production adapter may fabricate locality by combining unrelated observations.

## Ranking for next engineering work

The next phase is not more discovery. It is adapter work, prioritized by evidence maturity.

Recommended order:

1. **Despar adapter implementation**
2. **Carrefour adapter implementation**
3. evaluate the first `promote_to_adapter_spike` candidate based on implementation value and retrieval risk
4. keep ALDI, Coop and PENNY on watch until their explicit promotion gates are satisfied

Despar and Carrefour come first because they already crossed the hardest deterministic evidence boundary: real store-scoped capture suitable for hashing/replay plus deterministic parser behavior.

## Discovery closure

The investigated retailer cohort is broad enough to stop source hunting. Parent #64 can be closed once this consolidation lands on `main`.

The next operational phase is:

```text
SOURCE DISCOVERY COMPLETE
        ↓
select adapter target
        ↓
implement deterministic retailer adapter
        ↓
source evidence projection
        ↓
validation / verification / admission
```

## Non-goals

This consolidation introduces no scraper, retailer adapter, schema change, AI change, admission-policy change, inferred locality, loyalty harvesting, personalized-offer harvesting, or access-control bypass.
