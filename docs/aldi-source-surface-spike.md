# ALDI public offer source surface spike

## Status

Issue #67 discovery spike.

Decision: `promote_to_adapter_spike`.

No production scraper or adapter is implemented here.

## Official surfaces inspected

- `https://www.aldi.it/prodotti`
- `https://www.aldi.it/volantino-online`
- `https://www.aldi.it/speciali-della-settimana`
- product detail pages under `/it/p.<slug>.<article-id>.html`
- store/location-aware pages under `/liste/local-...`
- official ALDI Italia mobile app description

## Observed product/offer richness

The public product catalogue exposes canonical-relevant fields directly in rendered content, including:

- product/brand name;
- package quantity;
- current price;
- unit/reference price;
- previous price for discounted products;
- discount percentage for some products;
- explicit availability start date for weekly/special products;
- distinction between regular assortment and time-bounded special availability.

## Product identity

Product detail URLs carry stable-looking numeric article identifiers, for example:

```text
000000000000652299
000000000000601433
```

The same identifier is also rendered as `Codice articolo` on the product page.

The identifier format is therefore a strong candidate for deterministic source identity, subject to stability checks across multiple refreshes.

## Locality and store semantics

ALDI exposes multiple store-aware signals:

- product detail pages expose a `Ricerca disponibilità prodotto in filiale` function;
- the site exposes pages with a selected store and explicitly states that changing the store changes the offers shown;
- store finder pages expose individual stores, addresses, opening hours, and associated flyer access;
- the official ALDI Italia app advertises product availability checks at a preferred branch.

This is materially stronger locality evidence than a national-only flyer surface.

The public flyer FAQ also states that most promotions are national but some availability can vary by store. Therefore `national` MUST NOT be assumed blindly for every offer.

## Freshness and cadence

ALDI publishes current and next-week flyer/offer surfaces. The official flyer page states that offers are generally activated Monday, Thursday, and weekend, current and next-week offers are visible, dates are explicitly shown, and weekly offers are updated regularly.

## Structured source mechanism

This spike did **not** establish a documented public product API or a stable undocumented JSON endpoint as a source contract.

However, the following are established:

- product data is rendered in stable, repeatable product/detail/list pages;
- product IDs are embedded in canonical product URLs and visible in content;
- store selection and product availability are real public application features;
- the official app consumes the same domain of products, promotions, store selection, and product availability without requiring registration for the basic shopping flow.

A future adapter spike may therefore investigate either:

1. the network/data requests made by the public website/app, without bypassing access controls; or
2. deterministic extraction from public server-rendered product/list pages if no stable structured endpoint is available.

No endpoint stability claim is made here.

## Canonical evidence potential

| Canonical concern | ALDI public evidence |
| --- | --- |
| retailer | direct (`aldi`) |
| product identity/name | strong |
| price | strong |
| currency | implicit by euro-denominated official Italian surface; future rule must be explicit |
| reference/unit price | strong for many products |
| previous/base price | available for discounted rows |
| promotion discount | available for many discounted rows |
| validity start | strong for weekly/special products |
| validity end | generally flyer/week-derived rather than always product-row explicit |
| loyalty semantics | no comparable loyalty-card dependency observed in inspected rows |
| locality/store | strong store-selection and availability surface |
| provenance | strong official-retailer URL + article ID |
| verification | only after deterministic source rules are formalized |

## Legal/access notes

The inspected surfaces are official public ALDI pages and the official app advertises browsing promotions and checking branch availability as normal consumer features.

The site footer exposes `Condizioni di Utilizzo`, but this spike did not obtain a specific clause that clearly authorizes automated reuse. Therefore future automated retrieval still requires a focused terms/robots review before productionization.

No authentication, anti-bot mechanism, private API, or access-control bypass was used in this spike.

## Why ALDI is promoted

ALDI is promoted because the combination is unusually strong:

```text
public product catalogue
+ explicit prices
+ unit prices
+ discount/base-price evidence
+ explicit special availability dates
+ stable-looking article IDs
+ store selection
+ per-store availability feature
+ current/next-week cadence
```

The only major unresolved technical question is the exact best machine-readable retrieval mechanism.

That is a suitable question for an adapter spike, not a reason to keep the retailer in indefinite watch.

## Decision

```text
promote_to_adapter_spike
```

The adapter spike must remain conservative:

- identify and pin the exact retrieval surface;
- prove reproducibility and stable IDs;
- preserve store/locality context;
- capture freshness/provenance metadata;
- avoid assuming national applicability;
- keep source extraction deterministic;
- perform a terms/robots review before any production automation;
- fall back to `watch` if no stable retrieval surface can be established without fragile scraping.
