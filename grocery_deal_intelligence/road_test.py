from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from grocery_deal_intelligence.carrefour_adapter import adapt_carrefour_fixture_text
from grocery_deal_intelligence.despar_adapter import adapt_despar_fixture_text
from grocery_deal_intelligence.ingestion import ingest_deterministic_source_records
from grocery_deal_intelligence.source_evidence import (
    CONTRADICTED,
    SUPPORTED,
    UNVERIFIABLE,
)


_REPO_ROOT = Path(__file__).resolve().parent.parent
_OBSERVED_AT = "2026-08-27T00:00:00Z"

_RETAILERS: tuple[dict[str, Any], ...] = (
    {
        "name": "carrefour",
        "fixture": _REPO_ROOT / "fixtures/carrefour/store-5190-flyer-56879.txt",
        "sha256": "25f18f28c52ae114e68bb18f93ed78d777390b0d2ebf1a070e45d99a4b52d571",
        "adapter": adapt_carrefour_fixture_text,
        "expectation": "eligible",
    },
    {
        "name": "despar",
        "fixture": _REPO_ROOT / "fixtures/despar/store-191-flyer-2026-08-13.txt",
        "sha256": "54607c3e32d3984d68b6889c522cd17486c31361a8e781f1447c5abe24edaf17",
        "adapter": adapt_despar_fixture_text,
        "expectation": "eligible",
    },
)


def run_road_test() -> dict[str, Any]:
    """Run the committed real-fixture deterministic road test."""
    retailers: list[dict[str, Any]] = []
    overall_pass = True

    for spec in _RETAILERS:
        result = _run_retailer(spec)
        retailers.append(result)
        overall_pass = overall_pass and result["pass"]

    unsupported_facts = sum(
        retailer["claims"][CONTRADICTED] + retailer["claims"][UNVERIFIABLE]
        for retailer in retailers
    )

    return {
        "pass": overall_pass and unsupported_facts == 0,
        "network_required": False,
        "ai_required": False,
        "unsupported_facts_invented": unsupported_facts,
        "retailers": retailers,
    }


def _run_retailer(spec: dict[str, Any]) -> dict[str, Any]:
    fixture_path: Path = spec["fixture"]
    adapter: Callable[..., list[dict[str, Any]]] = spec["adapter"]
    text = fixture_path.read_text(encoding="utf-8")
    original = text[:]

    records = adapter(
        text,
        observed_at=_OBSERVED_AT,
        expected_sha256=spec["sha256"],
    )
    batch = ingest_deterministic_source_records(
        records,
        retailer=spec["name"],
    )
    summary = batch["summary"]

    invariant_results = {
        "fixture_read_only": text == original,
        "all_claims_supported": (
            summary["claims"][SUPPORTED] > 0
            and summary["claims"][CONTRADICTED] == 0
            and summary["claims"][UNVERIFIABLE] == 0
        ),
        "batch_preserves_all_records": len(batch["records"]) == len(records),
    }

    if spec["expectation"] == "eligible":
        invariant_results["expected_admission_behavior"] = (
            len(records) > 0
            and summary["structurally_valid"] == len(records)
            and summary["admission_eligible"] == len(records)
            and summary["canonical_records"] == len(records)
            and not summary["rejection_reasons"]
        )
    elif spec["expectation"] == "fail_closed":
        invariant_results["expected_admission_behavior"] = (
            len(records) > 0
            and summary["structurally_valid"] == 0
            and summary["admission_eligible"] == 0
            and summary["canonical_records"] == 0
            and summary["rejection_reasons"].get("structural_invalid") == len(records)
        )
    else:
        raise ValueError(f"unknown road-test expectation: {spec['expectation']!r}")

    return {
        "retailer": spec["name"],
        "fixture": str(fixture_path.relative_to(_REPO_ROOT)),
        "offers_parsed": summary["total_records"],
        "claims": summary["claims"],
        "structurally_valid": summary["structurally_valid"],
        "admission_eligible": summary["admission_eligible"],
        "rejection_reasons": summary["rejection_reasons"],
        "invariants": invariant_results,
        "pass": all(invariant_results.values()),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = ["=== GDI DETERMINISTIC ROAD TEST ===", ""]

    for retailer in result["retailers"]:
        lines.extend(
            [
                retailer["retailer"].upper(),
                f"offers parsed:       {retailer['offers_parsed']}",
                f"claims supported:    {retailer['claims'][SUPPORTED]}",
                f"claims contradicted: {retailer['claims'][CONTRADICTED]}",
                f"claims unverifiable: {retailer['claims'][UNVERIFIABLE]}",
                f"structural valid:    {retailer['structurally_valid']}/{retailer['offers_parsed']}",
                f"canonical admission: {retailer['admission_eligible']}/{retailer['offers_parsed']} eligible",
                "rejection reasons:    " + _format_reasons(retailer["rejection_reasons"]),
                f"retailer result:     {'PASS' if retailer['pass'] else 'FAIL'}",
                "",
            ]
        )

    lines.extend(
        [
            "RESULT",
            f"pipeline behaves fail-closed: {'PASS' if result['pass'] else 'FAIL'}",
            f"unsupported facts invented:   {result['unsupported_facts_invented']}",
            f"network required:              {'YES' if result['network_required'] else 'NO'}",
            f"AI required:                   {'YES' if result['ai_required'] else 'NO'}",
        ]
    )
    return "\n".join(lines)


def _format_reasons(reasons: dict[str, int]) -> str:
    if not reasons:
        return "none"
    return ", ".join(f"{code}={count}" for code, count in reasons.items())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic real-fixture GDI road test")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    result = run_road_test()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_report(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
