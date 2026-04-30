---
description: Reproduce macOS issues across Python flavors, including local GitHub Actions Python execution
---

# Reproduce macOS Python Flavor Issues

Use this workflow when a Nuitka issue on macOS might depend on the Python distribution, framework
layout, or CI packaging. Typical signals are:

- Different behavior between CPython Official, Homebrew, Anaconda/Conda, and CI.
- `otool -L` differences.
- Absolute `libpython` or framework paths in standalone or app bundle outputs.
- Issue reports that mention `actions/setup-python`, `actions/python-versions`, Miniforge, or hosted
  runners.

## 1. Establish the runtime matrix first

Before reducing or patching, run the same minimal reproducer across the most relevant macOS Python
flavors in this order:

1. Python.org CPython (`Flavor: CPython Official`).
2. Homebrew Python.
3. Conda or Miniforge, if the report mentions Anaconda, Conda, Miniforge, or `CONDA_PREFIX`.
4. GitHub Actions Python, if the report specifically depends on hosted runner packaging or
   `actions/setup-python`.

Keep the reproducer, reports, extracted runtimes, and logs in `tests/scratch/`.

## 2. Use the same oracle for every flavor

Record the exact same evidence for each runtime:

1. `python bin/nuitka --version`
2. The source runtime linkage:
   - For framework builds: `otool -L <python_home>/Python`
   - For libpython builds: `otool -L <libpython.dylib>`
3. The built output linkage:
   - `otool -L <dist app main executable>`
   - If relevant, `otool -L <dist app embedded Python or libpython copy>`
4. A compilation report in `tests/scratch/` via `--report=...`

For issue 3733-like bugs, the important oracle is usually the app bundle main executable, not just
the copied framework binary.

When running in an agent or sandboxed environment, keep caches local:

```sh
env NUITKA_CACHE_DIR="$PWD/tests/scratch/cache/nuitka" \
    CCACHE_DIR="$PWD/tests/scratch/cache/ccache" \
    <python> bin/nuitka --version
```

## 3. Flavor-specific notes

### Python.org CPython

- Use the explicit framework interpreter path when possible, e.g.
  `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3`.
- Inspect the framework binary with
  `otool -L /Library/Frameworks/Python.framework/Versions/3.12/Python`.

### Homebrew Python

- Use the explicit Cellar or `opt` interpreter path, not a guessed shell alias.
- Inspect the framework binary under Homebrew, e.g.
  `/opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13/Python`.

### Conda or Miniforge

- This is the primary target when the report mentions `Anaconda Python`, Miniforge, or
  `conda-incubator/setup-miniconda`.
- Inspect the source runtime with `otool -L "$CONDA_PREFIX/lib/libpythonX.Y.dylib"`.
- Preserve the environment as closely as possible to the report before introducing any local
  simplifications.

## 4. Run GitHub Actions Python locally on macOS

Current macOS archives from `actions/python-versions` are package-based. The tarball does not
contain a ready-to-run toolcache tree. Instead, it contains:

- `setup.sh`
- `python-<version>-macos11.pkg`

The upstream setup script installs the package into `/Library/Frameworks/...` and then creates
hosted-toolcache symlinks. For local reproduction, you can avoid a system-wide install by expanding
the package payload and exposing it under a synthetic framework root.

### Download and extract

1. Download the exact archive for your architecture from the matching `actions/python-versions`
   release.
2. Extract it into `tests/scratch/gha-python-<version>/`.
3. Expand the package payload:

```sh
pkgutil --expand-full \
    tests/scratch/gha-python-<version>/python-<version>-macos11.pkg \
    tests/scratch/gha-python-<version>/pkg-expanded
```

If the release does not publish a macOS archive for the version you need, note that explicitly and
do not pretend to have matched the runtime.

### Create a synthetic framework root

```sh
mkdir -p tests/scratch/gha-python-<version>/local-root/Library/Frameworks
ln -sfn "$PWD/tests/scratch/gha-python-<version>/pkg-expanded/Python_Framework.pkg/Payload" \
    tests/scratch/gha-python-<version>/local-root/Library/Frameworks/Python.framework
```

### Use a wrapper script

Create a wrapper in `tests/scratch/` that launches the unpacked interpreter with the correct dyld
and Python home overrides:

```sh
#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gha_root="$script_dir/gha-python-3.13.13"
frameworks_root="$gha_root/local-root/Library/Frameworks"
python_home="$frameworks_root/Python.framework/Versions/3.13"
python_bin="$python_home/bin/python3.13"

export DYLD_FRAMEWORK_PATH="$frameworks_root"
export PYTHONHOME="$python_home"

exec "$python_bin" "$@"
```

### Verify you are using the unpacked runtime

Run:

```sh
tests/scratch/run_gha_python.sh -c 'import sys; print(sys.version); print(sys.executable); print(sys.prefix); print(sys.base_prefix)'
```

Checks:

- `sys.version` must match the downloaded Actions version exactly.
- `sys.prefix` and `sys.base_prefix` should point into your synthetic
  `tests/scratch/.../Library/Frameworks/Python.framework/Versions/X.Y` tree.

If direct execution of the unpacked `bin/python3.X` reports a different patch version than the
archive you downloaded, it is probably binding to an already-installed
`/Library/Frameworks/Python.framework/...` on the host. In that case:

- Use the wrapper script above.
- Debug with `DYLD_PRINT_LIBRARIES=1`.

### Caveats

- `sysconfig` may still report install-name-based paths under `/Library/Frameworks/...` for values
  like `LIBDIR`. That comes from packaging metadata and does not by itself prove the override
  failed.
- Nuitka may show `Flavor: Unknown` for this runtime. That is expected for the unpacked local
  variant.

## 5. Run the reproducer under the local Actions runtime

Once the wrapper works, use it exactly like a normal interpreter:

```sh
env NUITKA_CACHE_DIR="$PWD/tests/scratch/cache-gha/nuitka" \
    CCACHE_DIR="$PWD/tests/scratch/cache-gha/ccache" \
    tests/scratch/run_gha_python.sh bin/nuitka --version
```

Then compile the same scratch reproducer and capture the same `otool -L` evidence as for the other
flavors.

## 6. Report the result cleanly

Summarize the result by flavor:

- Whether the bug reproduced.
- The exact Python flavor and version.
- The source runtime linkage.
- The output binary linkage.
- Which flavor first reproduced, if any.

If no flavor reproduces locally, say so explicitly and identify the closest remaining gap, e.g.
Conda environment contents, GitHub runner image version, or signing/notarization steps not yet
matched.
