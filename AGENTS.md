# Agent Guidance

You are an expert Python developer and maintainer of Nuitka. Your goal is to help develop, debug,
and maintain the Nuitka compiler.

Core rules live in `.agents/rules/` (auto-loaded via `opencode.json` and Antigravity frontmatter).
If your harness has not already injected them into context, read all three files before editing code
or running verification:

- [`.agents/rules/python-compatibility.md`](./.agents/rules/python-compatibility.md): Python 2.6/2.7
  strict syntax and stdlib constraints.
- [`.agents/rules/coding-standards.md`](./.agents/rules/coding-standards.md): Python and C style,
  naming, optional docstrings, strict "why-only" comment rules, and codegen templates.
- [`.agents/rules/verification.md`](./.agents/rules/verification.md): fast inner-loop checks, final
  auto-format/pylint/codespell gate, verification matrix, and Windows execution.

## Architecture & Codegen Map

- `nuitka/tree/` and `nuitka/nodes/`: Python AST parsing, reformulations, and node classes
  (`NodeBase`, `ExpressionBase`, `StatementBase`). Specialized Python nodes/mixins come from
  `nuitka/tools/specialize/templates_python/*.py.j2` via `bin/generate-specialized-python-code`.
- `nuitka/optimizations/`: fixed-point value-trace and type-shape optimization passes.
- `nuitka/code_generation/` and `nuitka/c_types/`: lowering node trees into C code. Specialized C
  helpers come from Jinja2 templates in `nuitka/code_generation/templates_c/*.c.j2` - never edit
  generated C or Python files without updating the `.j2` template and running the generator.
- `nuitka/build/`: SCons build scripts (`Backend.scons`, `Onefile.scons`), `include/`, and
  `static_src/` C runtime.
- `nuitka/plugins/standard/standard.nuitka-package.config.yml`: declarative package rules (implicit
  imports, data files, DLLs, anti-bloat), validated and formatted via
  `bin/autoformat-nuitka-source`.

## Planning & Workspace Hygiene

- **Planning gate:** When `.planning/` is present, respect the document lifecycle (`Drafting`,
  `Review`, `Frozen`, `Execution` in `.planning/README.md`). Never begin code implementation for a
  planning document unless its state is `Execution` or the user explicitly authorizes
  implementation.
- **Checkout hygiene:** Put all temporary reproducers, logs, and `--report=...` XML files in
  `tests/scratch/`. Treat any checkout-root `Mini*.py` scripts as local reproducers and any
  checkout-root `*-todo.md` / `*-TODO.md` files as non-authoritative notes unless explicitly asked
  about them.

## Skills

Skills are auto-discovered in `.agents/skills/*/SKILL.md`. Use the skill whose `description` matches
your task; do not maintain a manual list here.

## AI Contribution Policy

- [`CONTRIBUTING.md`](./CONTRIBUTING.md): contributor guidance for AI-assisted issues and pull
  requests.
- [`.github/PULL_REQUEST_TEMPLATE.md`](./.github/PULL_REQUEST_TEMPLATE.md): AI-generated code policy
  checklist; preserve prompts, manual verification notes, and test evidence when preparing PR text.
- **Do not auto-close issues in PRs:** PRs target `develop`, while issues are closed only once fixes
  reach `main`. Never use `Fixes #N`, `Closes #N`, or `Resolves #N` in PR bodies; use plain `- #N`
  references instead.
