# Proposal v0.1 real-retailer rerun

## Status

Issue #58 is a retained opt-in AI measurement experiment.

The deterministic ingestion path is the preferred authority path when captured
retailer evidence is already sufficient. This experiment does not replace that
path and does not make Proposal v0.1 canonical authority.

Its purpose is narrower: measure Proposal v0.1 over the exact historical
four-record real-retailer corpus and record where deterministic verification,
projection, validation, and admission accept or stop the AI proposal.

## Fixed corpus

The corpus remains exactly:

- Esselunga `2_27__8400__1`;
- Esselunga `2_27__8400__2`;
- Lidl fixture index `0`;
- Lidl fixture index `1`.

The source files are pinned before any AI backend is constructed:

~~~text
esselunga/all-8400.json
581d738dc11c5ea287c7ef1b15d88369211c203e1ef3db900dfe038c0b5a669f

lidl/data/output/lidl-lucca-current.json
a74d6ffa880b46513f90cbe22b1dccd3a99a21ed80f84680808ea4cb363500df
~~~

A hash mismatch aborts the experiment. The corpus must not silently drift.

## Path under measurement

~~~text
raw source
    -> deterministic source evidence
    -> Proposal v0.1 AI capability / adapter
    -> proposal validation
    -> Proposal claim verification
    -> deterministic Proposal-to-canonical projection
    -> canonical structural validation
    -> projected-candidate claim verification
    -> canonical admission
    -> canonical | null
~~~

Each layer remains distinct. A valid Proposal does not imply projectability;
projectability does not imply canonical validity; canonical validity does not
imply admission.

## Historical comparison baseline

Issue #42 measured the direct-canonical grounded path as:

~~~text
records:               4
structurally valid:    4
admission eligible:    4
canonical:             4
AI/candidate claims:  71
supported:            42
contradicted:          0
unverifiable:         29
~~~

This is a comparison baseline, not a target.

The Proposal experiment is explicitly allowed to produce fewer than four
canonical records. `not_projectable` is the correct result whenever required
canonical facts are not established with sufficient evidence.

Historical `0/4 projectable` behavior must also not be treated as a target:
current deterministic completion and projection behavior may legitimately
produce different results.

## Execution

The experiment requires the repository's pinned GiadaWare AI dependency, a real
Ollama service, and the configured model.

~~~bash
GROCERY_DEAL_INTELLIGENCE_RUN_PROPOSAL_PATH_EXPERIMENT=1 \
GROCERY_DEAL_INTELLIGENCE_OLLAMA_TIMEOUT=300 \
python -m experiments.run_proposal_path_real_retailer_ingestion
~~~

Defaults:

~~~text
base URL: http://127.0.0.1:11434
model:    qwen2.5:1.5b-instruct
timeout:  120 seconds
~~~

Optional runtime overrides:

~~~text
GROCERY_DEAL_INTELLIGENCE_OLLAMA_BASE_URL
GROCERY_DEAL_INTELLIGENCE_OLLAMA_MODEL
GROCERY_DEAL_INTELLIGENCE_OLLAMA_TIMEOUT
~~~

## Required evidence

For each record, retain:

- source identity and source record;
- Proposal object and validation;
- Proposal leaf-claim count;
- Proposal claim verification and semantic summary;
- projection result;
- `missing_required_claims`;
- `rejected_claims`;
- canonical structural validation when reached;
- projected-candidate claim verification when reached;
- admission result when reached;
- canonical object or `null`.

The aggregate summary records Proposal, projection, structural-validation,
admission, and canonical counts independently.

## Interpretation

The experiment answers measurement questions only:

1. How many claims does Proposal v0.1 emit?
2. How many are supported, contradicted, or unverifiable?
3. Which records are deterministically projectable?
4. Which canonical requirements stop projection?
5. Where do validation and admission stop independently?
6. How does the observed behavior compare with the historical direct-canonical
   baseline?

No prompt, schema, source-evidence, projection, validation, or admission rule may
be changed merely to improve the result.

A migration decision requires a fresh real run and recorded evidence.

## Fresh real-run evidence — 2026-08-31

A fresh opt-in run was executed against the pinned local Ollama runtime with:

~~~text
backend: giadaware_ai.backends.ollama.OllamaBackend
base URL: http://127.0.0.1:11434
model: qwen2.5:1.5b-instruct
timeout: 300.0 seconds
~~~

The complete generated JSON remained a local runtime artifact, consistent with
the repository experiment policy.

Local artifact identity:

~~~text
.artifacts/issue-58/proposal-path-real-retailer-rerun.json
SHA-256:
a5733aa045d13d8f244ba642c28c2fc41409df0c8061d67ab3f61a558170e518
~~~

Observed aggregate result:

~~~text
total records:                         4
proposal valid:                        4
proposal invalid:                      0

proposal leaf claims:                  8
proposal supported claims:             6
proposal contradicted claims:          0
proposal unverifiable claims:          2

projectable records:                   2
not projectable records:               2

structurally valid projected records:  2
admission eligible records:            2
canonical records:                     2

canonical supported claims:            42
canonical contradicted claims:         0
canonical unverifiable claims:         0
~~~

The two Esselunga records fail closed before canonical projection.

For both, the required unsupported canonical paths are:

~~~text
currency
locality.scope
locality.stores
provenance.observed_at
provenance.source_type
provenance.source_url
verification.evidence_status
verification.locality_status
~~~

The second Esselunga Proposal also emitted two unverifiable claims:

~~~text
provenance.source_type = deterministic
provenance.source_url =
https://images.services.esselunga.it/html/img_prodotti/esselunga/promo-articolo/571055.jpg
~~~

Neither record reaches canonical structural validation or admission.

The two Lidl records behave differently:

~~~text
Lidl index 0 — Controfiletti di pollo
proposal claims:       1
supported:             1
unverifiable:          0
projectable:           yes
canonical valid:       yes
admission eligible:    yes
canonical present:     yes

Lidl index 1 — Peperone Corno Sweet Palermo
proposal claims:       2
supported:             2
unverifiable:          0
projectable:           yes
canonical valid:       yes
admission eligible:    yes
canonical present:     yes
~~~

### Comparison with Issue #42

~~~text
                                  Issue #42        Issue #58 fresh run
                                  direct canonical Proposal v0.1
records                           4                4
AI/candidate leaf claims          71               8
supported claims                  42               6
contradicted claims               0                0
unverifiable claims               29               2
projectable                       n/a              2
canonical records                 4                2
~~~

The lower canonical count is not treated as a regression.

The fresh run demonstrates that Proposal v0.1 emits substantially fewer claims,
while the deterministic authority chain refuses to manufacture the required
Esselunga canonical facts that current evidence does not establish.

For the two Lidl records, deterministic source evidence and completion rules are
sufficient for Proposal projection, structural validity, admission, and
canonical output.

## Decision

The experiment supports keeping Proposal v0.1 as an optional AI-assisted
ingestion path, subject to deterministic verification and fail-closed
projection/admission.

It does not displace deterministic ingestion as the preferred path when source
records already provide sufficient explicit evidence.

No prompt tuning, Proposal schema change, source-evidence change, projection
change, canonical-schema change, or admission-policy change is justified by this
measurement.
