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

Use only information supported by the supplied source record. Do not invent
retailer, locality, provenance, dates, prices, or verification evidence.

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


class ProposeOfferCandidateCapability(ProposeCapability[Mapping[str, Any], dict[str, Any]]):
    """Propose advisory grocery-offer candidate data from one source record."""

    def execute(self, value: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise TypeError("source_record must be a mapping")

        source = deepcopy(dict(value))
        serialized_source = json.dumps(
            source,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        response_schema = _load_schema()

        raw = self._backend.generate_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=(
                "Propose candidate canonical grocery-offer data from this source "
                "record. Return candidate data only.\n\n"
                f"{serialized_source}"
            ),
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
