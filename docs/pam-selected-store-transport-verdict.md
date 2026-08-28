# Pam selected-store transport verdict (#117)

## Verdict

`watch`

## Objective

Resolve the remaining Pam/Panorama selected-store transport gate from #94 for the concrete store:

- banner: `PAM SUPERMERCATO`
- locality: `VIAREGGIO`
- address: `Largo Risorgimento, 13`
- postal code: `55049`

Promotion to deterministic adapter implementation requires a public, replayable chain from that concrete store identity to a flyer/promotion payload whose applicability and raw identity can be proven without joining unrelated surfaces.

## What is now confirmed

### A stable official store identifier is observable

Pam-controlled promotional/regulatory material lists the Viareggio store with numeric store identifier `738` and the same address:

```text
738 | VIAREGGIO | LU | Largo Risorgimento, 13 | 55049
```

This materially improves #94, which had only the human-readable store identity.

The numeric identifier is useful store evidence, but it is not by itself a flyer retrieval recipe.

### Pam flyer surfaces are retailer-controlled and campaign-specific

Pam publishes public flyer pages under `pampanorama.it/volantini/` that delegate rendering to `pam.volantinopiu.com` targets.

Observed examples expose explicit validity windows and structured product/category navigation.

The public surface therefore provides a stable retailer-controlled entry point into digital flyers, even when the rendered flyer asset is hosted by Pam's flyer service provider.

### Some flyer artifacts explicitly carry store applicability

A publicly indexed Pam flyer artifact explicitly contains the section:

```text
OFFERTE VALIDE NEI PUNTI VENDITA SOTTOELENCATI
```

and includes:

```text
VIAREGGIO
LARGO RISORGIMENTO, 13
```

This is important evidence: Pam flyer artifacts can themselves carry the applicability scope needed by GDI. Store applicability therefore does not necessarily need to be inferred from geography or preferred-store state.

That observed artifact is useful as historical evidence of the source contract. It is not treated as proof that the same campaign is current in August 2026.

## Remaining transport gate

The exact deterministic current mapping is still not pinned:

```text
Pam store 738
Viareggio / Largo Risorgimento 13
        ↓
public stable store → flyer binding
        ↓
current flyer payload
        ↓
raw bytes + SHA-256
```

The following individual facts are supported:

- store `738` identifies Viareggio / Largo Risorgimento 13 in Pam-controlled material;
- Pam exposes public campaign-specific flyer pages;
- flyer artifacts can explicitly list Viareggio / Largo Risorgimento 13 among valid stores;
- the Pam app supports a preferred-store digital flyer;
- public and personalized offers are separate evidence classes.

What is not yet supported is one replayable same-chain association that starts from store `738` (or an equivalent selected-store token) and deterministically resolves to the current applicable flyer payload.

No observed `pv...` flyer-service identifier is therefore asserted to mean store `738` without direct retailer-controlled evidence.

## Why the historical applicability artifact is not enough

The historical flyer proves an important capability:

```text
flyer payload
        ↓
explicit store list
        ↓
Viareggio / Largo Risorgimento 13
```

But implementation readiness requires an identity-pinned fixture and temporal suitability. During this spike we did not establish all of the following for one current artifact:

1. deterministic current flyer selection for store `738`;
2. reproducible raw-byte capture;
3. SHA-256;
4. explicit current validity;
5. explicit applicability to Viareggio in that same captured artifact.

A historical or externally indexed PDF is not silently relabeled as a current store-scoped fixture.

## Personalization and delivery boundaries remain separate

Pam's official app states that the digital flyer can expose offers for the user's preferred store. Pam a Casa uses delivery locality. Carta Per Te / Perte Plus includes personalized offers.

These remain distinct:

```text
public flyer applicability
!= preferred-store app state
!= delivery-context pricing
!= personalized loyalty offers
```

No personalized or delivery-context data is used to fill the missing public flyer transport.

## Fixture decision

No new Viareggio fixture is committed by this spike.

Reason:

```text
stable store id exists
        +
flyer applicability can be explicit
        but
current store → flyer binding not pinned
        ↓
no identity-pinned current fixture
        ↓
no parser
        ↓
no adapter
```

## Verdict rationale

The correct verdict is:

`watch`

This is a **strong watch** because two major uncertainties from #94 have narrowed:

- a concrete official numeric store identifier (`738`) is observable;
- Pam flyer artifacts can explicitly prove store applicability by listing the participating points of sale.

The remaining blocker is narrower and technical: pin one current retailer-controlled flyer payload to Viareggio/store `738` in a reproducible chain and capture its bytes.

This is not `reject` because the source semantics are rich and store applicability is demonstrably expressible by the flyer itself.

It is not yet `promote_to_adapter_implementation` because GDI must not manufacture the missing current store-to-payload association.

## Promotion condition

Pam may be promoted when the following chain is captured end-to-end:

```text
store 738 / Viareggio
        ↓
stable public current flyer binding
        ↓
Pam/Pam-provider flyer payload
        ↓
explicit validity + explicit Viareggio applicability
        ↓
reproducible raw bytes
        ↓
SHA-256
        ↓
deterministic parser candidate
```

A second acceptable path is a current public flyer artifact whose own applicability list explicitly includes Viareggio/Largo Risorgimento 13, provided its raw bytes are reproducibly captured and identity-pinned.

## Non-goals preserved

This spike introduces no production scraper, AI dependency, canonical schema change, admission-policy change, personalized-offer harvesting, private API reverse engineering, inferred store applicability, guessed flyer-service identifier, synthetic fixture, parser, or adapter implementation.
