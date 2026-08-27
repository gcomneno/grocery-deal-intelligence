from __future__ import annotations

import copy
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from giadaware_ai.backends.ollama import OllamaBackend

from grocery_deal_intelligence.diagnostics import diagnose_candidate_rejection
from grocery_deal_intelligence.giadaware_ai_adapter import GiadaWareAIAdapter
from grocery_deal_intelligence.ingestion import ingest_offer
from grocery_deal_intelligence.offer_proposal import ProposeOfferCandidateCapability
from grocery_deal_intelligence.source_evidence import (
    CONTRADICTED,
    SUPPORTED,
    UNVERIFIABLE,
    summarize_claim_verification,
)


RUN_ENV = "GROCERY_DEAL_INTELLIGENCE_RUN_MULTI_RETAILER_EXPERIMENT"
BASE_URL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_BASE_URL"
MODEL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_MODEL"
TIMEOUT_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_TIMEOUT"

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:1.5b-instruct"
DEFAULT_TIMEOUT = 120.0

FIXTURES = (
    {
        "retailer": "esselunga",
        "path": "esselunga/all-8400.json",
        "selector": {"kind": "item_id", "value": "2_27__8400__1"},
        "expected": {"code": "531442"},
    },
    {
        "retailer": "esselunga",
        "path": "esselunga/all-8400.json",
        "selector": {"kind": "item_id", "value": "2_27__8400__2"},
        "expected": {"code": "571055"},
    },
    {
        "retailer": "lidl",
        "path": "lidl/data/output/lidl-lucca-current.json",
        "selector": {"kind": "list_index", "value": 0},
        "expected": {"product_name": "Controfiletti di pollo"},
    },
    {
        "retailer": "lidl",
        "path": "lidl/data/output/lidl-lucca-current.json",
        "selector": {"kind": "list_index", "value": 1},
        "expected": {"product_name": "Peperone Corno Sweet Palermo"},
    },
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_payload(relative_path: str) -> tuple[Path, Any]:
    path = repository_root() / relative_path
    return path, json.loads(path.read_text(encoding="utf-8"))


def load_fixture_record(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    path, payload = _load_payload(spec["path"])
    selector = spec["selector"]

    if selector["kind"] == "item_id":
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            raise ValueError(f"fixture payload {spec['path']} must contain an items list")
        matches = [
            item
            for item in payload["items"]
            if isinstance(item, dict) and item.get("id") == selector["value"]
        ]
        if len(matches) != 1:
            raise ValueError(
                f"fixture {spec['path']} selector {selector!r} matched {len(matches)} records"
            )
        record = matches[0]
    elif selector["kind"] == "list_index":
        if not isinstance(payload, list):
            raise ValueError(f"fixture payload {spec['path']} must be a list")
        index = selector["value"]
        if not isinstance(index, int) or index < 0 or index >= len(payload):
            raise ValueError(f"fixture index out of range for {spec['path']}: {index!r}")
        record = payload[index]
        if not isinstance(record, dict):
            raise ValueError(f"fixture record at index {index} must be an object")
    else:
        raise ValueError(f"unsupported fixture selector: {selector!r}")

    for field, expected_value in spec.get("expected", {}).items():
        if record.get(field) != expected_value:
            raise ValueError(
                f"fixture identity mismatch for {spec['path']}: "
                f"expected {field}={expected_value!r}, got {record.get(field)!r}"
            )

    identity = {
        "retailer": spec["retailer"],
        "path": spec["path"],
        "selector": copy.deepcopy(selector),
        "expected": copy.deepcopy(spec.get("expected", {})),
        "file_sha256": file_sha256(path),
    }
    return copy.deepcopy(record), identity


def evaluate_fixture(
    source: dict[str, Any],
    source_identity: dict[str, Any],
    *,
    adapter: GiadaWareAIAdapter,
) -> dict[str, Any]:
    source_before = copy.deepcopy(source)
    result = ingest_offer(
        source,
        ai=adapter,
        validate=True,
        admission=True,
        retailer=source_identity["retailer"],
    )

    if source != source_before:
        raise AssertionError("multi-record experiment mutated a source record")

    candidate = result["candidate"]
    authority_fields = {"canonical", "validated", "valid"}.intersection(candidate)
    if authority_fields:
        raise AssertionError(
            "AI candidate unexpectedly contains authority fields: "
            + ", ".join(sorted(authority_fields))
        )

    validated = bool(result["validated"])
    canonical = result["canonical"]
    structural_validation = result["structural_validation"]
    source_evidence = result["source_evidence"]
    claim_verification = result["claim_verification"]
    admission = result["admission"]

    if validated != bool(structural_validation["valid"]):
        raise AssertionError("validated must reflect structural_validation.valid")
    if (canonical is not None) != bool(admission["eligible"]):
        raise AssertionError("canonical presence must match admission eligibility")

    diagnostics = [] if validated else diagnose_candidate_rejection(candidate)
    semantic_summary = summarize_claim_verification(claim_verification)

    return {
        "source_identity": copy.deepcopy(source_identity),
        "source_record": source_before,
        "candidate": candidate,
        "validated": validated,
        "structural_validation": structural_validation,
        "canonical": canonical,
        "diagnostics": diagnostics,
        "source_evidence": source_evidence,
        "claim_verification": claim_verification,
        "semantic_summary": semantic_summary,
        "admission": admission,
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts: Counter[str] = Counter()
    semantic_counts: Counter[str] = Counter()
    admission_reason_counts: Counter[str] = Counter()
    structurally_valid = 0
    admission_eligible = 0
    canonical_records = 0

    for result in results:
        if result["validated"]:
            structurally_valid += 1
        if result["admission"]["eligible"]:
            admission_eligible += 1
        if result["canonical"] is not None:
            canonical_records += 1
        for diagnostic in result["diagnostics"]:
            category_counts[diagnostic["category"]] += 1
        for status in (SUPPORTED, CONTRADICTED, UNVERIFIABLE):
            semantic_counts[status] += result["semantic_summary"][status]
        for reason in result["admission"]["reasons"]:
            admission_reason_counts[reason["code"]] += 1

    total_claims = sum(semantic_counts.values())
    return {
        "total_records": len(results),
        "structurally_valid_records": structurally_valid,
        "structurally_invalid_records": len(results) - structurally_valid,
        "admission_eligible_records": admission_eligible,
        "admission_ineligible_records": len(results) - admission_eligible,
        "canonical_records": canonical_records,
        "diagnostic_category_counts": dict(sorted(category_counts.items())),
        "admission_reason_counts": dict(sorted(admission_reason_counts.items())),
        "total_claims": total_claims,
        "supported_claims": semantic_counts[SUPPORTED],
        "contradicted_claims": semantic_counts[CONTRADICTED],
        "unverifiable_claims": semantic_counts[UNVERIFIABLE],
    }


def run_experiment() -> dict[str, Any]:
    if os.environ.get(RUN_ENV) != "1":
        raise RuntimeError(f"multi-retailer AI experiment is opt-in; set {RUN_ENV}=1")

    base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)
    model = os.environ.get(MODEL_ENV, DEFAULT_MODEL)
    timeout = float(os.environ.get(TIMEOUT_ENV, DEFAULT_TIMEOUT))

    backend = OllamaBackend(model=model, base_url=base_url, timeout=timeout)
    capability = ProposeOfferCandidateCapability(backend)
    adapter = GiadaWareAIAdapter(capability)

    results = []
    for spec in FIXTURES:
        source, identity = load_fixture_record(spec)
        results.append(evaluate_fixture(source, identity, adapter=adapter))

    return {
        "experiment": {
            "name": "multi-retailer-real-ai-ingestion-with-canonical-admission",
            "fixture_count": len(FIXTURES),
            "fixture_order": [
                {
                    "retailer": spec["retailer"],
                    "path": spec["path"],
                    "selector": copy.deepcopy(spec["selector"]),
                }
                for spec in FIXTURES
            ],
        },
        "fixtures": results,
        "summary": summarize_results(results),
        "runtime_metadata": {
            "backend": "giadaware_ai.backends.ollama.OllamaBackend",
            "base_url": base_url,
            "model": model,
            "timeout": timeout,
        },
    }


def main() -> int:
    evidence = run_experiment()
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
