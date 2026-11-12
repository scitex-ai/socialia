# Changelog

All notable changes to `socialia` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- Await FastMCP's asynchronous runner from the legacy async entry point.
  `socialia mcp start` now initializes stdio without nesting event loops; a real
  initialize/list-tools integration test covers the CLI startup path. Include
  nested Python tests in source distributions so this regression ships.

- Stop release tests when the complete `[all,dev]` dependency installation
  fails. Do not retry a reduced profile and report it as full qualification.

- Treat manual release versions as data, reject non-release refs and extra
  workflow outputs, and require stable `vX.Y.Z` tags. Test, build, publish,
  and release checkouts now select the tag explicitly, including the
  publication helper checkout.

- Classify `social_analytics_*` tools as analytics before applying the broader
  social namespace match. The analytics catalog filter now exposes its four
  tools; the social filter contains only posting/status tools. Registered tools
  and the full registry total are unchanged.

- Preserve the selected source when preparing a checked-out `develop` for
  quality auditing. Detached and feature checkouts still materialize the
  local audit baseline. Changes to the actual quality workflow now trigger
  its push gate; the audit policy and commands are unchanged.

- Honor `mcp show-installation --json` and its legacy `installation` alias:
  emit only the MCP client configuration object with placeholder credentials,
  while preserving the human-readable instructions without `--json`.

## [0.5.11]

### Changed

- **No-mocks + test-quality migration** (PR #33). The entire `tests/` tree
  is rewritten to exercise real collaborators — `unittest.mock`,
  `pytest-mock`, and `monkeypatch` are gone (PA-306 audit: 0). Every test
  now satisfies the SciTeX test-quality contract (PA-307 audit: 0):
  AAA marker comments, descriptive `>= 3`-word name, and exactly one
  assertion. Net suite: 252 passed / 3 skipped under both deterministic
  and `pytest-randomly` random orderings.
- `Twitter`, `LinkedIn`, and `GoogleAnalytics` accept new keyword-only
  collaborator hooks (`session_factory=`, `http=`) so consumers can
  inject a fake or alternative HTTP client without monkey-patching.
  Defaults preserve the previous module-level behaviour.
- `scheduler.schedule_post` / `list_scheduled` / `cancel_scheduled` /
  `run_due_jobs` accept `schedule_file=` so callers can point the
  job store at a `tmp_path` (or any other location) without mutating
  module globals.

### Fixed

- CI: `[dev]` extras now include `pytest-cov` and `pytest-randomly`, so
  the `pytest --cov=src/socialia --cov-report=xml` invocation in
  `pytest-matrix-on-ubuntu-py3-11-3-12-3-13.yml` resolves cleanly.
- Docs: `sphinx-build -W` is now warning-clean (was: 109 warnings →
  errors on every PR build). Three root causes addressed —
  `GoogleAnalytics` docstring `SOCIALIA_:` token (parsed as RST
  hyperlink), `track_event` example block (Napoleon definition-list
  parsing), and `automodule::` + per-class `autoclass::` collision in
  `docs/sphinx/api/socialia.rst`.

## [0.5.9]

- Initial CHANGELOG entry — see git log for prior history.
