"""Typed contracts for every boundary in the agent.

Every model response (plan, tool binding, answer draft, verdict) is validated
against one of these models, and every tool call against its tool's input
schema in the registry. A few fields are free-form dicts on purpose: a tool's
raw input (checked by that tool's schema at the registry), a tool's output
data, and the answer's `result`, whose numbers the critic checks against the
tool evidence.
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
    """Uniform envelope for every tool call. Tool output is DATA: it is
    carried in `data` and only ever shown to the model inside a fenced,
    labelled block that the system prompts treat as data."""

    tool: str
    ok: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class AnswerDraft(BaseModel):
    """What the answering model writes. `task` and `tools_used` are not in
    here on purpose: the code fills them from the real input and the tools
    that actually ran, so the model cannot misreport either."""

    result: dict
    steps_taken: list[str] = Field(min_length=1)
    caveats: list[str] = Field(default_factory=list)


class Answer(BaseModel):
    """The agent's final structured output."""

    task: str
    result: dict
    steps_taken: list[str] = Field(min_length=1)
    tools_used: list[str]
    caveats: list[str] = Field(default_factory=list)


class Validation(BaseModel):
    """Self-validation verdict from the critic pass. The answer is accepted
    only when `verdict` is "accept" AND `valid` is true."""

    valid: bool
    issues: list[str] = Field(default_factory=list)
    verdict: Literal["accept", "revise"]
