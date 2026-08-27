from copy import deepcopy
import json
from collections.abc import Mapping
from typing import Any

from giadaware_ai.extension import ProposeCapability

from .validation import _load_schema


_SYSTEM_PROMPT = """
You propose candidate canonical grocery-offer data from one supplied source record.

Your output is advisory candidate data only. Do not claim that it is valid,
canonical, verified, approved, or persisted.

Use only information supported by the supplied inputs. When deterministic source
evidence is supplied, treat those fields as already-supported facts and do not
contradict them. Use the raw source record only for additional candidate fields
that are not represented in the deterministic evidence.

Return JSON only as one object shaped for the Grocery Offer v0.1 contract.
The object may include these fields:

retailer
product_name
price
currency
reference_price
packaging_text
base_price_text
promotion
validity
locality
verification
provenance

Do not include authority fields such as canonical, validated, or valid.
Deterministic application validation decides canonicality after this proposal.
""".strip()


_FORBIDDEN_AUTHORITY_FIELDS = frozenset({"canonical", "validated", "valid"})


def _serialize_mapping(value: Mapping[str, Any]) -> str:
    return json.dumps(
        deepcopy(dict(value)),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


class ProposeOfferCandidateCapability(ProposeCapability[Mapping[str, Any], dict[str, Any]]):
    """Propose advisory grocery-offer candidate data from one source record."""

    def execute(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return self._execute(value, source_evidence=None)

    def execute_grounded(
        self,
        value: Mapping[str, Any],
        *,
        source_evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(source_evidence, Mapping):
            raise TypeError("source_evidence must be a mapping")
        return self._execute(value, source_evidence=source_evidence)

    def _execute(
        self,
        value: Mapping[str, Any],
        *,
        source_evidence: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise TypeError("source_record must be a mapping")

        serialized_source = _serialize_mapping(value)
        response_schema = _load_schema()

        if source_evidence is None:
            user_prompt = (
                "Propose candidate canonical grocery-offer data from this source "
                "record. Return candidate data only.\n\n"
                f"RAW SOURCE RECORD:\n{serialized_source}"
            )
        else:
            serialized_evidence = _serialize_mapping(source_evidence)
            user_prompt = (
                "Propose candidate canonical grocery-offer data using the deterministic "
                "source evidence as grounding. Do not contradict grounded fields. Use "
                "the raw source only for additional fields not represented in the "
                "evidence. Return candidate data only.\n\n"
                f"DETERMINISTIC SOURCE EVIDENCE:\n{serialized_evidence}\n\n"
                f"RAW SOURCE RECORD:\n{serialized_source}"
            )

        raw = self._backend.generate_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        if not isinstance(raw, Mapping):
            raise TypeError("offer proposal backend must return mapping data")

        candidate = deepcopy(dict(raw))
        forbidden = _FORBIDDEN_AUTHORITY_FIELDS.intersection(candidate)
        if forbidden:
            fields = ", ".join(sorted(forbidden))
            raise ValueError(f"offer proposal must not include authority fields: {fields}")

        return candidate
