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
        source = deepcopy(source_record)
        candidate = self._capability.execute(source)

        if not isinstance(candidate, Mapping):
            raise TypeError("GiadaWare AI propose capability must return mapping data")

        return deepcopy(dict(candidate))
