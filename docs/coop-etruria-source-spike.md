# Coop a Casa / Unicoop Etruria promotion source spike

Issue: #69

Decision: `promote_to_adapter_spike`

## Scope

This spike investigates the cooperative-specific `Coop a Casa / Unicoop Etruria` promotion surface. It does **not** assume a single national Coop backend.

Primary public surface:

```text
https://coopacasa.coopetruria.coop.it/promo
```

## Findings

### Cooperative boundary

The public site identifies the operator as `Unicoop Etruria SC` and explicitly routes some addresses to a previous `SpesaOnline Coop Etruria` platform.

This confirms that the source must be treated as a cooperative-specific boundary, not as a generic national Coop source.

### Promotion richness

The public `/promo` surface exposes machine-readable product promotion rows containing, depending on the offer:

- product name;
- brand;
- package quantity;
- promotional price;
- previous/base price;
- unit/reference price;
- percentage discount;
- promotion validity expressed as `per consegne fino al ...`;
- loyalty semantics such as `con carta socio Unicoop Etruria`;
- separate socio / non-socio prices where applicable.

Observed examples include ordinary discounts and loyalty-specific promotions.

### Stable-looking product identity

Product links use numeric identifiers directly in stable-looking product URLs.

Observed example:

```text
https://coopacasa.coopetruria.coop.it/salumi-e-formaggi/formaggi-confezionati/formaggi-spalmabili/75882.html
```

The product page renders `75882` as the product identifier together with product name, quantity, price and detailed product information.

This is strong evidence that product identity is not derived from display text alone.

### Backend / retrieval surface evidence

The rendered promotion page exposes Salesforce Commerce Cloud / Demandware-style request paths, including:

```text
/on/demandware.store/Sites-CoopTi-Site/it_IT/Search-Refinebar
```

and promotion query state such as a `pmid` value.

This is evidence of a structured commerce backend behind the public catalog. The exact request contract required for deterministic bulk retrieval is **not yet pinned** by this discovery spike.

### Locality and availability semantics

The public site explicitly requires a delivery or pickup context and warns that changing the delivery address can make products unavailable.

Therefore product availability and possibly promotion applicability are locality-dependent.

What is established:

- delivery and pickup are explicit modes;
- address context affects product availability;
- the platform may route locations to different Coop Etruria commerce surfaces.

What is not yet established:

- the exact deterministic parameter/cookie/session state that carries locality into promotion retrieval;
- whether a selected pickup store can be represented in a replayable request without session dependence;
- whether all promotion rows on `/promo` are globally advertised or contextualized to a default/current delivery scope.

No locality claim should be emitted until that context is pinned.

## Reproducibility assessment

### Strong

- public promotion catalog URL;
- product URLs with numeric identifiers;
- price and reference-price text;
- previous/base prices;
- percentage discount;
- delivery-valid-until text;
- loyalty labels and socio/non-socio price distinctions;
- cooperative ownership/provenance.

### Requires adapter spike

- bulk request endpoint contract;
- pagination / load-more request contract;
- promotion campaign identifier semantics;
- locality context transport;
- exact relationship between delivery address, pickup store and offer applicability.

## Deterministic boundary

```text
public Coop Etruria commerce surface
        ↓
cooperative-specific source context
        ↓
structured promotion/product evidence
        ↓
locality unresolved until request context is pinned
```

Do not infer national Coop applicability from this source.

## Recommendation

`promote_to_adapter_spike`

The source is rich enough to justify a concrete technical spike because it already exposes:

- stable-looking product IDs;
- detailed promotion semantics;
- loyalty-specific pricing;
- explicit validity;
- a visible structured commerce backend.

The follow-up must pin one reproducible locality-aware retrieval recipe and capture one raw promotion dataset before any production adapter is considered.

## Follow-up target

A suitable next issue is:

> Coop Etruria adapter spike: pin locality-aware Demandware promotion retrieval and capture one reproducible raw dataset

The success criterion is not merely retrieving `/promo`; it is proving the request context that determines locality/applicability.

## Non-goals preserved

This spike introduces no:

- production scraper;
- canonical schema change;
- AI change;
- admission-policy change;
- access-control bypass;
- assumption of a national Coop backend.
