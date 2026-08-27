# Carrefour store-scoped flyer fixture spike (#83)

## Decision

`promote_to_adapter_implementation`

## Target

Official public Carrefour Express flyer for:

- store id: `5190`
- flyer id: `56879`
- store: Carrefour Express, Viale Abruzzi 54, Milano
- campaign: `Offerte d'estate`
- validity: `2026-08-03` through `2026-08-31`

Source URL:

`https://www.carrefour.it/volantino/supermercato-carrefour-express-milano-viale-abruzzi-54/5190/-volantino-supermercato-carrefour-express-milano-viale-abruzzi-54-5190-offerte-d-estate-carrefour-express-56879-carrefour-express/56879`

The same public flyer page carries the store locality, campaign validity and promotion rows used by this spike. No separate locality source is merged into the fixture.

## Captured fixture

Path:

`fixtures/carrefour/store-5190-flyer-56879.txt`

SHA-256:

`25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571`

The committed fixture is a deterministic textual excerpt preserving only facts observed on the public flyer surface. It is not canonical data.

## Evidence represented

The fixture preserves:

- store id and flyer id;
- store identity/address/locality;
- campaign title and validity interval;
- product identity text;
- percentage discount where shown;
- `SPESAMICA PAYBACK` marker where shown;
- displayed base/current price texts;
- displayed unit/reference price text.

Examples include:

- Brescia Latte UHT Centrale Brescia Parzialmente Scremato 1 l: `-30%`, `SPESAMICA PAYBACK`, `€1,57`, `€1,09`, `€1,09 al Lt`;
- Passata di Pomodoro Terre d’Italia 520 g: `-21%`, `SPESAMICA PAYBACK`, `€1,39`, `€1,09`, `€2,10 al Kg`;
- Raffo Birra Originale 3 x 330 ml: `-25%`, `SPESAMICA PAYBACK`, `€3,47`, `€2,49`, `€2,52 al Lt`.

## Parser boundary

`grocery_deal_intelligence.carrefour_fixture` parses only the committed fixture contract.

It does not:

- infer canonical promotion semantics;
- decide whether the first/second price is a base or final canonical price beyond preserving order;
- infer loyalty requirements beyond preserving the explicit PAYBACK marker;
- perform network access;
- ingest personalized `Volantino Per Te` content;
- alter canonical validation or admission behavior.

## Personalized content boundary

`Volantino Per Te` is explicitly outside this spike. The fixture is derived from the ordinary public store-scoped flyer only.

## Verification

Tests cover:

- fixture SHA-256 identity;
- store/flyer/locality metadata;
- deterministic offer parsing;
- discount, loyalty and price-text preservation;
- deterministic/read-only behavior;
- missing metadata rejection;
- malformed offer rejection.

## Recommendation

Carrefour now has the same essential source properties that justified the Despar promotion:

```text
official public store-scoped flyer
        ↓
committed hashed fixture
        ↓
deterministic parser
        ↓
source evidence only
```

Therefore the recommendation is `promote_to_adapter_implementation`.
