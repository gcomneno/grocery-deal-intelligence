# PENNY official offers source spike

## Status

Research result for Issue #66.

## Decision

`watch`

PENNY exposes one of the richest official public offer surfaces found so far, but this spike does **not** promote it to automated ingestion yet.

Two blockers remain:

1. the exact frontend data-delivery mechanism behind the public offer pages was not independently verified as a stable documented or undocumented structured endpoint;
2. PENNY's published site terms materially restrict reuse/reproduction of site content and therefore require a legal/permission review before automated retrieval is treated as an acceptable production source.

The source should remain high-priority on the watchlist rather than being rejected.

## Official source surfaces inspected

Primary public surfaces:

- `https://www.penny.it/offerte`
- `https://www.penny.it/categorie/tutte-le-offerte-99000000`
- category pages such as `https://www.penny.it/categorie/alimentari-684`
- campaign/category pages such as `https://www.penny.it/categorie/volantino-27-agosto-prezzi-fermi`

Observed public navigation also exposes pagination and sorting parameters, for example:

- `?page=2`
- `?sortBy=price&sortOrder=asc`

These are frontend navigation surfaces, not yet accepted as a stable ingestion API contract.

## Product-level evidence richness

Observed public offer cards expose many canonical-relevant facts directly in page content:

- product name;
- brand where available;
- package quantity and unit;
- offer validity `from` / `to` dates;
- promotional/current price;
- previous/base price for discount offers;
- percentage discount for many offers;
- unit/reference price;
- quantity-limited marker;
- PENNYCard-specific pricing where applicable;
- non-card price where applicable;
- category/campaign grouping.

Examples observed on the official public surface include products with dual `Senza PENNYCard` / `Con PENNYCard` prices and products with explicit crossed-out previous prices.

This is materially richer than a flat flyer image or PDF.

## Product identity

Product links expose stable-looking numeric identifiers in canonical public URLs, for example:

```text
/prodotto/gran-pesto-radicchio-e-speck-11100977
/prodotto/salsa-di-pomodoro-datterino-11104374
```

These identifiers are promising evidence candidates for product/offer identity, but stability across campaign cycles has not yet been demonstrated. They must therefore be treated as observed identifiers, not guaranteed permanent IDs.

## CMS / delivery observations

PENNY public assets are served from a Kontent.ai/Kentico asset domain:

```text
assets-eu-01.kc-usercontent.com
```

Observed asset URLs repeatedly contain the same UUID-like segment:

```text
d49cd34d-2aa0-0177-a7ec-f52a295434d9
```

Third-party technology inventories also identify `penny.it` as a Kontent.ai user.

This strongly suggests a headless/content-delivery architecture, but the spike did **not** establish the exact product/offer delivery endpoint or prove that the UUID segment is a public Delivery API environment identifier for the offer catalogue.

Therefore:

```text
Kontent.ai-backed source architecture -> observed/strongly supported
exact offer API endpoint              -> not established
stable API contract                   -> not established
```

No guessed Delivery API URL is promoted to evidence.

## Locality semantics

The global offers/category surfaces inspected do not expose an explicit store identifier on each offer card.

PENNY also publishes store/volantino pages, but this spike did not establish a deterministic mapping between the global offer catalogue and a specific point of sale.

Therefore locality remains unresolved for automated canonical admission:

```text
global public offer -> visible
store applicability -> not established from inspected offer rows
```

No assumption such as `national` is allowed.

## Loyalty semantics

PENNY is unusually strong here.

The public offer surface explicitly distinguishes:

```text
Senza PENNYCard
Con PENNYCard
```

with separate prices and, for some products, separate unit prices.

This can support deterministic future mapping of loyalty-dependent promotions if a source contract is approved. No AI inference is required for the existence of the loyalty condition where this distinction is explicit.

## Freshness and campaign structure

Observed offer pages carry explicit validity intervals and campaign/category pages for specific flyer periods.

The public source currently exposes overlapping campaigns/current and upcoming offers. This is useful for reproducible temporal evidence, but update cadence has not yet been measured longitudinally.

## Access and reproducibility

The source is publicly readable without authentication for the inspected offer/category pages.

No authentication bypass, anti-bot bypass, or access-control circumvention was attempted.

The spike did not establish a documented public API.

## Terms / legal constraint

PENNY's official `Termini di utilizzo` state that site materials and contents are owned by PENNY/REWE and protected by intellectual-property rights. The terms state that access does not grant a right to appropriate, reproduce, modify, distribute, or republish site information without written authorization, while preserving the possibility to store and/or print information for exclusively personal use.

This creates a material boundary for Grocery Deal Intelligence:

- technical public accessibility is not equivalent to permission for automated reusable ingestion;
- a future production retrieval path should not be implemented until the intended personal/private usage model is reviewed against those terms or explicit permission/another lawful basis is established;
- the repository must not mirror or republish PENNY content as a dataset merely because it is technically obtainable.

## Canonical-relevant source matrix

| Fact | Status |
| --- | --- |
| product identity | strong observed candidate |
| product name | directly visible |
| brand | directly visible where present |
| current/promo price | directly visible |
| base/previous price | directly visible for many offers |
| reference/unit price | directly visible for many offers |
| validity interval | directly visible |
| percentage discount | directly visible for many offers |
| loyalty requirement | directly visible where PENNYCard split exists |
| quantity-limited promotion | directly visible |
| campaign/category | directly visible |
| store/locality scope | unresolved |
| stable structured endpoint | unresolved |
| documented API | not found |
| long-term identifier stability | unverified |

## Why the result is `watch`, not `reject`

PENNY remains technically one of the highest-value source candidates discovered:

```text
rich offer facts
+ explicit validity
+ explicit loyalty semantics
+ apparent product identifiers
+ public navigation/pagination
```

The decision is `watch` because the remaining blockers are source-contract and permission questions, not lack of useful data.

## Conditions for promotion

PENNY may be promoted to `promote_to_adapter_spike` only after both classes of evidence improve:

1. **technical**: identify and reproduce the actual offer delivery mechanism, or deliberately accept server-rendered official HTML as the source contract and verify stability across multiple campaign refreshes;
2. **usage/legal**: establish that the intended automated personal-use retrieval pattern is acceptable, or obtain an alternative permission/source basis.

Until then, no production scraper or adapter should be implemented.

## Architecture invariant

```text
publicly visible != automatically reusable
structured-looking != stable source contract
technically retrievable != canonical evidence authority
```
