These are tests written to analyse the performance of certain code.

`DictionaryStructureTest.py` is a differential structural harness. It builds
two dictionaries with the same operation sequence, one using only CPython APIs
and one mixing CPython APIs with the Nuitka dictionary helpers, then compares
the internal table layout after every operation. It also exercises split instance
dictionaries: split-source merges on all supported versions, split-target
insertion, deletion, and merging on 3.4 through 3.12 through compiled subscript
operations, and split-target operations on all versions through the C helpers.
The C helper section also checks known-hash insertion and lookup, and caller
supplied equality rules. It verifies that forced-hash general keys survive
repeated resizes, which covers the constants-cache pattern. The harness has
separate ctypes layouts for the free-threaded `PyObject`, `PyDictObject`, and
`PyDictKeysObject` structures, so the same structural checks run on 3.13t
through 3.15t as well. The C concurrency harness additionally covers contention,
including known-hash set, lookup, and deletion on free-threaded builds.
Run it through Nuitka with the native interpreter, e.g. `python3.13 bin/nuitka
--run tests/codegen-analysis/DictionaryStructureTest.py`. Add
`--user-plugin=tests/codegen-analysis/DictStructurePlugin.py` to inject the C
helper tests; without it, those tests are skipped. Run the harness with
`--debug` as well, since it checks assertions on debug-only paths, e.g. the
immortal empty dictionary keys object of Python 3.14 during cloning.

`DictionaryConcurrencyTest.py` builds and runs a standalone C test that links
the Nuitka dictionary helpers directly and drives shared dictionaries from
native threads with mixed helper and CPython C-API calls. It exercises combined
tables, split instance dictionaries, collision chains, threaded set/delete,
bulk mapping and sequence updates, forced-hash set calls, and refcounts. Run it
with the interpreter whose C API should be used, for example
`python3.13t tests/codegen-analysis/DictionaryConcurrencyTest.py --gil 0`.
Use `--gil 1` to re-enable the GIL on free-threaded builds. Add `--tsan` to
build the C harness with ThreadSanitizer; TSAN runs in no-GIL mode need an
instrumented Python runtime to avoid reports from uninstrumented CPython
internals. If TSAN reports an unexpected memory mapping, rerun under
`setarch $(uname -m) -R`.
