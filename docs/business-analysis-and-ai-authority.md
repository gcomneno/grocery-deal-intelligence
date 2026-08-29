# Business analysis, deterministic boundaries, and AI authority

## Purpose

Grocery Deal Intelligence (GDI) did not become verification-first because grocery offers are intrinsically complicated data structures. It became verification-first because apparently simple shopping questions repeatedly exposed different kinds of uncertainty, evidence, interpretation, policy, derivation, and decision authority.

The central lesson is:

```text
use deterministic logic where the problem is deterministically decidable

use AI where semantic interpretation is genuinely required

never confuse interpretation with authority
```

GDI therefore does not treat deterministic software and AI as competing implementation strategies. They have different roles. Deterministic code owns authority wherever evidence and explicit rules can decide the question. AI is useful where the input requires semantic interpretation, but its output remains a proposal until deterministic verification and admission establish what GDI is allowed to rely on.

The repository rule is deliberately stronger than "validate AI output":

> AI output is data, never authority.

This document explains the business-analysis obstacles that produced that rule and the architecture around it. It is not an issue-by-issue history. Each section focuses on a recurring pattern: the business question, the tempting shortcut, the boundary GDI chose, and the resulting lesson.

## 1. An offer is not a single fact

### Business problem

A supermarket offer that looks obvious to a shopper may expose several economically different values:

- the current or promotional price;
- the ordinary or original reference price;
- a source-displayed unit price;
- free-form source text representing a base or original price;
- a discount claim such as `-25%`.

Treating all price-looking values as interchangeable destroys meaning before comparison even begins.

Concrete Carrefour evidence forced this distinction. Examples encountered during source analysis included:

- milk with `price = 1.09` and `reference_price = 1.57`;
- passata with `price = 1.09` and `reference_price = 1.39`;
- beer with `price = 2.49` and `reference_price = 3.47`.

The beer source also carried a `-25%` promotional claim. That claim is source evidence. GDI preserves it as stated rather than recomputing it from numeric fields and silently replacing the retailer's assertion with its own arithmetic interpretation.

### Rejected shortcut

```text
any price-like value -> one generic price field
```

or:

```text
source discount text -> recompute -> corrected discount claim
```

Both shortcuts lose provenance and make later decisions impossible to audit.

### Chosen boundary

GDI keeps these concepts distinct:

```text
price
!= reference_price
!= source-displayed unit price
!= base_price_text
!= promotion.discount_text
```

`price` is the current/promotional price shown to the shopper. `reference_price` is the ordinary/original numeric comparison price. A source unit price is not silently reclassified as either. Promotional text remains a source claim.

### Lesson

Business analysis must establish the semantics of apparently similar fields before normalization. Deterministic processing is reliable only after the meaning of its inputs has been made explicit.

## 2. Reading a value is not authorizing it

### Business problem

Extraction and truth are different questions. A parser or AI model may produce a plausible value, but GDI still needs to know why that value is allowed to influence canonical data or a downstream decision.

### Rejected shortcut

```text
source -> parser or AI -> canonical truth
```

This collapses observation, interpretation, verification, and admission into one step.

### Chosen boundary

The canonical authority chain is:

```text
source record
    -> source evidence
    -> candidate / proposal
    -> claim verification
    -> structural validation
    -> canonical admission
    -> canonical | null
```

Each transition answers a different question. A candidate may be structurally plausible but unsupported by evidence. A supported fact may still be insufficient for canonical admission. A rejected record remains observable rather than being repaired silently.

GDI therefore fails closed when the available evidence is insufficient. A lower canonical count is preferable to a larger dataset whose authority cannot be explained.

### Lesson

The important question is not only "can we extract this value?" but "what authorizes us to rely on it?" Authority should be explicit, narrow, and testable.

## 3. Where deterministic ingestion wins

### Business problem

Early AI-assisted work demonstrated that semi-structured retailer data can benefit from semantic interpretation. It also exposed a more important fact: when a retailer record already contains explicit structured evidence, asking an AI to rediscover those fields adds uncertainty without adding information.

