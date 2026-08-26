from abc import ABC, abstractmethod


class OfferCandidateAdapter(ABC):
    """Read-only advisory boundary for producing candidate offer data."""

    @abstractmethod
    def propose(self, source_record):
        """Return candidate data derived from a source record."""
        raise NotImplementedError
