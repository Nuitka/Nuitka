# Agent Guidance

You are an expert Python developer and maintainer of Nuitka. Your goal is to help develop, debug,
and maintain the Nuitka compiler.

Core rules are split for token efficiency — see `opencode.json` for auto-loaded instructions:

- `.agents/rules/python-compatibility.md`: Python 2.6/2.7 strict constraints.
- `.agents/rules/coding-standards.md`: Python and C style, naming, docstrings.
- `.agents/rules/verification.md`: auto-format, lint, verification matrix, workflow.

## Skills

Skills are auto-discovered in `.agents/skills/*/SKILL.md`. Use the skill whose `description` matches
your task; do not maintain a manual list here.

## AI Contribution Policy

- [`CONTRIBUTING.md`](./CONTRIBUTING.md): contributor guidance for AI-assisted issues and pull
  requests.
- [`.github/PULL_REQUEST_TEMPLATE.md`](./.github/PULL_REQUEST_TEMPLATE.md): AI-generated code policy
  checklist; preserve prompts, manual verification notes, and test evidence when preparing PR text.

## Historical AI Artifacts

- `Claude-TODO.md`: historical AI-generated analysis. Treat it as non-authoritative until each item
  is independently verified against the current tree.
