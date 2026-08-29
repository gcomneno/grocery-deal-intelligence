# Deterministic exact price comparison

GDI compares prices only after semantic comparability and economic normalization have already succeeded.

The boundary is deliberately narrow:

```text
semantically comparable offers
    -> supported economic normalization
    -> common verified basis
    -> deterministic exact price comparison
    -> left_cheaper | right_cheaper | equal | unknown
```

Price comparison is not semantic-comparability authority, economic-normalization authority, ranking, or recommendation.

## Inputs

`compare_normalized_prices(left, right)` consumes two economic-normalization results produced by the downstream normalization boundary.

Both inputs must be structurally supported and expose a compatible comparable-price basis:

- `EUR/kg` with `EUR/kg`; or
- `EUR/l` with `EUR/l`.

The comparator does not reparse source text, inspect retailer-specific data, or recompute a price from package price and quantity.

## Exact rational authority

Economic normalization represents the comparable price as an exact rational value:

```json
{
  "exact_ratio": {
    "numerator": "10",
    "denominator": "3"
  }
}
```

The comparator orders these rational values exactly. It never rounds through a decimal display value before deciding which side is cheaper.

For example:

```text
10/3 EUR/kg > 13/4 EUR/kg
```

therefore the right side is cheaper even though either value may later be rendered with a finite number of decimal places for display.

Equivalent unreduced ratios are canonicalized by exact rational arithmetic, so `498/20` and `249/10` compare as equal.

## Outcomes

A supported comparison returns exactly one bilateral outcome:

- `left_cheaper`;
- `right_cheaper`;
- `equal`.

`unknown` is returned when the comparison cannot be authorized safely.

The supported result also carries:

- the common currency/unit basis;
- the reduced exact ratio for each side;
- the deterministic comparison rule identifier.

This makes the decision inspectable without treating rounded UI values as authority.

## Fail-closed cases

The comparator returns `unknown` when, among other cases:

- either economic-normalization input is not `supported`;
- a purported supported normalization contains contradictory structure;
- the two sides use incompatible bases such as `EUR/kg` and `EUR/l`;
- a rational numerator/denominator is malformed;
- a denominator is zero or negative;
- a numerator is negative.

No FX conversion, density conversion, evidence borrowing, or source-text reparsing is attempted.

## Authority boundary

Keep these concepts distinct:

```text
semantic comparability
!= package-size equality
!= economic-basis compatibility
!= exact price ordering
!= ranking
!= recommendation
```

A `right_cheaper` result means only that the right comparable-price ratio is numerically lower on the same authorized economic basis. It does not mean that the right product is preferable overall or that the user should buy it.

That distinction preserves the intended progression:

```text
verified offers
    -> semantic comparability
    -> exact economic basis
    -> exact bilateral price comparison
    -> future preference-aware ranking
    -> future recommendation / decision support
```
