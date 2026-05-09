---
name: obs-build-logs
description: Access and diagnose openSUSE Build Service (OBS) package build logs. Use when the user provides a `build.opensuse.org` live build log URL, a package page, or a `project/package/repository/arch` tuple, or asks why an OBS RPM build failed. Prefer this skill for translating OBS URLs into raw log URLs, fetching public `_log` output, and finding the actual failing step instead of earlier noise.
---

# OBS Build Logs

Use the public logfile route first. The live-log page is often awkward to scrape, and the API `_log`
route may require authentication.

## Normalize The Input

Extract `project`, `package`, `repository`, and `arch` first.

- Live log page:
  `https://build.opensuse.org/package/live_build_log/<project>/<package>/<repository>/<arch>`
- Public raw logfile:
  `https://build.opensuse.org/public/build/<project>/<repository>/<arch>/<package>/_log`
- API raw logfile: `https://api.opensuse.org/build/<project>/<repository>/<arch>/<package>/_log`

Remember the ordering difference:

- `live_build_log` puts `package` second.
- Raw `_log` URLs put `package` last.

## Fetch The Log

Prefer the public raw logfile URL on `build.opensuse.org`.

- It is the route OBS uses for the web UI "Download logfile" action.
- Use the API route only when authentication is available or required.
- On Windows, do not rely on `osc` for this unless it is already known to work in the current
  environment; recent `osc` builds may fail because they import `fcntl`.

If shell access is allowed, fetch the public log directly rather than the live page.

## Read The Failure From The Bottom

Start near the end of the log and work upward.

Look for the first load-bearing failure marker near the bottom:

- `RPM build errors:`
- `Bad exit status from ...`
- `FATAL:`
- `FAILED`
- `Traceback`
- `Error, results differed`
- compiler or linker `error:`

Treat earlier lines as suspect until the final failing section confirms they matter.

Common false leads:

- early `spec file parser line ... cannot expand %(...)`
- dependency cycle output during setup
- unrelated package install warnings
- earlier warnings that do not match the terminal failure

## Classify The Failure

Map the terminal failure to one of these buckets:

1. Spec or packaging failure
2. Build dependency resolution failure
3. `%build` script failure
4. `%check` test failure
5. Compiler or linker failure
6. Runtime failure in a smoke test

State explicitly which stage failed and quote the smallest useful log fragment.

## Trace The Failure Back Into This Repository

For this repository, inspect these files first when the log points to packaging or OBS upload logic:

- `nuitka/tools/release/rpm/nuitka.spec`
- `nuitka/tools/release/osc_upload/__main__.py`
- `rpm/make-osc-upload.py`
- `rpm/check-osc-status.py`

If the failure is inside generated code, tests, or a runtime warning, inspect the named module or
test file from the log before changing packaging.

## Report The Result

Report these items in order:

1. The exact stage that failed
2. The real terminal error
3. Why earlier warnings are or are not the root cause
4. The local file or code path that should be changed
5. The most direct fix or next verification step

If the public logfile fetch fails, say which URL variant was tried and whether the failure looks
like bad path ordering, missing auth, or network restrictions.
