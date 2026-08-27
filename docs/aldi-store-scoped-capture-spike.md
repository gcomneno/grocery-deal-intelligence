# ALDI store-scoped capture spike

## Status

Issue #74.

Current decision: **store context is proven to exist, but a reproducible store-scoped offer retrieval request is not yet pinned**.

No production adapter is introduced by this spike.

## Objective

Pin one deterministic ALDI retrieval surface and capture one real offer dataset whose selected-store scope is proved by the source itself.

## Public retrieval surfaces confirmed

The following official public surfaces are reproducible without authentication:

- `https://www.aldi.it/prodotti`
- `https://www.aldi.it/tools/features/prossimi-aldi-finds`
- `https://www.aldi.it/volantino-online`
- individual product pages such as `https://www.aldi.it/prodotto/philadelphia-philadelphia-original-000000000000298390`

The catalog and product pages expose canonical-relevant facts directly in server-readable HTML, including product name, package quantity, current price, unit/reference price, discount percentage, previous price where present, and availability start date where applicable.

Observed real product example:

```text
article id: 000000000000298390
product: Philadelphia Original
package: 0.22 kg
unit price: 8.59 EUR / kg
promotion: 20% discount
current price: 1.89 EUR
previous price: 2.39 EUR
```

This establishes a strong public product/offer surface, but does not by itself establish store applicability.

## Store-context evidence

ALDI's public site explicitly renders a selected-store state and tells users they can change store to see specific offers.

Observed selected-store context from public indexed pages:

```text
selected store locality: 37057 San Giovanni Lupatoto
```

A public store page also exposes:

```text
ALDI San Giovanni Lupatoto
Via Ca' Nova Zampieri snc
37057 San Giovanni Lupatoto
```

Separately, ALDI store URLs use stable-looking terminal identifiers such as `/h038` for a store page.

A category page observed under selected-store context can return:

```text
Questa categoria non è disponibile per il commerciante selezionato.
```

That is direct evidence that product/category availability is evaluated against a selected merchant/store context rather than being purely global.

## Critical unresolved mechanism

The inspected static offer/product URLs do **not** encode the selected store in an obvious query/path parameter.

The selected-store state therefore appears to be carried by one of:

- cookie/session state;
- embedded frontend state;
- a request parameter to an internal public endpoint;
- another client-side context mechanism.

This spike has not yet established which mechanism is authoritative.

No store applicability claim may therefore be attached to a globally retrieved offer merely because a store was visible elsewhere in the browsing session.

## Deterministic distinction

### Proven globally

For observed public product rows/pages:

- product identity;
- numeric article identifier;
- packaging/quantity;
- current price;
- unit/reference price;
- previous price where present;
- discount percentage where present;
- availability start date where present;
- weekly campaign cadence.

### Proven about store context

- ALDI supports a selected-store state;
- selected-store context changes which categories/offers are available;
- stores have public identity/address surfaces.

### Not yet proven for a captured offer

- that a specific global offer applies to the selected store;
- the exact store-context request parameter/value;
- a deterministic store-scoped offer response suitable for hashing and replay.

## Why no synthetic dataset is committed

Combining a global product row with an independently observed selected store would fabricate provenance.

The required dataset is:

```text
one retrieval
+ explicit store context
+ offer payload
```

not:

```text
global offer
+ store observed elsewhere
```

Therefore no fake `store_id` or inferred applicability is added to the captured product example.

## Next technical gate

Use a real browser/network trace against the public ALDI site while changing the selected store, and record only the public request(s) whose parameters or state deterministically carry store identity into product/offer retrieval.

The successful capture must preserve:

- request URL;
- request method;
- relevant public query/cookie/context value;
- selected store identity;
- retrieval timestamp;
- raw response;
- SHA-256;
- at least one offer/article identifier.

No authentication, anti-bot bypass, consent bypass, or hidden credential extraction is allowed.

## Current recommendation

**CONTINUE SPIKE — not ready for adapter implementation yet.**

ALDI remains a strong candidate because the product data surface and store-specific availability semantics are both real. The remaining blocker is narrow and technical: pinning the deterministic store-context transport so a store-scoped raw response can be reproduced and hashed.
