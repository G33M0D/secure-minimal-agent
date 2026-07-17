"""Contract tests: the boundaries reject what they must reject."""
import pytest
from pydantic import ValidationError

from agent.schemas import Answer, Plan, Validation
from agent.tools.fx_rate import FxRateInput


def test_plan_requires_at_least_one_subtask():
    with pytest.raises(ValidationError):
        Plan(task_summary="do nothing", subtasks=[])


def test_plan_caps_subtasks_at_ten():
    subtasks = [{"id": i, "description": f"s{i}"} for i in range(1, 12)]
    with pytest.raises(ValidationError):
        Plan(task_summary="too much", subtasks=subtasks)


def test_fx_input_rejects_non_iso_codes():
    with pytest.raises(ValidationError):
        FxRateInput(base="usd; DROP TABLE", quote="PHP")
    with pytest.raises(ValidationError):
        FxRateInput(base="USDT", quote="PHP")


def test_answer_requires_steps():
    with pytest.raises(ValidationError):
        Answer(task="t", result={}, steps_taken=[], tools_used=[])


def test_validation_verdict_is_closed_enum():
    with pytest.raises(ValidationError):
        Validation(valid=True, verdict="maybe")
