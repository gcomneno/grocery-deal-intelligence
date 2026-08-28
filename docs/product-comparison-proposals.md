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
 resolved comparison policy
            ↓
 relationship evaluation
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

The comparison-policy mechanism now exists and can deterministically decide
which already-verified product facts matter for comparability. Built-in defaults
are explicit, versioned, inspectable, and overridable rather than hidden
semantic assumptions.

However, the current canonical grocery-offer schema still does not expose
normalized product-family or quantity facts sufficient to make those policies
operational over real canonical offers in the general case.

Consequently, the existing v0.1 proposal/admission path remains fail-closed to
`unknown` whenever the required verified product facts do not exist. This is
intentional rather than an implementation gap hidden as apparent certainty.

## Comparison policy boundary

Comparison policies are documented separately in
[Overridable comparison policies](comparison-policies.md).

They resolve in increasing specificity:

```text
built-in global default
    -> built-in category default
    -> user category override
    -> user product-family override
    -> user specific-product override
```

Policy rules operate only on verified facts. They cannot create missing facts or
turn heuristic category assumptions into source evidence.

This keeps three questions separate:

1. What facts were actually verified?
2. Which verified facts does the effective policy require, ignore, prefer, or
   exclude?
3. Does that explicit policy authorize comparability?

`same_product` remains a stronger and separate relationship from `comparable`.
The comparison-policy mechanism introduced for pragmatic comparability does not
silently authorize product identity.

## AI boundary

The core comparison path requires neither AI nor network access.

A future GiadaWare AI capability may propose structured comparison data,
category assignments, or candidate policy templates, but AI output remains
proposal data.

AI may help answer:

> Which relationship, category, or facts should GDI inspect?

AI may not answer authoritatively:

> Are these products proven to be the same or comparable?

Nor may AI silently choose or alter the effective user comparison policy.

That authority remains deterministic and evidence-grounded inside GDI.

In particular:

```text
same_product != comparable != cheaper != recommended

proposal verified != relationship verified

heuristic default != evidence

AI proposal != comparison authority
```

## Deliberate limitations

This layer does not implement:

- semantic extraction;
- fuzzy matching;
- embeddings;
- product catalogs;
- normalized product-family extraction;
- quantity or unit normalization;
- unit-price calculation;
- price normalization;
- ranking;
- recommendation;
- natural-language question answering;
- retailer-specific comparison exceptions.

Sharing the Grocery Offer v0.1 canonical schema is necessary for canonical
consumption but is never, by itself, evidence of product comparability.
