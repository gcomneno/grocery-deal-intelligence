# Bennet selected-store flyer source spike (#96)

## Decision

`promote_to_adapter_spike`

## Objective

Evaluate Bennet as a deterministic retailer evidence source by selecting one concrete point of sale and checking whether store identity, flyer applicability, promotion validity and price evidence can be replayed without conflating public flyer evidence with loyalty/personalized surfaces.

## Concrete point of sale

Official Bennet-controlled surfaces observed on 2026-08-27 identify and actively select:

- retailer: `Bennet`
- locality: `Montano Lucino (CO)`
- selected-store context: `Il tuo Punto Vendita Bennet`
- public store-finder surface: `https://www.bennet.com/storefinder`

The store finder lists Montano Lucino among Bennet points of sale and the public flyer page simultaneously renders Montano Lucino as the selected point of sale.

## Public flyer capability

The official flyer page at `https://www.bennet.com/flyer` exposes a selected-store context and a set of currently active flyer campaigns.

Observed campaigns include explicit validity intervals such as:

- `SOTTOCOSTO FRESCHI` — `27/08` through `09/09`;
- `TUTTO PRONTO PER LA SCUOLA 2° PARTE` — `27/08` through `16/09`;
- `IL BELLO DEL PULITO` — `20/08` through `02/09`;
- `SCUOLA 1` — `30/07` through `16/09`;
- `OFFERTE EXTRA` — `20/08` through `02/09`.

The same page states that the user is viewing flyers for the currently selected store context.

This is stronger than a generic chain-wide flyer listing because store selection and flyer rendering coexist in the same retailer-controlled surface.

## Promotion richness

Bennet's main shopping surface exposes product rows with structured promotion evidence including, depending on the product:

- product name and brand;
- base price;
- current/promotional price;
- percentage discount;
- package quantity;
- unit/reference price;
- current availability status;
- online-purchasability status.

Observed examples on the official surface include rows with explicit percentage discounts and struck-through/base unit prices alongside current unit prices.

## Store-selection semantics

Bennet explicitly requires store selection before online shopping.

Its WhatsApp flyer service likewise instructs users to indicate a reference Bennet point of sale before receiving the flyer.

These independently confirm that locality/store context is part of Bennet's offer and flyer semantics.

## Retrieval result

The exact deterministic transport:

```text
Montano Lucino (CO)
        ↓
selected-store identity/context
        ↓
applicable flyer set
```

was not yet pinned as a stable store identifier, query parameter, path component, embedded token, cookie-independent request, or other directly replayable public mechanism during this spike.

The current public page proves that a selected-store flyer context exists, but not yet how to reproduce that exact selection deterministically from a fresh client without relying on frontend/session state.

Accordingly, no Montano-Lucino-specific raw fixture is captured here yet.

## Loyalty and personalization boundary

Bennet Club and the Bennet app expose coupon and dedicated-benefit semantics. Those must remain distinct from public store-applicable flyer evidence.

The evidence classes remain separate:

```text
public selected-store flyer evidence
!= Bennet Club coupon evidence
!= personalized/dedicated app offers
```

No loyalty-only or personalized content is harvested or promoted into public deterministic evidence by this spike.

## Evidence boundary

Observed and supported:

- Bennet exposes a public store finder;
- Montano Lucino (CO) is a real Bennet point of sale;
- the public flyer page renders Montano Lucino as the selected store context;
- active flyer campaigns have explicit validity intervals;
- the shopping surface exposes rich product/base/current-price/unit-price evidence;
- Bennet requires store selection for shopping and reference-store selection for WhatsApp flyer delivery;
- loyalty/coupon surfaces exist and are semantically distinct.

Not yet supported:

- a stable public Bennet store identifier usable directly in flyer retrieval;
- a replayable Montano Lucino → flyer URL or request parameter;
- a cookie/session-independent recipe that reproduces the same selected-store context;
- a raw current Montano Lucino store-scoped fixture;
- deterministic parser input proven to be scoped to that store.

## Recommendation

`promote_to_adapter_spike`

The next Bennet spike should focus narrowly on pinning the selected-store transport and capturing one raw applicability-proven flyer/promotion response before any deterministic parser or production adapter is introduced.

Expected boundary:

```text
official Bennet store selection
        ↓
replayable store identity/context
        ↓
applicability-proven flyer/promotion response
        ↓
raw fixture + SHA-256
        ↓
deterministic parser
```

## Non-goals preserved

No production scraper, adapter, AI change, canonical schema change, admission-policy change, access-control bypass, loyalty harvesting, personalized-offer harvesting, or inferred store applicability is introduced by #96.
