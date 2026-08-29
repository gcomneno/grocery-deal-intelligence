from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from grocery_deal_intelligence.carrefour_adapter import adapt_carrefour_fixture_text
from grocery_deal_intelligence.despar_adapter import adapt_despar_fixture_text
from grocery_deal_intelligence.ingestion import ingest_deterministic_source_record
from grocery_deal_intelligence.source_evidence import (
    CONTRADICTED,
    SUPPORTED,
    UNVERIFIABLE,
    summarize_claim_verification,
)


_REPO_ROOT = Path(__file__).resolve().parent.parent
_OBSERVED_AT = "2026-08-27T00:00:00Z"

_SCENARIO: tuple[dict[str, Any], ...] = (
    {
        "retailer": "carrefour",
        "fixture": _REPO_ROOT / "fixtures/carrefour/store-5190-flyer-56879.txt",
        "fixture_id": "fixtures/carrefour/store-5190-flyer-56879.txt",
        "sha256": "25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571",
        "adapter": adapt_carrefour_fixture_text,
        "product_name": "Raffo Birra Raffo Originale Conf. 3 pz da 330 ml Cad. 990 ml",
    },
    {
        "retailer": "despar",
        "fixture": _REPO_ROOT / "fixtures/despar/store-191-flyer-2026-08-13.txt",
        "fixture_id": "fixtures/despar/store-191-flyer-2026-08-13.txt",
        "sha256": "54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17",
        "adapter": adapt_despar_fixture_text,
        "product_name": "Birra Speciale Pedavena",
    },
)

_DOWNSTREAM_STAGES = (
    "normalized_attributes",
    "semantic_comparability",
    "economic_normalization",
    "price_comparison",
)


def run_business_road_test() -> dict[str, Any]:
    """Run the committed real-offer business scenario without adding authority."""
    offers = [_run_offer(spec) for spec in _SCENARIO]

    source_pass = all(
        offer["source_evidence"]["status"] == "pass" for offer in offers
    )
    admission_pass = all(
        offer["canonical_admission"]["status"] == "pass" for offer in offers
    )

    stages: list[dict[str, Any]] = [
        {
            "id": "source_evidence",
            "reached": True,
            "status": "pass" if source_pass else "fail_closed",
            "sides": {
                offer["retailer"]: offer["source_evidence"]["status"]
                for offer in offers
            },
        },
        {
            "id": "canonical_admission",
            "reached": True,
            "status": "pass" if admission_pass else "fail_closed",
            "sides": {
                offer["retailer"]: offer["canonical_admission"]["status"]
                for offer in offers
            },
            "reasons": {
                offer["retailer"]: deepcopy(
                    offer["canonical_admission"]["reasons"]
                )
                for offer in offers
                if offer["canonical_admission"]["reasons"]
            },
        },
    ]

    stopping_boundary = None
    if not source_pass:
        stopping_boundary = "source_evidence"
    elif not admission_pass:
        stopping_boundary = "canonical_admission"

    if stopping_boundary is not None:
        stages.extend(
            {
                "id": stage_id,
                "reached": False,
                "status": "not_reached",
                "reason": "upstream_authority_unavailable",
            }
            for stage_id in _DOWNSTREAM_STAGES
        )
        final = "unknown"
    else:
        # This initial scenario is intentionally bounded by current repository
        # authority. Reaching beyond canonical admission would require composing
        # additional verified inputs rather than fabricating them here.
        stages.extend(
            {
                "id": stage_id,
                "reached": False,
                "status": "not_reached",
                "reason": "scenario_not_yet_authorized_for_stage",
            }
            for stage_id in _DOWNSTREAM_STAGES
        )
        stopping_boundary = "normalized_attributes"
        final = "unknown"

    expected_stop = stopping_boundary == "canonical_admission"
    expected_despar_rejection = any(
        reason.get("code") == "structural_invalid"
        for offer in offers
        if offer["retailer"] == "despar"
        for reason in offer["canonical_admission"]["reasons"]
    )
    no_rejected_candidate_leak = all(
        stage["reached"] is False for stage in stages[2:]
    )

    return {
        "pass": source_pass
        and expected_stop
        and expected_despar_rejection
        and no_rejected_candidate_leak,
        "question": "Can GDI compare Raffo Carrefour with Pedavena Despar?",
        "final": final,
        "authorized_stopping_boundary": stopping_boundary,
        "network_required": False,
        "ai_required": False,
        "offers": offers,
        "stages": stages,
    }


def _run_offer(spec: dict[str, Any]) -> dict[str, Any]:
    fixture_path: Path = spec["fixture"]
    adapter: Callable[..., list[dict[str, Any]]] = spec["adapter"]
    text = fixture_path.read_text(encoding="utf-8")
    original = text[:]

    records = adapter(
        text,
        observed_at=_OBSERVED_AT,
        expected_sha256=spec["sha256"],
    )
    selected = [
        record for record in records if record.get("product_name") == spec["product_name"]
    ]
    if len(selected) != 1:
        raise ValueError(
            f"expected exactly one {spec['retailer']} record for {spec['product_name']!r}"
        )

    ingestion = ingest_deterministic_source_record(
        selected[0],
        retailer=spec["retailer"],
    )
    claim_counts = summarize_claim_verification(ingestion["claim_verification"])
    source_status = (
        "pass"
        if claim_counts[SUPPORTED] > 0
        and claim_counts[CONTRADICTED] == 0
        and claim_counts[UNVERIFIABLE] == 0
        else "fail_closed"
    )
    admission_status = "pass" if ingestion["canonical"] is not None else "fail_closed"

    return {
        "retailer": spec["retailer"],
        "fixture": spec["fixture_id"],
        "fixture_sha256": spec["sha256"],
        "product_name": selected[0]["product_name"],
        "price": selected[0]["price"],
        "fixture_read_only": text == original,
        "source_evidence": {
            "reached": True,
            "status": source_status,
            "claims": dict(claim_counts),
        },
        "canonical_admission": {
            "reached": True,
            "status": admission_status,
            "eligible": ingestion["admission"]["eligible"],
            "reasons": deepcopy(ingestion["admission"]["reasons"]),
            "canonical_present": ingestion["canonical"] is not None,
        },
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "=== GDI BUSINESS ROAD TEST ===",
        "",
        f"Question: {result['question']}",
        "",
    ]

    for stage in result["stages"]:
        lines.append(stage["id"].replace("_", " ").upper())
        if stage["reached"]:
            for retailer, status in stage.get("sides", {}).items():
                lines.append(f"{retailer}: {status.upper()}")
            for retailer, reasons in stage.get("reasons", {}).items():
                codes = ", ".join(reason["code"] for reason in reasons)
                lines.append(f"{retailer} reasons: {codes}")
        else:
            lines.append("NOT REACHED")
            lines.append(f"reason: {stage['reason']}")
        lines.append("")

    lines.extend(
        [
            "FINAL",
            result["final"].upper(),
            f"Authorized stopping boundary: {result['authorized_stopping_boundary']}",
            f"Business road test: {'PASS' if result['pass'] else 'FAIL'}",
            f"Network required: {'YES' if result['network_required'] else 'NO'}",
            f"AI required: {'YES' if result['ai_required'] else 'NO'}",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the fail-closed real-offer GDI business road test"
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    result = run_business_road_test()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_report(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
