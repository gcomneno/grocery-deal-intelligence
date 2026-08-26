from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from giadaware_ai.backends.ollama import OllamaBackend

from grocery_deal_intelligence.giadaware_ai_adapter import GiadaWareAIAdapter
from grocery_deal_intelligence.ingestion import ingest_offer
from grocery_deal_intelligence.offer_proposal import ProposeOfferCandidateCapability


RUN_ENV = "GROCERY_DEAL_INTELLIGENCE_RUN_REAL_RETAILER_EXPERIMENT"
BASE_URL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_BASE_URL"
MODEL_ENV = "GROCERY_DEAL_INTELLIGENCE_OLLAMA_MODEL"

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:1.5b-instruct"

SOURCE_RELATIVE_PATH = Path("esselunga/all-8400.json")
SOURCE_RECORD_ID = "2_27__8400__1"
SOURCE_RECORD_CODE = "531442"


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_path() -> Path:
    return repository_root() / SOURCE_RELATIVE_PATH


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_selected_source_record() -> dict[str, Any]:
    path = source_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items")

    if not isinstance(items, list):
        raise ValueError("real retailer source payload must contain an items list")

    matches = [item for item in items if isinstance(item, dict) and item.get("id") == SOURCE_RECORD_ID]

    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one source record with id {SOURCE_RECORD_ID!r}; "
            f"found {len(matches)}"
        )

    record = copy.deepcopy(matches[0])

    if record.get("code") != SOURCE_RECORD_CODE:
        raise ValueError(
            "selected source record identity mismatch: "
            f"expected code {SOURCE_RECORD_CODE!r}, got {record.get('code')!r}"
        )

    return record


def run_experiment() -> dict[str, Any]:
    if os.environ.get(RUN_ENV) != "1":
        raise RuntimeError(
            f"real retailer AI experiment is opt-in; set {RUN_ENV}=1"
        )

    base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)
    model = os.environ.get(MODEL_ENV, DEFAULT_MODEL)

    source = load_selected_source_record()
    source_before = copy.deepcopy(source)

    backend = OllamaBackend(
        model=model,
        base_url=base_url,
        timeout=120.0,
    )
    capability = ProposeOfferCandidateCapability(backend)
    adapter = GiadaWareAIAdapter(capability)

    result = ingest_offer(source, ai=adapter, validate=True)

    if source != source_before:
        raise AssertionError("real retailer experiment mutated the source record")

    candidate = result["candidate"]
    authority_fields = {"canonical", "validated", "valid"}.intersection(candidate)
    if authority_fields:
        raise AssertionError(
            "AI candidate unexpectedly contains authority fields: "
            + ", ".join(sorted(authority_fields))
        )

    canonical = result["canonical"]
    validated = bool(result["validated"])

    if validated != (canonical is not None):
        raise AssertionError(
            "deterministic gate invariant violated: validated must match canonical presence"
        )

    return {
        "source_identity": {
            "path": SOURCE_RELATIVE_PATH.as_posix(),
            "record_id": SOURCE_RECORD_ID,
            "record_code": SOURCE_RECORD_CODE,
            "file_sha256": file_sha256(source_path()),
        },
        "source_record": source_before,
        "candidate": candidate,
        "validated": validated,
        "canonical": canonical,
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
