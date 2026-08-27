# Despar digital flyer source spike

## Status

Issue #68.

Decision: **promote_to_adapter_spike**.

No production adapter is introduced by this spike.

## Objective

Determine whether Despar official digital-flyer and point-of-sale surfaces provide a reproducible, store-scoped source suitable for deterministic grocery ingestion.

## Official public surfaces

Observed reproducible public surfaces include:

- store pages under `/it/punto-vendita-<brand>/<id>/<slug>/`;
- digital flyers under `/it/volantino-digitale/<id>/`;
- provincial store lists under `/it/i-nostri-punti-vendita/...`;
- promotion-specific pages such as `/it/sottocosto/`.

The site is operated for the inspected territory by Aspiag Service S.r.l., concessionaria del marchio Despar in Triveneto, Emilia-Romagna e Lombardia.

## Store identity and flyer identity

A particularly strong deterministic property is that the public numeric store identifier is reused across the point-of-sale and flyer URLs.

Observed example:

```text
store:
https://www.despar.it/it/punto-vendita-interspar/191/montebelluna/

flyer:
https://www.despar.it/it/volantino-digitale/191/
```

The store page identifies:

```text
Interspar Montebelluna (TV)
Via Schiavonesca Priula, 64
```

The flyer page itself renders:

```text
Montebelluna - Via Schiavonesca Priula, 64
```

Therefore the inspected flyer is directly store-scoped by the public URL and by content rendered on the flyer page itself. No cookie/session inference is required to establish this locality relationship.

## Offer richness

Despar digital flyer pages expose structured offer rows directly in server-readable page content.

Observed canonical-relevant facts include:

- product name/brand;
- package quantity or weight;
- current promotional price;
- unit/per-piece or per-kilogram price where applicable;
- previous price for some discounted products;
- percentage discount for some products;
- bundle mechanics;
- explicit campaign validity interval;
- store identity/locality on store-scoped flyer pages.

Observed promotion mechanics include:

```text
2+1 gratis
Sconto 10%
Sconto 25%
```

Example observed on current digital flyers:

```text
Filetti di alici distesi in olio di oliva Despar 90 g
1 pz. 3,19 EUR
3 pz. 6,38 EUR
Offerta pari a 2,13 EUR al pz.
Offerta 2+1 gratis
```

The page also exposes a single explicit campaign validity interval, for example:

```text
Valido dal 27.08.2026 al 10.09.2026
```

This is significantly stronger than a raster-only/PDF-only flyer source.

## Pagination and density

Observed flyers expose category filtering and multi-page offer listings. One inspected flyer reported `1 di 39`, demonstrating that the public page is not merely a small editorial teaser but a substantial product-offer surface.

## Locality semantics

Despar explicitly requires or displays a selected point of sale for offer surfaces in several parts of the site.

Observed public messaging includes:

```text
Nessun punto vendita impostato, scegline uno per vedere le offerte.
```

and, for store-scoped flyers, the store address is rendered directly on the flyer page.

This provides two levels of evidence:

1. global/site-wide offer features are locality-aware;
2. numeric store IDs can bind a specific public flyer to a specific store page.

That is materially stronger than session-only locality.

## Promotion and applicability caveats

The official rules state that some fresh-department offers are valid only in stores equipped with the relevant department, and that prices/articles are valid while stocks last.

Therefore a future adapter must not flatten all campaign rows into unconditional store-wide claims without preserving these applicability constraints when the source expresses them.

Affiliated Despar stores may also retain autonomy over discounts and initiatives. The retailer/operating-company/source boundary must therefore remain explicit rather than assuming one homogeneous national Despar contract.

## Deterministic evidence candidates

A future adapter spike should be able to establish, at minimum, the following from a store-scoped flyer page:

```text
retailer/brand context
store numeric id
store name/address
product description
package quantity
campaign valid_from
campaign valid_to
current price
unit/reference price where rendered
previous price where rendered
promotion mechanic text
percentage discount where rendered
source URL
observed_at
```

Fields not present in the rendered source must remain absent rather than inferred.

## Retrieval mechanism

The exact lower-level API/backend feeding the page has not yet been pinned.

However, unlike ALDI, the spike does not depend on discovering hidden session state to prove store scope: the public store and flyer URLs themselves provide deterministic locality identity.

Therefore the next technical step can start from the public HTML contract and only prefer a structured backend if a separate inspection proves it stable and appropriate.

## Access / legal boundary

This spike used public pages only and did not bypass authentication, anti-bot controls, consent mechanisms, or access restrictions.

A dedicated terms/robots review remains required before any recurring production retrieval is implemented.

## Recommendation

**promote_to_adapter_spike**

Rationale:

- store scope is deterministic and URL-addressable;
- product rows are rich and machine-readable in the public page response;
- validity is explicit;
- promotion mechanics are unusually well preserved;
- no session/cookie reconstruction is required to bind the inspected flyer to a store;
- unresolved questions are now implementation details rather than fundamental provenance blockers.

## Follow-up spike

Recommended next issue:

```text
Despar adapter spike:
capture and parse one store-scoped digital flyer fixture deterministically
```

The spike should preserve raw HTML/structured response evidence, content hash, store/flyer identity, validity interval, and a small deterministic parser proof without yet introducing production scheduling or broad retailer coverage.