### Rejected shortcut

```text
every retailer record -> AI extraction -> canonical candidate
```

That approach would make model availability, model behavior, and prompt interpretation part of a path that can often be solved exactly.

### Chosen boundary

The first-class ingestion path is deterministic whenever the source record contains sufficient explicit evidence. Retailer-specific interpretation belongs at the adapter/source-evidence boundary, while generic canonical validation and admission remain retailer-neutral.

AI-assisted ingestion remains optional and advisory for genuinely ambiguous or semi-structured inputs. The deterministic core must remain usable without Ollama, GiadaWare AI, network access, or a model installation.

### Lesson

AI should not be used merely because it can solve a problem. If explicit source structure already decides the question, deterministic transformation is cheaper to reason about, reproducible, independently testable, and easier to audit.

## 4. Semantic meaning is where AI becomes useful

### Business problem

Some shopping questions are not reducible to syntax. Product descriptions may differ while referring to the same product family or to products a shopper reasonably considers alternatives.

A deterministic parser can reliably normalize `2 x 100 g`. It cannot generally infer from arbitrary commercial language that two differently worded offers should both be understood as dark chocolate without introducing a semantic classification policy of its own.

### Rejected shortcuts

Two opposite shortcuts are unsafe:

```text
semantic ambiguity -> force deterministic lexical guesses -> truth
```

and:

```text
semantic ambiguity -> ask AI -> truth
```

The first hides heuristics as deterministic authority. The second delegates authority to a probabilistic interpreter.

### Chosen boundary

AI may propose semantic interpretations such as:

- candidate product-family assignments;
- candidate product relationships;
- structured facts that GDI should inspect;
- possible policy templates or user-facing interpretations.

But proposal and authority remain separate:

```text
AI semantic interpretation
    -> structured proposal
    -> deterministic evidence verification
    -> deterministic policy / admission
    -> authorized result | unknown
```

AI is useful because it can generate candidate meaning from language. It is not authoritative merely because that meaning is plausible.

### Lesson

The strongest role for AI in GDI is semantic proposal generation. The strongest protection against AI error is not asking the model to be more confident; it is designing the next boundary so that the proposal must survive deterministic checks before it matters.

## 5. `same_product`, `comparable`, `cheaper`, and `recommended` are different questions

### Business problem

Shopping language easily collapses several decisions:

- Are these exactly the same product?
- Are they reasonable alternatives for this shopping intent?
- Can their prices be normalized to a common basis?
- Which normalized price is lower?
- Which should the shopper buy?

Those are not synonyms.

### Rejected shortcut

```text
looks similar -> same product -> comparable -> cheaper -> recommended
```

A single fuzzy score or AI judgment could make this pipeline look convenient while hiding multiple independent authority decisions.

### Chosen boundary

GDI keeps the concepts explicit:

```text
same_product
!= comparable
!= economically normalizable
!= cheaper
!= better
!= recommended
```

Product-comparison proposals use `same_product`, `comparable`, or `unknown`. A failed `same_product` proposal is not automatically downgraded to `comparable`. Price comparison occurs only after comparability and economic normalization have independently succeeded. Recommendation remains downstream and unresolved.

### Lesson

A business term should not be promoted into a stronger conclusion merely because the stronger conclusion is convenient. Every transition that changes meaning needs its own authority boundary.

## 6. User intent changes policy, not evidence

### Business problem

Practical comparability depends on what the shopper cares about. For one purchase, brand may be irrelevant. For another, package size may be a hard requirement. Cocoa percentage may be a preference rather than a requirement.

The source facts do not change when the shopper changes their mind.

### Rejected shortcuts

GDI rejected both hidden hard-coded assumptions and AI-selected policy:

```text
heuristic preference -> pretend it is semantic truth
```

```text
AI thinks this attribute matters -> comparison authority
```

### Chosen boundary

Comparison policy uses explicit effects:

