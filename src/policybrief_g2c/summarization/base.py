from __future__ import annotations

from abc import ABC, abstractmethod

from policybrief_g2c.models import PolicyDocument, SummaryResult


class Summarizer(ABC):
    @abstractmethod
    def summarize(self, document: PolicyDocument) -> SummaryResult:
        """Create a validated summary for a policy document."""
