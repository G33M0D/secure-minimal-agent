# Agent Instructions: secure-minimal-agent

Project-specific instructions for any AI coding agent working in this repo (Claude Code, Codex,
Gemini CLI). The maintainer's global agent rules (secrets handling, folder layout, tracking docs) apply
on top of this file.

This repo is **public**. Keep everything in tracked files generic and safe for anyone to read.
PROJECT_CONTEXT.md and PLAN.md are the maintainer's local notes and are gitignored on purpose: never
commit them, and never copy private context from them into tracked files.

## Stack
Python 3.9 or newer. Provider-agnostic LLM client (Anthropic and OpenAI implementations). Pydantic v2
contracts. pytest for tests; GitHub Actions runs them on every push to main and every pull request.

## Build & test commands
- `pip install -r requirements-dev.txt` (runtime packages plus pytest).
- `python -m pytest tests/`: the whole suite runs offline, with no API key and no network.
- Keep the virtual environment outside the repo when it sits on an exFAT drive (for example in a folder
  under your home directory): macOS writes `._*` files there that break virtual environments.

## Conventions
- Tool access is deny-by-default through an explicit registry. Never widen it implicitly.
- Answers must be composed only from evidence actually observed during the tool loop, never from the
  model's own unchecked recall. The output's `task` and `tools_used` are filled in by code.
- Arithmetic goes through the calc tool (AST-allowlisted), never raw LLM math. See the README for the
  design lesson behind this.
- Untrusted text reaches a prompt only through `_fence()` in `agent/core.py`.
- No em or en dashes in new text.

## Do not
- Do not add private or client context to any tracked file.
- Do not register a write-capable tool without the `allow_writes` gate and a test for it.

## Key files
See the "Project structure" table in README.md.
