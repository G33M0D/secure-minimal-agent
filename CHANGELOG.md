# Changelog

All notable changes to this project are documented here, newest first.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- 2026-10-19: 12 more offline tests (62 in all) for the fixes below.
- 2026-10-19: the overview image regenerated with the current figures (62 tests, about 820 lines of Python), every
  word checked; GitHub topics added to the repository.
- 2026-10-18: overview image at the top of the README (`docs/images/secure-minimal-agent-overview.png`) and the brief it
  was made from. Every word on it came from a claim checked against the code (regenerated on 2026-10-19 with the current figures).
- 2026-10-18: README "Known limitations" section, the tested package versions, the model-call ceiling per task and the
  exchange-rate attribution.
- 2026-10-18: 36 new offline tests (50 in all) for the reasoning loop, both model clients, the FX tool and the
  command line, plus a GitHub Actions workflow that runs them on Python 3.9 and 3.13.

### Changed

- 2026-10-19: README corrected again: the Anthropic client is described as never having sent a request, the quick-start
  comment and the note on recorded runs match the Live runs section, the test list matches the tests, and a caption
  under the overview image says it predates the fixes.
- 2026-10-19: AGENTS.md: the "Do not" list and the virtual environment note made generic.
- 2026-10-18: README corrected against the code. Only the OpenAI client has a recorded run; the injection example now
  quotes the logged value (`6165.1002`) and says which defence layer that run exercised; the audit log is described as
  storing task text verbatim; per-tenant credentials are described as a possible extension, not a feature.
- 2026-10-18: `.gitignore` now excludes `.claude/`.
- 2026-10-18: default Anthropic model is now `claude-sonnet-5-5`; `LLM_MODEL` picks another model. Runtime
  requirements have upper bounds, and pytest moved to `requirements-dev.txt`.
- 2026-10-18: public AGENTS.md rewritten without private context or machine paths.

### Fixed

- 2026-10-19: a model reply that fails validation is no longer quoted back in the retry request. Pydantic's error text
  included the rejected reply, so tags such as `</task>` could reach the prompt outside any fence; the retry now names
  only the failing fields and the reason.
- 2026-10-19: `NaN`, `Infinity` and numbers too large for a float in a model reply are refused like invalid JSON. They
  used to reach stdout and the audit log as tokens that are not JSON, and a `1e999` could pass the number check when
  the task held a number too large for a float.
- 2026-10-19: the full-width and small-form less-than signs are now escaped in tool data and in the planner's draft
  input too (they were turned into JSON escapes first, so the escaping never saw them), invisible Unicode tag
  characters are removed from untrusted text, and a lone surrogate in tool data is written as an escape so the request
  can still be sent. Other look-alike brackets are not changed: no such list is complete, and the allowlist is the hard
  control.
- 2026-10-19: the number check no longer sends back numbers copied from the task when the task writes them as `-$50`,
  with a Unicode minus, as `(500)`, as `.75%` or in a date such as `18.10.2026`.
- 2026-10-18: the Anthropic client no longer sends `temperature` (current Claude models reject it with HTTP 400),
  reads the reply's text blocks by type (a thinking block can come first), treats any stop other than `end_turn` as
  no answer, and allows 16,000 tokens because thinking counts toward the limit. The OpenAI client treats a cut-off or
  refused reply as an error too. An empty reply is retried like invalid JSON. Both clients share one JSON-and-retry
  helper.
- 2026-10-18: the output's `task` and `tools_used` are filled in by code from the real input and the tools that
  returned a result; the model can no longer misreport them.
- 2026-10-18: the critic's `valid` flag is now honoured (accept needs `valid=true`), and a revision sees its own
  previous draft as well as the feedback.
- 2026-10-18: every `<` in untrusted text (and its full-width and small-form look-alikes) is escaped before it reaches
  a prompt, so a typed `</task>` cannot close its fence, and the critic's feedback and previous draft are fenced.
- 2026-10-18: a plan step naming an unregistered tool is refused before any model call is spent on it.
- 2026-10-18: the registry rejects undeclared input fields and non-object input instead of silently dropping them.
- 2026-10-18: `calc` refuses booleans, complex and non-finite results, any whole number over 1000 bits (about 300
  digits), exponents above 1000 and `round()` digits outside -100 to 100, so `9**9**9`, `round(1, -999999999)` and long
  products of powers no longer tie up the process or crash later steps.
- 2026-10-18: every audit line carries the run's `run_id`; stale docstrings corrected.
- 2026-10-18: the number check compares whole numbers without converting them to float (a huge one used to crash the
  run), and reads a `-` after a digit as a range or date separator, not a minus sign.
- 2026-10-18: "never do arithmetic yourself" is now checked in code: a numeric field in `result` that appears in no
  tool result and not in the task sends the answer back for revision, even when the critic accepts. A live run with
  Claude Sonnet 5.5 had written a 138 USD subtotal itself and the critic had accepted it.

### Not changed

- One 2026-08-03 commit in the public history records a machine-local author address. Removing it needs a history
  rewrite, which is the owner's decision.

## 2026-10-04

### Changed

- README rewritten to match the code as it was that day (a881c69).

## 2026-09-22

### Changed

- Working state synced and the drive path updated after the rename to Workspace (56b985d).

## 2026-08-03

### Added

- AGENTS.md, CHANGELOG.md and CLAUDE.md (05c6a1a).

## 2026-07-17

### Added

- First version: plan, allowlisted tools, self-validation and structured JSON output (6b37aa0).
