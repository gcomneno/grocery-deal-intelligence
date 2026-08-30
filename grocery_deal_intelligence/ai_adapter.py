from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class OfferCandidateAdapter(ABC):
    """Read-only advisory boundary for producing candidate offer data."""

    @abstractmethod
    def propose(self, source_record: Mapping[str, Any]) -> dict[str, Any]:
        """Return candidate data derived from a source record."""
        raise NotImplementedError

    def propose_grounded(
        self,
        source_record: Mapping[str, Any],
        *,
        source_evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Return candidate data with optional deterministic evidence grounding.

        Adapters that do not implement grounded proposal semantics remain
        backward-compatible by delegating to the legacy source-only proposal.
        """
        return self.propose(source_record)
