"""Registry isolation properties — the security gate must hold without any LLM."""
from pydantic import BaseModel

from agent.tools.registry import ToolRegistry, ToolSpec


class EchoInput(BaseModel):
    text: str


def _echo(params: EchoInput) -> dict:
    return {"echo": params.text}


def _registry(**kwargs) -> ToolRegistry:
    reg = ToolRegistry(**kwargs)
    reg.register(ToolSpec("echo", "echoes text", EchoInput, _echo, readonly=True))
    reg.register(ToolSpec("write_db", "pretend write", EchoInput, _echo, readonly=False))
    return reg


def test_unknown_tool_is_refused():
    result = _registry().call("shell_exec", {"text": "rm -rf /"})
    assert not result.ok
    assert "not in allowlist" in result.error


def test_write_tool_refused_when_writes_disabled():
    result = _registry(allow_writes=False).call("write_db", {"text": "x"})
    assert not result.ok
    assert "side effects" in result.error


def test_write_tool_allowed_only_with_explicit_optin():
    result = _registry(allow_writes=True).call("write_db", {"text": "x"})
    assert result.ok


def test_malformed_input_rejected_not_passed():
    result = _registry().call("echo", {"text": {"$ne": 1}})
    assert not result.ok
    assert "input rejected" in result.error


def test_wellformed_call_succeeds():
    result = _registry().call("echo", {"text": "hello"})
    assert result.ok and result.data == {"echo": "hello"}


def test_tool_exception_becomes_data_not_crash():
    def boom(params: EchoInput) -> dict:
        raise RuntimeError("upstream down")

    reg = ToolRegistry()
    reg.register(ToolSpec("boom", "always fails", EchoInput, boom))
    result = reg.call("boom", {"text": "x"})
    assert not result.ok
    assert "upstream down" in result.error
