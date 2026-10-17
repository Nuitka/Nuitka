These are tests written to analyse the performance of certain code.

`DictionaryStructureTest.py` is a differential structural harness. It builds
two dictionaries with the same operation sequence, one using only CPython APIs
and one mixing CPython APIs with the Nuitka dictionary helpers, then compares
the internal table layout after every operation. It also exercises split instance
dictionaries: split-source merges on all supported versions, and split-target
insertion, deletion, and merging on 3.4 through 3.12. Run it through Nuitka with
the native interpreter, e.g. `python3.12 bin/nuitka --run
tests/codegen-analysis/DictionaryStructureTest.py`.
