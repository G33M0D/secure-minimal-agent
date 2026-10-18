"""The command line refuses bad input and missing configuration before any model call."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(tmp_path, *args, **env_extra):
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LLM_PROVIDER", "LLM_MODEL")}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(ROOT / "main.py"), *args],
        capture_output=True, text=True, env=env, cwd=tmp_path, timeout=60,
    )


def test_missing_blank_or_too_long_task_exits_2_with_nothing_on_stdout(tmp_path):
    for args in [(), ("   ",), ("x" * 2001,)]:
        result = _run(tmp_path, *args)
        assert result.returncode == 2 and result.stdout == ""


def test_missing_api_key_fails_before_any_output_or_audit(tmp_path):
    result = _run(tmp_path, "How many PHP is 100 USD?")
    assert result.returncode == 1 and result.stdout == ""
    assert "ANTHROPIC_API_KEY is not set" in result.stderr
    assert not (tmp_path / "runs").exists()


def test_unknown_provider_is_refused(tmp_path):
    result = _run(tmp_path, "task", LLM_PROVIDER="acme")
    assert result.returncode == 1 and "unknown LLM provider" in result.stderr


def test_llm_model_is_reported_before_the_client_is_created(tmp_path):
    result = _run(tmp_path, "task", LLM_MODEL="claude-test")
    assert "[agent] model: claude-test" in result.stderr
    assert result.returncode == 1 and result.stdout == ""  # no key, so it stops there
