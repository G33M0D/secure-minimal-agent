"""CLI entry point.

    export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY with LLM_PROVIDER=openai
    python main.py "Quote a landed price in PHP for a $120 USD order with $18 shipping"

The provider is swappable (LLM_PROVIDER=anthropic|openai) because the agent
core depends on an LLMClient interface, not a vendor SDK. Secrets are
env-only, never logged.

Structured JSON goes to stdout; progress goes to stderr, so the output is
pipeable: `python main.py "..." | jq .result`
"""
import json
import os
import sys

from agent.core import run
from agent.llm import make_client
from agent.tools.calc import SPEC as CALC
from agent.tools.fx_rate import SPEC as FX_RATE
from agent.tools.registry import ToolRegistry


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print('usage: python main.py "<business task>"', file=sys.stderr)
        return 2

    task = sys.argv[1].strip()
    if len(task) > 2000:
        print("task too long (max 2000 chars)", file=sys.stderr)
        return 2

    registry = ToolRegistry(allow_writes=False)  # this demo is read-only by policy
    registry.register(FX_RATE)
    registry.register(CALC)

    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    print(f"[agent] task: {task}", file=sys.stderr)
    print(f"[agent] provider: {provider}", file=sys.stderr)
    print(f"[agent] tools allowlisted: {registry.names()}", file=sys.stderr)

    answer = run(task, make_client(provider), registry)
    print(json.dumps(answer.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
