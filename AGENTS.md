# Agent Guidance

This file is the index for AI-facing guidance in this repository.

Before doing work in this repository, read and follow the rules in `.cursorrules`. If task-specific
guidance conflicts with `.cursorrules`, prefer `.cursorrules`.

## Core Rules

- `.cursorrules`: repository-wide coding, compatibility, testing, and verification rules.
- `.agent/rules/cursorrules.md`: integration shim that points agents back to `.cursorrules`.

## Workflows

Check `.agent/workflows/` for task-specific procedures:

- `.agent/workflows/create-mre.md`: create or reduce a minimal reproducer for Nuitka bugs.
- `.agent/workflows/reproduce-macos-python-flavors.md`: reproduce macOS issues across Python
  distributions and GitHub Actions Python packaging.
- `.agent/workflows/fix-module-not-found-error.md`: diagnose and fix missing implicit imports that
  cause `ModuleNotFoundError` in compiled standalone binaries.
- `.agent/workflows/create-planning-document.md`: create planning documents under `.planning/` and
  wait for explicit user authorization before implementation.

## Skills

Use the skill system when the task matches one of these entries in `.agents/skills/`:

- `.agents/skills/buildbot-log-fetcher/SKILL.md`: fetch and analyze Buildbot logs via the REST API.
- `.agents/skills/create-planning-document/SKILL.md`: skill wrapper for the planning document
  workflow.
- `.agents/skills/cpython-test-suites/SKILL.md`: work with Nuitka's adapted CPython test suite
  submodules.
- `.agents/skills/create-mre/SKILL.md`: skill wrapper for the MRE workflow.
- `.agents/skills/fix-module-not-found-error/SKILL.md`: skill wrapper for missing implicit import
  fixes.
- `.agents/skills/obs-build-logs/SKILL.md`: fetch and diagnose openSUSE Build Service logs.
- `.agents/skills/obs-build-logs/agents/openai.yaml`: UI metadata for the OBS build log skill.
- `.agents/skills/reproduce-macos-python-flavors/SKILL.md`: skill wrapper for the macOS Python
  flavor reproduction workflow.

## AI Contribution Policy

- `CONTRIBUTING.md`: contributor guidance for AI-assisted issues and pull requests.
- `.github/PULL_REQUEST_TEMPLATE.md`: AI-generated code policy checklist; preserve prompts, manual
  verification notes, and test evidence when preparing PR text.

## Historical AI Artifacts

- `Claude-TODO.md`: historical AI-generated analysis. Treat it as non-authoritative until each item
  is independently verified against the current tree.
