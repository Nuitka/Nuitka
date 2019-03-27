#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

from __future__ import print_function
import sys, os

original_import = __import__

_indentation = 0

def _normalizePath(path):
    path = os.path.abspath(path)

    best = None

    for path_entry in sys.path:
        if path.startswith(path_entry):
            if best is None or len(path_entry) > len(best):
                best = path_entry

    if best is not None:
        path = path.replace(best, "$PYTHONPATH")

    return path

def _moduleRepr(module):
    try:
        module_file = module.__file__
        module_file = module_file.replace(".pyc", ".py")

        if module_file.endswith(".so"):
            module_file = os.path.join(
                os.path.dirname(module_file),
                os.path.basename(module_file).split(".")[0] + ".so"
            )

        file_desc = "file " + _normalizePath(module_file).replace(".pyc", ".py")
    except AttributeError:
        file_desc = "built-in"

    return "<module %s %s>" % (
        module.__name__,
        file_desc
    )

def enableImportTracing(normalize_paths = True, show_source = False):

    def _ourimport(name, globals = None, locals = None, fromlist = None,  # @ReservedAssignment
                   level = -1 if sys.version_info[0] < 2 else 0):
        builtins.__import__ = original_import

        global _indentation
        try:
            _indentation += 1

            print(_indentation * " " + "called with: name=%r level=%d fromlist=%s" % (name, level, fromlist))

            for entry in traceback.extract_stack()[:-1]:
                if entry[2] == "_ourimport":
                    print(_indentation * " " + "by __import__")
                else:
                    entry = list(entry)

                    if not show_source:
                        del entry[-1]
                        del entry[-1]

                    if normalize_paths:
                        entry[0] = _normalizePath(entry[0])

                    print(_indentation * " " + "by " + "|".join(str(s) for s in entry))

            print(_indentation * " " + "*" * 40)

            builtins.__import__ = _ourimport
            try:
                result = original_import(name, globals, locals, fromlist, level)
            except ImportError as e:
                print(_indentation * " " + "EXCEPTION:", e)
                raise
            finally:
                builtins.__import__ = original_import

            print(_indentation * " " + "RESULT:", _moduleRepr(result))
            print(_indentation * " " + "*" * 40)

            builtins.__import__ = _ourimport

            return result
        finally:
            _indentation -= 1
    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins

    import traceback
    builtins.__import__ = _ourimport
