"""Unit tests for the abstract CriterionAgent base class."""

from __future__ import annotations

import pytest

from conclave.agents.base import CriterionAgent
from conclave.schemas.criterion import CriterionInput, CriterionOutput, Direction, Strength
from conclave.schemas.variant import Variant


class _MockPM2Agent(CriterionAgent):
    criterion = "PM2"

    async def evaluate(self, inp: CriterionInput) -> CriterionOutput:
        return CriterionOutput(
            criterion=self.criterion,
            met=True,
            strength=Strength.SUPPORTING,
            direction=Direction.PATHOGENIC,
            rationale="Mock: absent from gnomAD",
        )


@pytest.fixture
def variant() -> Variant:
    return Variant(
        variant_id="13:32339461:A:-",
        chromosome="13",
        position=32339461,
        reference_allele="A",
        alternate_allele="-",
    )


@pytest.fixture
def agent() -> _MockPM2Agent:
    return _MockPM2Agent()


class TestCriterionAgent:
    def test_criterion_attribute(self, agent: _MockPM2Agent) -> None:
        assert agent.criterion == "PM2"

    def test_name_property(self, agent: _MockPM2Agent) -> None:
        assert agent.name == "PM2Agent"

    def test_repr(self, agent: _MockPM2Agent) -> None:
        assert "PM2" in repr(agent)

    @pytest.mark.asyncio
    async def test_evaluate_returns_output(self, agent: _MockPM2Agent, variant: Variant) -> None:
        inp = CriterionInput(variant=variant, criterion="PM2")
        out = await agent.evaluate(inp)
        assert isinstance(out, CriterionOutput)
        assert out.met
        assert out.criterion == "PM2"

    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            CriterionAgent()  # type: ignore[abstract]
