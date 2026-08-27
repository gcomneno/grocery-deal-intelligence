# Italian retailer source discovery

## Status

Initial evidence-backed source-discovery matrix for Issue #64.

This document ranks source surfaces, not retailers as businesses. A high rank means the currently observed official surface looks promising for deterministic ingestion and evidence projection. It does not imply that a stable undocumented API exists.

## Ranking summary

| Rank | Retailer | Observed official surface | Data richness | Locality | Recommendation |
| ---: | --- | --- | --- | --- | --- |
| 1 | PENNY | product-level offers page | very high | unclear from public offers page | `promote_to_spike` |
| 2 | ALDI | product catalogue + weekly offers | very high | mostly national / availability caveats | `promote_to_spike` |
| 3 | Despar | digital flyer with product-level offer rows | very high | strong store/territory orientation | `promote_to_spike` |
| 4 | Carrefour | online product promotions + store-specific flyer | high | strong store/location orientation | `promote_to_spike` |
| 5 | Coop / Unicoop Etruria | online shopping promotions + store-specific offer surfaces | high | strong store/cooperative orientation | `promote_to_spike` |
| 6 | Conad | store-specific flyers + some product-level promotional surfaces | medium/high | very strong | `promote_to_spike` |
| 7 | MD | store-selected digital flyer | medium | strong | `watch` / flyer-backend spike |
| 8 | Eurospin | store-selected flyer + weekly occasion surface | medium | strong | `watch` / flyer-backend spike |
| 9 | Todis | store-selected flyer + structured reservation products | medium | strong | `watch` |
| 10 | Pam Panorama | online grocery + store-oriented flyer/app | medium | strong | `watch` |
| 11 | Bennet | store-selected digital flyers | medium | strong | `watch` |

The ranking is intentionally provisional. A retailer may move substantially after endpoint inspection.

## 1. PENNY — promote to spike

Observed official source: `https://www.penny.it/offerte`.

The public offers surface exposes product-level structured information directly in rendered content, including:

- product name;
- brand where available;
- package quantity;
- explicit validity interval (`da ... a ...`);
- promotional price;
- previous/base price for percentage discounts;
- unit/reference price;
- explicit percentage discount;
- PENNYCard-specific price versus non-card price;
- quantity-limited markers.

Example observed on 2026-08-27: a loyalty-aware product can expose both `Senza PENNYCard` and `Con PENNYCard` prices in the same product record.

Why this matters:

```text
product identity
+ price
+ reference/base price
+ validity
+ loyalty semantics
+ unit price
```

are all visible before any hidden-endpoint work.

Unknowns for spike:

- exact locality/store semantics of the offers page;
- whether the frontend consumes a stable structured endpoint;
- stable product identifiers;
- provenance timestamps/source identifiers;
- pagination/filter endpoint behavior.

Recommendation: first or second technical spike.

## 2. ALDI — promote to spike

Observed official surfaces:

- `https://www.aldi.it/prodotti`
- `https://www.aldi.it/speciali-della-settimana`
- `https://www.aldi.it/volantino-online`

The public catalogue exposes product rows with:

- product name and brand;
- quantity/package text;
- current price;
- unit/reference price;
- previous price for discounted products;
- percentage discount for some offers;
- explicit availability date for weekly specials.

ALDI also publishes current-week and next-week offers. Official copy states that most promotions are national while availability can vary by store.

Strengths:

- unusually rich product catalogue;
- product data visible outside a PDF viewer;
- freshness dates directly present;
- base/current price pairs are observable for some discounts.

Risks / unknowns:

- weaker store-specific locality than several competitors;
- availability semantics are not equivalent to store verification;
- hidden endpoint stability is not yet known.

Recommendation: high-priority spike.

## 3. Despar — promote to spike

Observed official surfaces:

- `https://www.despar.it/it/volantino-digitale/<id>/`
- point-of-sale finder under `https://www.despar.it/it/punti-vendita/`

The digital flyer is not merely an image/PDF shell. Observed pages expose product-level offer rows containing combinations of:

- product name;
- brand;
- quantity/package;
- offer price;
- base/original price;
- percentage discount;
- multibuy mechanics such as `2+1 gratis`;
- per-piece effective price;
- flyer validity interval;
- category filters.

Store and regional context are explicit in the Despar site and individual flyer pages can be associated with point-of-sale or concession-area context.

This is especially attractive because it combines rich promotion semantics with locality.

Unknowns:

- flyer ID discovery contract;
- exact mapping between flyer IDs, stores and concession areas;
- structured endpoint behind the digital flyer;
- stable product identifiers.

Recommendation: high-priority spike, potentially the richest promotion-semantics target.

## 4. Carrefour — promote to spike

Observed official surfaces:

- `https://www.carrefour.it/`
- `https://www.carrefour.it/volantino`

The official homepage exposes product-level online promotions including:

- product name;
- package quantity;
- current price;
- original price;
- unit price;
- percentage discount;
- explicit promotion end date;
- PAYBACK markers for some items.

The flyer surface is explicitly point-of-sale oriented and requires CAP/city/address selection.

Strengths:

- rich product-level pricing surface;
- explicit validity;
- loyalty marker;
- strong locality surface through store selection.

Risks:

- online assortment/pricing may differ from physical-store flyer semantics;
- personalized `Volantino PER TE` must not be conflated with public promotion data;
- endpoint access may depend on store/cart context.

