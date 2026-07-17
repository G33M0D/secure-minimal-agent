"""Tool registry — the agent's only gateway to the outside world.

Isolation model:
- Deny-by-default allowlist: a tool must be registered here to be callable.
  The model can *name* any tool it likes; resolution happens in this file,
  in code the model cannot influence.
- Input validation: every call is validated against the tool's input schema
  before execution. Malformed or unexpected fields are rejected, not passed.
- Read-only flags: side-effecting tools must be registered with
  `readonly=False` and are refused unless the run explicitly allows writes
  (this demo registers none — the write path exists to show the gate).
- Output as data: results are wrapped in ToolResult envelopes. Tool output is
  never fed back to the model as instructions — only as fenced, labeled data.
"""
from dataclasses import dataclass
from typing import Callable, Optional, Type

from pydantic import BaseModel, ValidationError

from agent.schemas import ToolResult


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Type[BaseModel]
    fn: Callable[[BaseModel], dict]
    readonly: bool = True


class ToolRegistry:
    def __init__(self, allow_writes: bool = False) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._allow_writes = allow_writes

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"duplicate tool name: {spec.name}")
        self._tools[spec.name] = spec

    def names(self) -> list[str]:
        return sorted(self._tools)

    def describe(self) -> str:
        """Human/model-readable catalog used in the planner prompt."""
        return "\n".join(
            f"- {t.name}: {t.description} "
            f"(input schema: {t.input_schema.model_json_schema()['properties']})"
            for t in self._tools.values()
        )

    def call(self, name: str, raw_input: Optional[dict]) -> ToolResult:
        """The single choke point for tool execution."""
        spec = self._tools.get(name)
        if spec is None:
            return ToolResult(tool=name, ok=False, error=f"unknown tool: {name!r} (not in allowlist)")
        if not spec.readonly and not self._allow_writes:
            return ToolResult(tool=name, ok=False, error=f"tool {name!r} has side effects; writes are disabled for this run")
        try:
            validated = spec.input_schema.model_validate(raw_input or {})
        except ValidationError as exc:
            return ToolResult(tool=name, ok=False, error=f"input rejected: {str(exc)[:300]}")
        try:
            return ToolResult(tool=name, ok=True, data=spec.fn(validated))
        except Exception as exc:  # tool failure is data, not a crash
            return ToolResult(tool=name, ok=False, error=f"tool failed: {str(exc)[:300]}")