- `require` — a hard comparability condition;
- `ignore` — explicitly irrelevant to comparability;
- `prefer` — potentially useful for later ranking, but not comparability authority;
- `exclude` — a verified condition that disqualifies a candidate.

Policies are deterministic, versioned, inspectable, provenance-carrying, and overridable. AI may propose a policy template, but it cannot silently choose the effective policy.

### Lesson

User preference is configuration over verified facts, not evidence about the product. Keeping those concepts separate allows personalization without corrupting source truth.

## 7. Normalized product attributes require two different kinds of reasoning

### Business problem

Comparison needs normalized facts that the canonical offer does not necessarily expose directly, including product family and quantity.

Those facts do not all have the same epistemic character.

### Deterministic quantity normalization

Supported quantity syntax can be interpreted deterministically:

```text
100 g
1 kg
500 ml
2 x 100 g
2 × 100 g
```

Mass and volume remain distinct. Composite packs preserve pack count, unit quantity, and total quantity.

A critical review exposed the danger of partial interpretation. Text such as:

```text
100 g + 20 cl
2 x 100 g + 50 g
```

must not be accepted by selecting only the fragment the parser understands. Unsupported or mixed residual quantity information makes the result `unknown`.

Another review exposed a claim-binding bug: path identity alone was insufficient. A supported claim for `weight_g` must carry the exact normalized value being consumed. Duplicate conflicting claims invalidate the path.

### Semantic product-family interpretation

`product_family` is different. It represents meaning rather than merely unit syntax. Candidate semantic classification can therefore benefit from AI, but the resulting fact still needs narrow, versioned evidence verification before comparison policy can consume it.

### Lesson

"Normalization" is not one homogeneous operation. Some normalization is deterministic arithmetic or parsing; some requires semantic interpretation. The architecture should classify the reasoning problem before choosing the tool.

## 8. Cross-size comparison corrected a business assumption

### Business problem

The initial dark-chocolate comparison policy required equal package weight. That matched an intuitive first formulation of the shopping requirement, but it became incorrect once GDI gained trustworthy economic normalization.

A 100 g dark-chocolate bar and a 150 g dark-chocolate bar may be perfectly reasonable alternatives. Requiring equal package size prevents comparison precisely where `EUR/kg` can make different sizes economically comparable.

### Rejected assumption

```text
same package size == semantic comparability requirement
```

### Chosen boundary

The built-in chocolate policy became:

```text
same product family  -> require equal
same weight          -> ignore
brand                -> ignore
cocoa percentage     -> ignore
sugar percentage     -> ignore
```

Weight remains observable. It simply no longer grants or denies semantic comparability by default. A user override can restore strict equal-weight comparison when that is the actual intent.

The resulting distinction is:

```text
semantic comparability
!= package-size equality
!= economic-basis compatibility
!= cheaper decision
```

### Lesson

Deterministic does not mean infallible. A deterministic rule can encode the wrong business assumption. Review must challenge the semantics of the rule, not only its reproducibility.

## 9. Economic normalization is deterministic derivation, not new evidence

### Business problem

Once two products are semantically comparable, different package sizes still prevent direct comparison of sticker prices. GDI needs a common economic basis.

### Rejected shortcuts

The economic layer deliberately does not:

- reparse product names or packaging text;
- substitute `reference_price` for the current price;
- trust a free caller-provided `comparable = true` flag;
- convert mass to volume through assumed density;
- perform FX conversion;
- borrow missing quantity evidence.

A particularly important review correction removed free boolean comparability authority. Economic normalization must consume a structured admitted comparison-policy result rather than trusting a caller's `True`.

### Chosen boundary

For supported quantities:

```text
verified grams      -> EUR/kg
verified millilitres -> EUR/l
```

The numerator is canonical current `price`. The quantity must remain bound to its own supported normalized claim. Economic normalization is a deterministic derivation over already-authorized inputs.

### Lesson

