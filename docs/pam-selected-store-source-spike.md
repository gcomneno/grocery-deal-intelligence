# Pam selected-store flyer source spike (#94)

## Decision

`promote_to_adapter_spike`

## Objective

Evaluate Pam/Panorama as a deterministic retailer evidence source by selecting one concrete point of sale and checking whether store identity, flyer applicability, promotion validity and price evidence can be replayed without conflating public, personalized and delivery-context offers.

## Concrete point of sale

Official Pam-controlled material identifies:

- banner: `PAM SUPERMERCATO`
- locality: `VIAREGGIO`
- address: `Largo Risorgimento, 13`
- postal code: `55049`

The store is also represented by Pam store-finder surfaces, which support finding and saving a preferred store.

## Public flyer capability

Pam exposes public flyer pages under `pampanorama.it/volantini/`. Observed public flyer pages expose explicit campaign validity and structured category/product navigation.

This is strong evidence that Pam has a retailer-controlled digital flyer surface, but the public flyer URL observed during this spike does not by itself prove applicability to the selected Viareggio store.

## Preferred-store semantics

Pam's official app/Carta Per Te surface states that the digital flyer can show offers for the user's preferred store. The website likewise supports saving a preferred Pam/Panorama store.

This proves that store preference is part of Pam's offer semantics. It does not yet prove how the preferred-store context is transported into a replayable flyer request.

## Online-shopping boundary

Pam a Casa states that online shopping uses the same prices and offers as the store for the selected delivery context. The online surface is therefore locality-sensitive, but delivery-address/CAP context must not be treated as equivalent to a stable public store-scoped flyer identifier without direct evidence.

## Personalization boundary

Carta Per Te and Pam Perte Plus expose dedicated and personalized offers. These are not interchangeable with public store-applicable flyer evidence.

The following must remain distinct:

```text
public flyer evidence
!= preferred-store flyer context
!= delivery-context online pricing
!= personalized Carta Per Te / app offers
```

## Retrieval result

The exact deterministic mapping:

```text
Pam Viareggio / Largo Risorgimento 13
        ↓
store identity / preferred-store context
        ↓
applicable public flyer variant
```

was not pinned as a stable replayable URL, request parameter, embedded identifier, or equivalent public transport during this spike.

Accordingly, no Viareggio raw flyer fixture is captured here and no generic Pam flyer is relabeled as store-scoped evidence.

## Evidence boundary

Observed and supported:

- Pam has an official Viareggio store at Largo Risorgimento, 13;
- public Pam flyer pages expose explicit validity and structured flyer navigation;
- Pam supports saving a preferred store;
- the Pam app advertises a digital flyer for the preferred store;
- Pam a Casa exposes locality-sensitive shopping through delivery context;
- Carta Per Te / app offers include personalization and must remain a separate evidence class.

Not yet supported:

- a stable public Pam store identifier for Viareggio usable in flyer retrieval;
- a replayable Viareggio → flyer URL or request parameter;
- a raw current Viareggio store-scoped fixture;
- deterministic parser input proven applicable to that store.

## Recommendation

`promote_to_adapter_spike`

The next Pam spike should focus only on pinning the selected/preferred-store transport and capturing one raw applicability-proven flyer or promotion response before any parser or production adapter is introduced.

Expected boundary:

```text
official Pam store selection
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

No production scraper, adapter, AI change, canonical schema change, admission-policy change, access-control bypass, personalized-offer harvesting, or inferred store applicability is introduced by #94.
