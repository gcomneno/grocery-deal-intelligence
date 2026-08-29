# Overridable comparison policies

GDI comparison policies express which already-verified product facts matter for
semantic comparability.

They are not source evidence, semantic truth, economic normalization, or AI
authority.

The policy hierarchy is:

```text
built-in global default
    -> built-in category default
    -> user category override
    -> user product-family override
    -> user specific-product override
```

More specific layers override only fields they explicitly redefine. Every
effective rule field retains provenance identifying the policy layer that
supplied it.

## Pragmatic defaults

Built-in defaults are deliberately pragmatic. They encode useful everyday
shopping assumptions without claiming universal semantic correctness.

They must remain:

- deterministic;
- inspectable;
- versioned;
- documented;
- explicitly identified as built-in defaults;
- overridable by users;
- separate from source evidence and canonical admission.

The initial built-in category is `chocolate_bar`.

Its default rules are:

```text
same product family  -> require equal
same weight          -> ignore
brand                -> ignore
cocoa percentage     -> ignore
sugar percentage     -> ignore
```

This means two verified dark-chocolate bars may be considered semantically
comparable even when their package weights differ. Weight remains observable,
but exact package-size equality is not comparison authority.

For example, a 100 g bar and a 150 g bar can both be semantically comparable as
`dark_chocolate`. Their different quantities are handled downstream by the
economic-normalization boundary, which can derive a common `EUR/kg` basis when
each offer has sufficient verified quantity evidence.

This separation is intentional:

```text
semantic comparability
!= package-size equality
!= economic-basis compatibility
!= cheaper decision
```

A missing or different weight therefore does not by itself block semantic
comparability. It may still prevent downstream economic normalization if no
verified quantity basis can be established.

The policy does not itself extract or verify `product_family`, `weight_g`,
`brand`, `cocoa_percentage`, or `sugar_percentage`. Those facts must already
have been established by an evidence/verification boundary before policy
evaluation.

## Rule vocabulary

Each rule has a stable rule identifier and an `effect`:

- `require`: the bilateral verified values must exist and be equal;
- `ignore`: the fact is explicitly irrelevant to semantic comparability;
- `prefer`: the fact may matter later for ranking/recommendation, but cannot
  authorize comparability;
- `exclude`: an explicitly configured verified value makes the candidate
  unacceptable.

`ignore` and `prefer` are non-authoritative for comparison admission.

A policy containing only `ignore` and/or `prefer` rules fails closed rather than
making every pair comparable by vacuous truth.

## Policy provenance

Resolved policies expose:

- all applied policy layers;
- effective rules;
- field-level provenance for inherited and overridden rule fields.

For example, the built-in chocolate policy ignores exact weight equality, while
a user override may deliberately change `same_weight` back to `require/equal`
for a stricter personal comparison rule. The effective result records which
layer supplied each rule field.

This makes silent policy drift observable.

## Authority boundary

The intended authority chain is:

```text
already-admitted canonical offers
    -> comparison proposal
    -> bilateral verified facts
    -> resolved comparison policy
    -> deterministic policy evaluation
    -> semantically comparable | unknown
    -> economic normalization
    -> common economic basis | unknown
```

Policy evaluation consumes verified facts. It must never:

- create missing product facts;
- reinterpret source text as evidence;
- borrow evidence between offers;
- mutate canonical offers;
- rerun or weaken canonical admission;
- make retailer-specific exceptions in generic comparison logic;
- use AI confidence as comparison authority;
- claim economic compatibility merely because semantic comparability succeeded.

Missing required verified facts fail closed to `unknown`.

## GiadaWare AI boundary

GiadaWare AI may later propose:

- category/product-family assignments;
- candidate policy templates;
- possible user overrides.

Those proposals remain advisory until explicitly adopted by deterministic
configuration or user intent.

AI must not silently select the effective policy or authorize `same_product` or
`comparable`.

## Product-attribute and economic boundaries

The canonical grocery-offer schema itself still does not expose normalized
`product_family` or `weight_g` fields. GDI provides a separate downstream
[evidence-grounded normalized product-attribute boundary](normalized-product-attributes.md)
that can derive those comparison-ready facts from already-admitted offers while
preserving evidence, provenance, deterministic normalization, and fail-closed
semantics.

The comparison-policy evaluator consumes only supported normalized claims from
that boundary. It does not inherit parsing or semantic-classification authority.

After semantic comparability is admitted, the
[economic-normalization boundary](economic-normalization.md) independently
requires verified quantity evidence and derives a common basis such as `EUR/kg`
or `EUR/l`. Therefore semantic comparability may succeed while economic
normalization still fails closed.

This preserves the separation:

```text
canonical offer
    -> verified normalized product attributes
    -> comparison policy
    -> semantically comparable | unknown
    -> economic normalization
    -> common economic basis | unknown
```

Comparison policy remains separate from:

- same-product identity policy;
- quantity/unit normalization;
- price-per-unit calculation;
- cheapest/best ranking;
- recommendation;
- natural-language question answering.

In short:

```text
heuristic default != evidence

verified fact + explicit policy -> deterministic semantic-comparability decision

package-size equality != semantic-comparability authority

prefer != comparison authority

AI proposal != policy authority
```