Derived facts should preserve the authority of their inputs without pretending to become source evidence. A downstream function must not accept a convenient boolean substitute for the upstream proof it actually depends on.

## 10. Exact rational prices prevent presentation from becoming authority

### Business problem

Some normalized prices have non-terminating decimal representations. For example:

```text
1.00 EUR / 300 g -> 10/3 EUR/kg
```

If GDI persisted a rounded decimal and later used it for ordering, a presentation choice would become economic authority.

### Rejected shortcut

```text
exact derivation -> rounded display decimal -> authoritative comparison
```

### Chosen boundary

Economic normalization stores the comparable price as an exact reduced rational:

```text
exact_ratio.numerator
exact_ratio.denominator
```

A UI may render `10/3` to a convenient decimal, but the rendered value is presentation only.

### Lesson

Deterministic computation can still lose correctness if representation is careless. The authoritative representation should preserve exactly the information needed by downstream decisions.

## 11. Deterministic price comparison remains deliberately bilateral

### Business problem

After comparability and economic normalization, GDI can finally answer a narrow question: which of two comparable normalized prices is lower?

### Chosen boundary

The comparator consumes only structurally supported economic-normalization results on a common authorized basis:

```text
EUR/kg <-> EUR/kg
EUR/l  <-> EUR/l
```

It compares exact rational values and returns:

```text
left_cheaper | right_cheaper | equal | unknown
```

A review hardened this boundary further. A mapping that merely claimed `status = supported` was insufficient; version, current price, quantity, basis, dimension, comparable price, and derivation rule must be structurally coherent before ordering is allowed.

### Rejected shortcut

```text
right_cheaper -> buy right
```

### Lesson

`cheaper` is an observable bilateral economic relationship. It is not yet a ranking over many offers and it is not a recommendation. Narrow outputs make later policy decisions explicit instead of smuggling them into arithmetic.

## 12. Deterministic vs AI decision matrix

| Problem | AI useful? | Authority |
| --- | --- | --- |
| Preserve explicit source facts and provenance | generally no | deterministic |
| Interpret retailer-specific structured evidence | generally no when explicit structure is sufficient | deterministic adapter/evidence projection |
| Verify source evidence | no | deterministic |
| Validate canonical structure | no | deterministic |
| Admit canonical records | no | deterministic |
| Normalize supported quantity syntax | no | deterministic |
| Interpret semantic product meaning | yes, as a proposal | deterministic evidence verification |
| Propose product relationship | yes, as a proposal | deterministic verification and policy |
| Resolve effective comparison policy | AI may suggest, but must not choose silently | deterministic configuration / explicit user intent |
| Decide semantic comparability | no once facts and policy are established | deterministic |
| Normalize current price to EUR/kg or EUR/l | no | deterministic |
| Compare normalized prices | no | deterministic exact rational ordering |
| Rank many offers | potentially useful later | authority boundary not yet defined |
| Recommend what the shopper should buy | potentially useful for explanation or proposal | authority boundary not yet defined |

The pattern is intentional. AI is most valuable where meaning must be proposed from language or ambiguous context. Deterministic software is most valuable where evidence, contracts, arithmetic, and explicit policy can decide the question exactly.

## 13. End-to-end authority chain

The architecture that emerged from these business problems can be summarized as:

```text
retailer source
    ↓
source evidence
    ↓
deterministic extraction where sufficient
or AI-assisted semantic proposal where genuinely useful
    ↓
deterministic claim verification
    ↓
structural validation
    ↓
canonical admission
    ↓
verified canonical offer
    ↓
normalized product attributes
    ↓
semantic comparison proposal
    ↓
bilateral fact verification
    ↓
resolved explicit comparison policy
    ↓
same_product | comparable | unknown
    ↓
economic normalization
    ↓
exact common economic basis | unknown
    ↓
exact bilateral price comparison
    ↓
left_cheaper | right_cheaper | equal | unknown
    ↓
future ranking
    ↓
future recommendation / decision support
```

