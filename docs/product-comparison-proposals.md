# Evidence-grounded product comparison proposals

Product comparison is a downstream authority boundary over already-admitted
canonical grocery offers.

Canonical admission proves that an offer is sufficiently grounded to enter the
canonical dataset. It does not prove that two canonical offers represent the
same product or are economically comparable.

The comparison flow is:

```text
already-admitted canonical offer A
            +
already-admitted canonical offer B
            ↓
    comparison proposal
            ↓
 bilateral fact verification
            ↓
 relationship evidence policy
            ↓
   comparison admission
            ↓
same_product | comparable | unknown
```

## Proposal vocabulary

A proposal may state one of:

- `same_product`
- `comparable`
- `unknown`

The proposal is advisory data. Its relationship is not authoritative.

`unknown` is the explicit fail-closed proposal when no stronger relationship is
claimed.

A failed or unsupported `same_product` proposal is never automatically
downgraded to `comparable`.

## Bilateral fact verification

Comparison claims are checked independently against the left and right
canonical offers.

A `supported` claim means only:

> the proposal represented this observed canonical fact correctly for this side.

It does not mean:

> this fact is sufficient to prove the proposed product relationship.

Evidence from one offer cannot repair missing evidence in the other.

Comparison admission also requires the verification set to correspond exactly
to the claim paths in the proposal. Missing, extra, mismatched, or duplicate
verification paths are rejected rather than being allowed to influence
relationship authority.

A proposed attribute absent from a canonical input is `unverifiable`. The
comparison layer does not extract or invent brand, category, variant, quantity,
unit, composition, pack count, or other facts from free text.

## Relationship authority

Bilateral fact verification and relationship admission are deliberately
separate authority layers.

For example, all of the following facts could be represented correctly on both
sides without proving product identity or comparability:

- retailer;
- price;
- product name;
- packaging text.

Therefore:

```text
bilaterally supported fact
    !=
relationship evidence
```

The current v0.1 contract does not yet define a deterministic semantic policy
that makes canonical fields sufficient to authorize `same_product` or
`comparable`.

Consequently, even a stronger proposal whose supplied facts are all
bilaterally supported is currently admitted only as `unknown`, with an explicit
`relationship_evidence_policy_unavailable` diagnostic.

This is intentional fail-closed behavior rather than an implementation gap
being hidden as apparent certainty.

## Future policy boundary

A later issue may introduce deterministic relationship-evidence rules once GDI
has sufficiently explicit product evidence.

Such evidence may eventually include independently verified product identity or
comparison attributes, but those facts must not be invented merely to improve
matching rates.

A future relationship policy will be responsible for deciding whether verified
facts are semantically sufficient for:

- `same_product`;
- `comparable`.

That policy remains distinct from quantity normalization, economic comparison,
ranking, and recommendation.

## AI boundary

The core comparison path requires neither AI nor network access.

A future GiadaWare AI capability may propose structured comparison data, but AI
output remains proposal data.

AI may help answer:

> Which relationship and facts should GDI inspect?

AI may not answer authoritatively:

> Are these products proven to be the same or comparable?

That authority remains deterministic and evidence-grounded inside GDI.

In particular:

```text
same_product != comparable != cheaper != recommended

proposal verified != relationship verified

AI proposal != comparison authority
```

## Deliberate limitations

This layer does not implement:

- semantic extraction;
- fuzzy matching;
- embeddings;
- product catalogs;
- quantity or unit normalization;
- unit-price calculation;
- price normalization;
- ranking;
- recommendation;
- natural-language question answering;
- retailer-specific comparison exceptions.

Sharing the Grocery Offer v0.1 canonical schema is necessary for canonical
consumption but is never, by itself, evidence of product comparability.
