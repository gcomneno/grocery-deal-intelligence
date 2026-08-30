import json
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from giadaware_ai.extension import ProposeCapability

from .proposal_validation import _load_proposal_schema, validate_proposal

_SYSTEM_PROMPT = """
You propose advisory grocery-offer claims from one supplied source record.

Return JSON only as a Grocery Deal Intelligence Proposal v0.1 object.
A proposal is partial and advisory: include only claims you choose to make from
the supplied information. Missing fields are valid and mean that no claim is made.
Do not try to complete a canonical Grocery Offer. Do not include authority fields.

When deterministic source evidence is supplied, treat it as grounded facts and do
not contradict it. Use the raw source record only for additional claims that are
not represented in the deterministic evidence.
""".strip()


def _serialize_mapping(value: Mapping[str, Any]) -> str:
    return json.dumps(
        deepcopy(dict(value)),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


class ProposeOfferProposalCapability(
    ProposeCapability[Mapping[str, Any], dict[str, Any]]
):
    """Produce advisory Proposal v0.1 data without canonical authority."""

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
        if source_evidence is None:
            user_prompt = (
                "Propose only supported grocery-offer claims from this source record. "
                "Omit fields for which you make no claim.\n\n"
                f"RAW SOURCE RECORD:\n{serialized_source}"
            )
        else:
            serialized_evidence = _serialize_mapping(source_evidence)
            user_prompt = (
                "Propose only supported grocery-offer claims. Treat deterministic "
                "source evidence as grounded facts and do not contradict it. Omit "
                "fields for which you make no claim.\n\n"
                f"DETERMINISTIC SOURCE EVIDENCE:\n{serialized_evidence}\n\n"
                f"RAW SOURCE RECORD:\n{serialized_source}"
            )

        raw = self._backend.generate_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=_load_proposal_schema(),
        )

        if not isinstance(raw, Mapping):
            raise TypeError("offer proposal backend must return mapping data")

        proposal = deepcopy(dict(raw))
        validation = validate_proposal(proposal)
        if not validation["valid"]:
            raise ValueError(f"invalid Proposal v0.1 output: {validation['errors']}")

        return proposal
