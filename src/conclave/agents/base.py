"""Abstract base class for all CONCLAVE criterion agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from conclave.schemas.criterion import CriterionInput, CriterionOutput


class CriterionAgent(ABC):
    """Abstract contract that every criterion agent must satisfy.

    Subclasses implement :meth:`evaluate` to assess one ACMG/AMP criterion
    for a given variant and return a structured :class:`CriterionOutput`.
    """

    #: The ACMG/AMP criterion code handled by this agent (e.g. ``"PM2"``).
    criterion: ClassVar[str]

    @abstractmethod
    async def evaluate(self, inp: CriterionInput) -> CriterionOutput:
        """Evaluate the criterion for the given variant input.

        Parameters
        ----------
        inp:
            All information needed to assess the criterion, including the
            variant representation and any pre-fetched evidence.

        Returns
        -------
        CriterionOutput
            Structured result including whether the criterion is met,
            the evidence strength, a rationale, and an optional abstention flag.
        """

    @property
    def name(self) -> str:
        """Human-readable agent name derived from the criterion code."""
        return f"{self.criterion}Agent"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} criterion={self.criterion!r}>"
