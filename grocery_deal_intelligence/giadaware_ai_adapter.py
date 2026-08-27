from copy import deepcopy
from typing import TYPE_CHECKING, Any, Mapping

from grocery_deal_intelligence.ai_adapter import OfferCandidateAdapter

if TYPE_CHECKING:
    from giadaware_ai.extension import ProposeCapability


class GiadaWareAIAdapter(OfferCandidateAdapter):
    """Translate GiadaWare AI proposal results into advisory candidate data."""

    def __init__(
        self,
        capability: "ProposeCapability[dict[str, Any], Mapping[str, Any]]",
    ) -> None:
        self._capability = capability

    def propose(self, source_record):
        """Return detached candidate data without granting canonical authority."""
        return self._propose(source_record)

    def propose_grounded(self, source_record, *, source_evidence):
        """Return detached candidate data grounded by deterministic evidence."""
        return self._propose(source_record, source_evidence=source_evidence)

    def _propose(self, source_record, *, source_evidence=None):
        source = deepcopy(source_record)

        if source_evidence is None:
            candidate = self._capability.execute(source)
        else:
            evidence = deepcopy(source_evidence)
            execute_grounded = getattr(self._capability, "execute_grounded", None)
            if execute_grounded is None:
                candidate = self._capability.execute(source)
            else:
                candidate = execute_grounded(source, source_evidence=evidence)

        if not isinstance(candidate, Mapping):
            raise TypeError("GiadaWare AI propose capability must return mapping data")

        return deepcopy(dict(candidate))
