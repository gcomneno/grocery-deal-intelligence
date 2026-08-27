from copy import deepcopy
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from giadaware_ai.extension import ProposeCapability


class GiadaWareAIProposalAdapter:
    """Adapt GiadaWare AI proposal capabilities to detached Proposal v0.1 data."""

    def __init__(
        self,
        capability: "ProposeCapability[dict[str, Any], Mapping[str, Any]]",
    ) -> None:
        self._capability = capability

    def propose(self, source_record):
        return self._propose(source_record)

    def propose_grounded(self, source_record, *, source_evidence):
        return self._propose(source_record, source_evidence=source_evidence)

    def _propose(self, source_record, *, source_evidence=None):
        source = deepcopy(source_record)

        if source_evidence is None:
            proposal = self._capability.execute(source)
        else:
            evidence = deepcopy(source_evidence)
            execute_grounded = getattr(self._capability, "execute_grounded", None)
            if execute_grounded is None:
                proposal = self._capability.execute(source)
            else:
                proposal = execute_grounded(source, source_evidence=evidence)

        if not isinstance(proposal, Mapping):
            raise TypeError("GiadaWare AI proposal capability must return mapping data")

        return deepcopy(dict(proposal))
