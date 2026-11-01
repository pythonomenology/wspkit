# Changelog

All notable changes to wspkit are recorded here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Each released section below doubles as the GitHub release notes for that
version: the release tooling extracts the section whose heading matches the
tag. Keep new entries under `Unreleased` until they ship.

## Unreleased

## [0.0.1] - 2026-11-01

### Added

- WSP server library implementing the Workflow Server Protocol over JSON-RPC,
  with the lifecycle state machine, Content-Length framing, and an asyncio
  stdio transport.
- `wsp` command line interface and a built-in venv-backed fallback
  Workflow_Tool so the CLI is useful before any tool is installed.
- Config_File adapter that exposes an arbitrary CLI over WSP through
  argv-substitution templates (`{key}`, `{argv}` splat) and per-method result
  modes (`json`, `template`, `exec`, `none`), with no runtime dependency on
  wspkit.
- Per-handler `timeout` support in the Config_File, a bounded stdin reader so
  the transport does not buffer without limit, and property-based and
  integration test suites covering the dispatcher, lifecycle, framing, and
  Config_File flows.
