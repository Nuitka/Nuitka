---
trigger: always_on
description: Core Nuitka compiler invariants for OOM/MemoryError modeling, exception alignment, borrowed values, C runtime contracts, and node design.
---

# Compiler Invariants

## Out-of-Memory (`MemoryError`) Handling

Nuitka distinguishes between bounded routine allocations and runtime-sized allocations that can
overflow or exhaust memory:

- **Ignored (`MemoryError` not modeled):** Fixed-size, compile-time-sized, or input-bounded
  allocations are assumed to succeed. Nodes whose C helper can only fail on OOM return `False` from
  `mayRaiseException()` and `mayRaiseExceptionOperation()`, do not call
  `trace_collection.onExceptionRaiseExit(...)`, and generate `needs_check=False` (emitting an
  assertion in debug builds).
  - Examples: `MAKE_SLICE_OBJECT*`, `LIST_COPY`, `DICT_COPY`, `LIST_APPEND*`, `str.splitlines()`,
    and `str.capitalize()`.
- **Handled (`MemoryError` / `OverflowError` modeled):** Operations whose allocation size comes from
  runtime values and can overflow `Py_ssize_t` or deliberately trigger `MemoryError` (including in
  tests) **must** keep exception exits (`onExceptionRaiseExit(MemoryError)` / `BaseException`,
  `mayRaiseExceptionOperation() == True`, and `needs_check=True` in C codegen).
  - Examples: sequence repetition (`str * n`, `bytes * n`, `list * n`, `tuple * n`), `bytes(n)` /
    `bytearray(n)`, container construction from large ranges (`list(range(n))` / `tuple(range(n))`
    when length exceeds the compile-time threshold), string padding with runtime widths
    (`str.ljust`, `str.rjust`, `str.center`, `str.zfill`), `str.expandtabs`, and arbitrary-precision
    integer growth (`a ** b`, `a << b`).

## Exception Alignment

- **Derive may-raise from the node:** Code generation must query the node (for example
  `expression.mayRaiseExceptionOperation()` or `statement.mayRaiseException(BaseException)`) rather
  than hardcoding `may_raise` / `needs_check` flags.
- **Exact bidirectional agreement:** Optimization (`computeExpression` /
  `trace_collection.onExceptionRaiseExit(...)`), the node's `mayRaiseException*()` methods, and C
  code generation must agree in both directions - emit a C error exit (`needs_check=True` /
  `may_raise=True`) **if and only if** the operation can raise a modeled exception and optimization
  annotated an exception exit for it.
- **Separate operation raises from child raises:** For expression operations, implement
  `mayRaiseExceptionOperation()` to describe only the operation itself and prefer it over
  `mayRaiseException(BaseException)` in code generation so child-only exceptions do not force
  redundant error checks after the helper call.

## No Bug-Hiding or Silent Fallbacks

- Never mask broken invariants with defensive `if x is None: return None`, broad
  `try: ... except Exception:`, `getattr(env, ..., default)` probes for attributes that should be
  initialized on `env`, or silent fallback defaults (such as mapping an unknown architecture to
  `"x64"`).
- Initialize fields unconditionally where objects are created, and `assert` (or fail loudly with
  `sysexit`) when an invariant is violated.

## Borrowed-Value Protection & Temporary Lifetimes

- Whenever a code generator evaluates multiple expressions sequentially and holds an earlier
  temporary live while evaluating later expressions, wrap the evaluation in
  `withBorrowedValueScope(context)` (if not already inside one) and call
  `promoteBorrowedValue(value_name, later_expressions, emit, context)` after each earlier value.
- Variable writes, deletions, and releases (`StatementAssignmentVariable`, `StatementDelVariable`,
  `StatementReleaseVariable`) all invalidate borrowed references and must be treated uniformly by
  write-detection and promotion helpers.
- Custom or deferred temporary releases belong inside `getReleaseCode` / `DeferredReleaseCodes`,
  never as ad-hoc `Py_DECREF` followed by extra cleanup or placed after error checks and branches.

## C Runtime, Loader & Debug Contracts

- **Loader entries stay `const`:** Never store mutable runtime load state inside
  `Nuitka_MetaPathBasedLoaderEntry`; keep mutable module state in separate variables.
- **Guaranteed hard imports cannot raise:** `IMPORT_HARD_*` and direct-entry hard imports abort on
  missing standard-library modules rather than raising Python exceptions. Keep error checks omitted
  for guaranteed hard imports and assert non-`NULL` where checks are skipped.
- **Internal C helpers over CPython DLL calls:** Prefer Nuitka's own C helpers
  (`DICT_GET_ITEM0`/`1`, `Nuitka_Unicode_CompareWithASCIIString`, `CHECK_AND_CLEAR_ERROR_OCCURRED`,
  `unlikely(...)` on error branches) over slow or hookable CPython DLL calls. Do not add redundant
  `PyUnicode_Check` checks before helpers that already check it, and avoid hashing-error paths for
  known string constants.
- **Debug-only checks stay out of release builds:** Sanity magic markers, extra payload-name checks,
  and heap-preservation capacity checks belong under `#ifdef _NUITKA_DEBUG` inside a single shared
  function body (never duplicated debug/release function bodies).

## AST, Node Design & Concrete Type Checks

- **Single-pass AST visits:** Do not add extra full `ast.walk(...)` passes during tree building;
  enforce syntax and semantic checks during the regular AST visit.
- **Node mixins & constant types:** Use `SideEffectsFromChildrenMixin` when a node has no own side
  effects, use `getCompileTimeConstantType()` (overridden as `@staticmethod` on constant ref node
  classes) instead of `type(node.getCompileTimeConstant())`, and do not add unused
  `computeExpression` overrides on nodes whose computation is handled by `auto_compute_handling`.
- **Concrete type checks:** For internal concrete classes (such as C-API argument descriptors
  `CArg`, `ConstantArg`, `TupleArg`, `OptionalArg`, AST node classes, or built-in scalar/container
  types where subclasses are not expected), prefer exact `type(x) is Cls` / `type(x) in (...)`
  checks over `isinstance(...)`.
- **Versioned nodes over argument slicing:** When a Python version adds or removes a trailing node
  child (for example Python 2 vs 3 `compile` `optimize`, or Python 3.12 vs 3.13+ type parameter
  `default_value`), split the node into version-specific classes (`*Before*` / `*Since*`) with exact
  `named_children` rather than slicing `arg_desc` in code generation.