Recommendation: spike after PENNY/ALDI/Despar or in parallel if locality is the priority.

## 5. Coop / Unicoop Etruria — promote to spike

Observed official surfaces:

- `https://coop.it/index.php/spesa-e-servizi`
- `https://coopacasa.coopetruria.coop.it/promo`
- Unicoop Etruria store/app surfaces.

The Coop a Casa promotion surface observed for Unicoop Etruria exposes hundreds of product-level promotion rows and filters, including:

- product and brand;
- package quantity;
- promotion percentage;
- promotional price;
- previous price;
- unit price;
- validity (`per consegne fino al ...`);
- lifestyle/product-category metadata.

Coop's public/store surfaces are explicitly tied to preferred stores/cooperatives and store-specific flyers.

Architectural note: "Coop" is not one uniform retailer backend. Cooperative ownership/territory likely matters. Source discovery and adapters may need cooperative-specific boundaries rather than a fictional national Coop source.

Recommendation: promote Unicoop Etruria / Coop a Casa to a dedicated spike rather than treating all Coop as one source.

## 6. Conad — promote to spike

Observed official surfaces:

- `https://www.conad.it/ricerca-negozi`
- homepage promotional products / `Bassi e Fissi`.

Conad explicitly requires point-of-sale selection to discover flyers and active offers. The public homepage also exposes product-level promotional examples with price and date range.

Strengths:

- excellent locality semantics;
- explicit store relationship;
- product-level promotional data exists in at least some surfaces.

Unknowns:

- flyer backend structure;
- cooperative/store variance;
- whether product rows can be enumerated reproducibly for a selected store;
- loyalty mechanics representation.

Recommendation: promote to spike, focused first on one concrete store rather than national Conad.

## 7. MD — watch / flyer-backend spike

Observed official surface: `https://www.mdspa.it/volantino/`.

The site requires point-of-sale selection and exposes a current flyer with explicit campaign date range. Point-of-sale pages expose "Offerte in corso", online flyer and downloadable flyer links.

Strengths:

- strong locality;
- explicit campaign validity;
- official store/flyer relationship.

Current limitation: public indexed content exposes much less product-level structure than PENNY/ALDI/Despar.

Recommendation: inspect the digital-flyer backend before committing to an adapter.

## 8. Eurospin — watch / flyer-backend spike

Observed official surface: `https://www.eurospin.it/volantino/`.

The flyer is explicitly tied to the nearest/selected point of sale and the homepage publishes current campaign ranges and weekly occasions.

Strengths:

- strong locality;
- explicit flyer campaigns;
- official weekly-offer surface.

Current limitation: product-level structured data is less exposed in indexed public content than higher-ranked candidates.

Recommendation: inspect flyer backend only; no scraper commitment yet.

## 9. Todis — watch

Observed official surface: `https://www.todis.it/`.

The homepage is store-oriented and exposes flyer discovery plus structured product cards for reservable non-food products with availability and prices.

This proves the platform can render structured product data, but it does not yet prove that grocery flyer products are available through the same machine-readable surface.

Recommendation: watch / targeted endpoint inspection.

## 10. Pam Panorama — watch

Observed official surface: `https://www.pampanorama.it/`.

The site advertises online shopping "agli stessi prezzi e offerte del negozio" and the app exposes a digital flyer for the preferred store.

Potential value:

- online catalogue may provide structured product data;
- store preference may provide locality context;
- loyalty/coupon semantics are explicit through Carta Per Te / Perte Plus.

Unknowns:

- unauthenticated catalogue discoverability;
- store-context contract;
- public versus personalized offer separation.

Recommendation: watch, then spike if online catalogue can be inspected without authentication barriers.

## 11. Bennet — watch

Observed official surface: `https://www.bennet.com/flyer`.

The site exposes selected-store digital flyers and explicit campaign date ranges.

Current evidence is sufficient for a flyer-backend lead, but not yet for a product-level source classification.

Recommendation: watch.

## Cross-retailer conclusions

### Strongest product-level surfaces

The best observed public product-level surfaces are currently:

```text
PENNY
ALDI
Despar
Carrefour
Coop a Casa / Unicoop Etruria
```

These deserve endpoint/source spikes before lower-information flyer-only targets.

### Strongest locality surfaces

The strongest observed locality contracts are:

```text
Conad
Carrefour
Despar
Coop / cooperative-specific
MD
Eurospin
Todis
```

### Important warning

A visually rich or server-rendered product page is not automatically a stable dataset. Each promoted spike must establish:

1. exact source request/response or embedded-data mechanism;
2. reproducibility without bypassing access controls;
3. stable identity candidates;
4. freshness/update behavior;
5. locality semantics;
6. promotion semantics;
7. provenance that Grocery Deal Intelligence can record honestly.

## Recommended spike order

```text
#1 PENNY
#2 ALDI
#3 Despar
#4 Coop a Casa / Unicoop Etruria
#5 Carrefour
#6 Conad (single selected store)
```

PENNY ranks first because the public offers surface already contains the highest concentration of canonical-relevant facts, including loyalty-aware dual pricing. ALDI is a close second because of its unusually rich public product catalogue. Despar may ultimately be stronger than both for promotion semantics if its digital-flyer backend proves stable.

## Next action

Open isolated spike issues rather than one giant integration task. Each spike should be allowed to end in `reject` if the source is unstable, inaccessible, overly personalized, or insufficiently attributable.