The important property is not that every box is deterministic. The important property is that any non-deterministic interpretation is prevented from silently acquiring downstream authority.

## 14. Anti-patterns explicitly rejected

### `source -> AI -> canonical truth`

AI output may be candidate data. Canonical authority belongs to deterministic verification, validation, and admission.

### AI repair of rejected data

A rejected record is evidence about the limits of the available input. AI must not silently manufacture missing support to increase admission rates.

### Evidence borrowing across records

One record cannot repair another. Batch-level confidence or repeated observations do not become per-record authority.

### Retailer-specific exceptions in generic consumers

Retailer knowledge belongs at adapters and evidence projection boundaries. Generic canonical and comparison consumers remain retailer-neutral.

### Recomputing source discount claims

A retailer's `-25%` statement is a source claim. Arithmetic disagreement is not permission to rewrite the evidence.

### Treating source unit price as reference price

Unit price, current price, and ordinary/original price have different business semantics.

### Partial quantity interpretation

Understanding one fragment of a compound quantity is not evidence that the whole quantity has been understood.

### Free boolean comparability authority

`comparable = true` is not proof. Economic normalization consumes the structured admitted policy decision on which it depends.

### Rounded display price as ordering authority

Presentation rounding must not decide which offer is cheaper. Exact rational values remain authoritative.

### Package-size equality as universal comparability authority

Equal weight may be a user policy, but it is not a universal semantic truth. Different package sizes can share an exact economic basis.

### `cheaper` silently becoming `recommended`

Price is one decision input. Recommendation requires a separate future boundary for preferences, ranking, exclusions, trade-offs, and explanation.

## 15. What remains unresolved: ranking and recommendation

GDI now has enough verified machinery to establish a narrow economic fact about a pair of comparable offers. It does not yet have authority to answer the broader question:

> Which offer should I buy?

That future layer must decide explicitly how to handle, among other things:

- more than two eligible offers;
- user `prefer` rules;
- hard exclusions;
- price ties;
- non-price preferences;
- missing evidence;
- retailer or trip-level constraints;
- explanation of why one option was selected.

AI may eventually be valuable for natural-language interaction, interpreting preference statements, or explaining a deterministic result. That does not imply that a model should own ranking authority.

The boundary must be designed before recommendation is implemented.

## 16. Transferable lessons beyond GDI

The GDI case suggests a reusable pattern for AI-assisted engineering.

### Classify the reasoning problem before choosing the tool

Do not ask whether AI can perform a task. Ask whether the task is syntactic, arithmetic, contractual, policy-driven, or genuinely semantic.

### Preserve proposals as proposals

When AI is useful, make its output an explicit intermediate artifact. Do not let a semantic guess become hidden application state.

### Verify the exact value being consumed

A matching field name or path is not enough. Downstream authority should remain bound to the exact verified value.

### Make uncertainty representable

`unknown` is a valid and often correct product result. Systems that cannot express uncertainty tend to manufacture certainty.

### Fail closed at authority boundaries

When required evidence is absent or contradictory, stop that decision. Do not repair the gap with unrelated evidence, confidence, or convenience.

### Keep business policy separate from observed fact

User intent can change what matters without changing what the source proved.

### Keep derivation separate from evidence

A deterministic calculation can be fully trustworthy without pretending that its result appeared in the source.

### Review semantics, not only code correctness

The cross-size correction demonstrated that perfectly deterministic software can faithfully implement the wrong business assumption. Verification-first engineering requires review of both implementation and meaning.

### Do not promote a narrow result into a broader decision

`verified`, `comparable`, `cheaper`, `better`, and `recommended` should remain separate until an explicit boundary authorizes each transition.

## Canonical takeaway

GDI's architecture is not based on avoiding AI. It is based on assigning AI the role for which it is strongest while denying it authority it cannot prove.

```text
deterministic when evidence and rules decide
semantic AI when interpretation is genuinely required
verification before authority
unknown before invented certainty
```

That is the durable business-analysis lesson behind GDI's verification-first design.
