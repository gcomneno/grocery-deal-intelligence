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


RUN_ENV = "GROCERY_DEAL_INTELLIGENCE_RUN_MULTI_RETAILER_EXPERIMENT"
BASE_URL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_BASE_URL"
MODEL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_MODEL"

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:1.5b-instruct"

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
    result = ingest_offer(source, ai=adapter, validate=True)

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
    if validated != (canonical is not None):
        raise AssertionError(
            "deterministic gate invariant violated: validated must match canonical presence"
        )

    diagnostics = [] if validated else diagnose_candidate_rejection(candidate)

    return {
        "source_identity": copy.deepcopy(source_identity),
        "source_record": source_before,
        "candidate": candidate,
        "validated": validated,
        "canonical": canonical,
        "diagnostics": diagnostics,
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts: Counter[str] = Counter()
    accepted = 0

    for result in results:
        if result["validated"]:
            accepted += 1
        for diagnostic in result["diagnostics"]:
            category_counts[diagnostic["category"]] += 1

    return {
        "total_records": len(results),
        "accepted_records": accepted,
        "rejected_records": len(results) - accepted,
        "diagnostic_category_counts": dict(sorted(category_counts.items())),
    }


def run_experiment() -> dict[str, Any]:
    if os.environ.get(RUN_ENV) != "1":
        raise RuntimeError(f"multi-retailer AI experiment is opt-in; set {RUN_ENV}=1")

    base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)
    model = os.environ.get(MODEL_ENV, DEFAULT_MODEL)

    backend = OllamaBackend(model=model, base_url=base_url, timeout=120.0)
    capability = ProposeOfferCandidateCapability(backend)
    adapter = GiadaWareAIAdapter(capability)

    results = []
    for spec in FIXTURES:
        source, identity = load_fixture_record(spec)
        results.append(evaluate_fixture(source, identity, adapter=adapter))

    return {
        "experiment": {
            "name": "multi-retailer-real-ai-ingestion",
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
        },
    }


def main() -> int:
    evidence = run_experiment()
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
