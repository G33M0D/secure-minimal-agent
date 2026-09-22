# Agent Instructions — secure-minimal-agent

Project-specific instructions for any AI coding agent working in this repo (Claude Code, Codex,
Gemini CLI). Global rules — secrets handling, `Projects/` layout, tracking-doc requirements — live
in the drive-root `/Volumes/Workspace/Claude/CLAUDE.md` and always apply on top of this file.

This repo is **public** (portfolio piece). Never add job-hunt-specific context here — that's why
PROJECT_CONTEXT.md and PLAN.md are gitignored in this repo specifically; keep any new tracking
content generic and public-appropriate the same way.

## Stack
Python. Provider-agnostic LLM client (Anthropic + OpenAI implementations). pytest for tests.

## Build & test commands
- venv lives at `~/.venvs/secure-minimal-agent` — off-drive. This drive's exFAT AppleDouble
  (`._*`) files break on-drive venvs, so always use an off-drive venv path for this project.
- `pytest` — 14 tests covering registry isolation, schema contracts, and calc AST safety.

## Conventions
- Tool access is deny-by-default through an explicit registry — never widen it implicitly.
- Answers must be composed only from evidence actually observed during the tool loop, never
  from the model's own unchecked recall.
- Arithmetic goes through the calc tool (AST-allowlisted), never raw LLM math — see README for
  the design lesson that motivated this (the model got `138×61.651` wrong).

## Do not
- Don't add job-hunt-specific content to this repo — see the note above.

## Key files
See PROJECT_CONTEXT.md's "Key facts" for the full map — don't duplicate it here.
