#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" The hints module should contain functions to call in your code.

In reality, right now it does only contain an import tracing mechanism
that helps us with debugging.
"""

from __future__ import print_function

import os
import sys
import traceback

try:
    import __builtin__ as builtins
except ImportError:
    import builtins


original_import = __import__

_indentation = 0


def _normalizePath(path):
    path = os.path.abspath(path)

    best = None

    paths = list(sys.path)

    # Nuitka standalone mode.
    try:
        paths.append(__nuitka_binary_dir)
        paths.append(os.getcwd())
    except NameError:
        pass

    for path_entry in paths:
        path_entry = os.path.normcase(path_entry)

        if os.path.normcase(path).startswith(path_entry):
            if best is None or len(path_entry) > len(best):
                best = path_entry

    if best is not None:
        path = "$PYTHONPATH" + path[len(best) :]

    return path


def _moduleRepr(module):
    try:
        module_file = module.__file__
        module_file = module_file.replace(".pyc", ".py")

        if module_file.endswith(".so"):
            module_file = os.path.join(
                os.path.dirname(module_file),
                os.path.basename(module_file).split(".")[0] + ".so",
            )

        file_desc = "file " + _normalizePath(module_file).replace(".pyc", ".py")
    except AttributeError:
        file_desc = "built-in"

    return "<module %s %s>" % (module.__name__, file_desc)


normalize_paths = None
show_source = None


def _ourimport(
    name,
    globals=None,
    locals=None,
    fromlist=None,
    level=-1 if sys.version_info[0] < 3 else 0,
):
    builtins.__import__ = original_import

    # Singleton, pylint: disable=global-statement
    global _indentation
    try:
        _indentation += 1

        print(
            _indentation * " "
            + "called with: name=%r level=%d fromlist=%s" % (name, level, fromlist)
        )

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


def enableImportTracing(normalize_paths=True, show_source=False):
    global do_normalize_paths, do_show_source
    do_normalize_paths = normalize_paths
    do_show_source = show_source

    # pylint: disable=redefined-builtin

    builtins.__import__ = _ourimport

    # Since we swap this around, prevent it from releasing by giving it a global
    # name too, not only a local one.
    global _ourimport_reference
    _ourimport
