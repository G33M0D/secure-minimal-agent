# Changelog

All notable changes to this project are documented here, newest first.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- 2026-10-18: overview image at the top of the README (`docs/images/secure-minimal-agent-overview.png`) and the brief it
  was made from. Every word on it comes from a claim checked against the code.
- 2026-10-18: README "Known limitations" section, the tested package versions, the model-call ceiling per task and the
  exchange-rate attribution.

### Changed

- 2026-10-18: README corrected against the code. Only the OpenAI client has a recorded run; the injection example now
  quotes the logged value (`6165.1002`) and says which defence layer that run exercised; the prompt fences are described
  as labels, not escaping; extra tool-input fields are dropped, not rejected; the audit log stores task text verbatim;
  per-tenant credentials are described as a possible extension, not a feature.
- 2026-10-18: `.gitignore` now excludes `.claude/`.

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
