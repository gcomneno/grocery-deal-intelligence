# ALDI store-scoped capture spike

## Status

Issue #74.

Decision: **watch** — store context is proven to exist and influence public product/category availability, but a reproducible store-scoped offer retrieval request is not yet pinned.

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

Observed public server-rendered selected-store context:

```text
Negozio selezionato: 37057, San Giovanni Lupatoto
```

The selected-store value is visible not only on store-finder pages but also on product/category surfaces. A category response under that context can state:

```text
Questa categoria non è disponibile per il commerciante selezionato.
```

This is direct evidence that returned category/product availability is evaluated against server-visible selected-merchant context rather than being purely global.

A public store surface also identifies ALDI Camposampiero at:

```text
Via Borgo Padova 80
35012 Camposampiero PD
```

and ALDI public store URLs expose stable-looking store identities in their routes/pages.

## Trace outcome

The public HTTP/HTML evidence available in this spike proves that:

1. selected-store state exists;
2. the server-rendered response is aware of it;
3. the state can affect whether a category is available;
4. global and weekly-offer pages remain publicly retrievable and expose strong product facts.

However, the inspected public request URLs do **not** reveal a deterministic store selector in path or query parameters. The same selected-store state appears on multiple otherwise global URLs.

The exact transport therefore remains unresolved. Plausible mechanisms include:

- cookie/session value;
- embedded application state;
- internal public request parameter;
- another client-side context mechanism.

This spike did not obtain a trustworthy browser network trace exposing that state transition. Container-level direct network access was unavailable, and no attempt was made to bypass that limitation or infer hidden request values.

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
- weekly/current-next-week campaign cadence.

ALDI's official weekly-offer surface also states that most promotions are national while local product availability may vary by store.

### Proven about store context

- ALDI supports a selected-store state;
- server-rendered pages can expose the selected store;
- selected-store context affects category/product availability;
- stores have public identity/address surfaces.

### Not proven for one captured offer

- that a specific globally rendered offer applies to one selected store;
- the exact cookie/query/state key carrying store identity;
- a replayable raw request/response pair whose store scope can be independently reproduced;
- a store-scoped raw offer response suitable for hashing.

## Why no synthetic dataset is committed

Combining a global product row with an independently observed selected store would fabricate provenance.

The required dataset is:

```text
one retrieval
+ explicit reproducible store context
+ offer payload
```

not:

```text
global offer
+ store observed elsewhere
```

Therefore no fake `store_id`, inferred applicability, or synthetic store-scoped capture is added.

## Decision

**WATCH**

ALDI remains one of the strongest source candidates in the discovery set because public product richness and real store-specific availability semantics are both established.

The blocker is narrow but fundamental: Grocery Deal Intelligence must be able to reproduce the store-context transport itself before treating an offer capture as store-scoped evidence.

Promotion to adapter implementation requires one future trace that records:

- selected store identity;
- exact public state carrier (URL/query/cookie/request field or equivalent);
- one request made under that explicit context;
- raw response;
- retrieval timestamp;
- SHA-256;
- at least one stable article/offer identifier.

Until then, global ALDI product/offers may be useful as global evidence, but must not be promoted to store-specific canonical locality claims.
