"""Typed contracts for every boundary in the agent.

Every hop — planner output, tool input/output, final answer — is validated
against one of these models. Nothing untyped crosses a boundary.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Subtask(BaseModel):
    """One step of the plan. `tool` must name a registered tool or be null
    for pure-reasoning steps."""

    id: int = Field(ge=1)
    description: str = Field(min_length=1, max_length=500)
    tool: Optional[str] = None
    tool_input: Optional[dict] = None


class Plan(BaseModel):
    """Planner output: the task decomposition."""

    task_summary: str = Field(min_length=1, max_length=500)
    subtasks: list[Subtask] = Field(min_length=1, max_length=10)


class ToolCallRequest(BaseModel):
    """Executor output: the resolved input for one tool call, bound against
    evidence gathered so far (e.g. a rate fetched two steps earlier)."""

    tool_input: dict


class ToolResult(BaseModel):
    """Uniform envelope for every tool call. Tool output is DATA — it is
    carried in `data` and never interpolated into prompts as instructions."""

    tool: str
    ok: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class Answer(BaseModel):
    """The agent's final structured output."""

    task: str
    result: dict
    steps_taken: list[str] = Field(min_length=1)
    tools_used: list[str]
    caveats: list[str] = Field(default_factory=list)


class Validation(BaseModel):
    """Self-validation verdict from the critic pass."""

    valid: bool
    issues: list[str] = Field(default_factory=list)
    verdict: Literal["accept", "revise"]
