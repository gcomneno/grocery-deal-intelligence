# AGENTS.md

## Purpose

Grocery Deal Intelligence is a verification-first laboratory for collecting,
normalizing, validating, admitting, and comparing grocery offers across retailers.

Prefer explicit evidence, deterministic behavior, and fail-closed outcomes over
apparent completeness.

## Core authority model

Canonical data is authorized only by deterministic application logic.

AI output is data, never authority.

Keep these layers distinct:

    source record
        -> source evidence
        -> candidate / proposal
        -> claim verification
        -> structural validation
        -> canonical admission
        -> canonical | null

No layer may silently collapse the authority of another.

## Deterministic ingestion

The first-class deterministic ingestion path is preferred whenever retailer
source records already contain sufficient explicit evidence.

Single-record ingestion owns per-record authority:

    ingest_deterministic_source_record(...)

Batch ingestion is orchestration only:

    ingest_deterministic_source_records(...)

The batch layer may aggregate observable outcomes, but it must never become a
new authority.

It must not:

- repair one record using another;
- borrow evidence across records;
- synthesize missing facts;
- convert aggregate confidence into per-record authority;
- hide rejected or ineligible records to improve success counts.

Rejected records remain observable with diagnostics and provenance.

## Fail-closed policy

When evidence is insufficient for canonical structure or admission, the correct
result is rejection or `canonical = None`.

Do not weaken canonical schema requirements, structural validation,
source-evidence verification, or canonical admission rules merely to increase
the number of admitted records.

A lower canonical count is acceptable when it is more truthful.

## Evidence and provenance

Every canonical claim must remain traceable to deterministic source evidence.

Preserve retailer identity, locality evidence, campaign identity where
available, capture metadata, fixture identity, verification results, and
rejection reasons.

Do not invent missing facts.

Do not combine independently observed facts into synthetic provenance unless
the source itself establishes their relationship.

## Acquisition-context authority

Acquisition context is evidence-bearing input, never caller authority.

A retailer-specific acquisition context may authorize source-evidence facts only
when deterministic verification establishes the relationship between the
captured source, store, campaign, locality, or provenance evidence involved.

Caller arguments, filenames, registry metadata, current execution time, and
historical retailer-neutral exports do not become authority merely because they
are supplied alongside a source record.

When the captured artifacts do not establish a required relationship, preserve
the observable context and fail closed.

## Retailer boundaries

Retailer-specific logic belongs in retailer adapters and source-evidence
projection boundaries.

Canonical consumers must remain retailer-neutral.

Do not add retailer-specific exceptions to generic canonical validation,
admission, querying, filtering, aggregation, profiling, or batch orchestration.

If a retailer cannot satisfy the canonical contract from available evidence,
preserve the evidence and fail closed.

## Retailer orchestration and canonical availability

A retailer or source registry, if present, is orchestration metadata only.

Registry membership may describe which retailer pipelines the current build
knows how to invoke. It must never be treated as proof that a retailer is
represented in the current canonical corpus.

Canonical retailer availability must be derived from admitted canonical records,
for example through `list_available_retailers(records)`.

Keep these states distinct:

    retailer pipeline registered
        != retailer admitted into corpus
        != retailer has current offers at as_of

Retailer-neutral structural validity is also not canonical admission.

A schema-valid retailer-neutral export must not be treated as canonical authority
unless the underlying records have passed the deterministic evidence,
verification, structural-validation, and canonical-admission boundaries required
by the current architecture.

## Source discovery

The current investigated retailer source-discovery phase is complete.

Do not resume general retailer hunting as incidental work.

New source investigation requires an explicit scoped decision.

## Fixtures and reproducibility

Committed real-source fixtures are evidence artifacts.

When a fixture has an expected SHA-256 identity, verify that identity before
using it as trusted deterministic input.

Do not rewrite fixtures to make parsers or admission succeed.

## Deterministic road test

The deterministic multi-retailer road test is a repository acceptance boundary:

    python -m grocery_deal_intelligence.road_test

It must exercise reusable core behavior rather than reimplement verification,
validation, admission, or batch-summary semantics.

Expected fail-closed retailer behavior is a successful outcome when it matches
the evidence contract.

## AI boundary

AI-assisted ingestion is optional and advisory.

The deterministic core must remain usable and testable without Ollama,
GiadaWare AI runtime, network access, or a model installation.

AI proposals remain subject to deterministic evidence verification, structural
validation, projection where applicable, and canonical admission.

Never add AI-generated authority or automatic AI repair of rejected canonical
data.

## Network boundary

Deterministic interpretation of captured evidence must not require network
access.

Network acquisition is separate from deterministic ingestion and admission.

## Change discipline

Before starting repository work:

1. read this `AGENTS.md`;
2. inspect current branch, HEAD, and working tree;
3. inspect relevant issue and PR state;
4. identify the exact authority boundary affected.

Keep changes narrowly scoped.

Prefer:

    one issue -> one branch -> one reviewed PR
        -> verified merge -> branch cleanup

## Python toolchain

Ruff is the canonical repository-owned Python linter and formatter.

The Ruff contract is defined in `pyproject.toml`.

Policy:

- lint starts from `select = ["ALL"]`;
- exceptions must be narrow, explicit, and justified by repository context;
- do not weaken domain contracts or tests merely to satisfy lint;
- do not use unsafe Ruff fixes without explicit review of their semantics;
- run `ruff check .` before final verification;
- run `ruff format --check .` before final verification;
- CI enforces both lint and formatter conformance.

Ruff is pinned deliberately. Because `ALL` may acquire new rules when Ruff is
upgraded, a Ruff version change is a reviewed toolchain-policy change rather
than incidental dependency drift.

This `AGENTS.md` is living operational documentation. Review and update it when
durable tooling, methodology, verification, architecture, workflow, or other
repository operating conventions change the canonical operating model.

## Verification discipline

For behavioral changes, verify the relevant focused tests and full test suite.

Run the deterministic road test when deterministic ingestion is affected.

Preserve source immutability, deterministic ordering, and fail-closed behavior.

Do not weaken meaningful contract tests merely to make CI pass.

## Documentation discipline

Documentation must describe current implemented architecture rather than an
obsolete historical phase.

Historical experiments may remain documented as evidence, but must not be
presented as the current preferred path.

## Historical experiments and stale branches

Before continuing work from an old branch, classify it explicitly as active
work, historical evidence, superseded work, or rejected evidence.

Do not merge stale experimental work merely because its branch still exists.

## Canonical design principle

When completeness and verifiability conflict, choose verifiability.

The repository should always make it possible to determine:

- what the source actually proved;
- what deterministic code derived;
- what was rejected;
- why it was rejected;
- what was finally admitted as canonical.

Those questions must remain answerable without trusting AI output, hidden state,
or undocumented heuristics.
