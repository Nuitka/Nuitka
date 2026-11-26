#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --mode=standalone

# Every module Nuitka provides as bytecode gets "__uncompiled__", while compiled
# modules get "__compiled__". Additionally, for Python3.11 the bytecode modules
# loaded by the Nuitka loader have to align their module dict layout with the
# compiled module and package shapes, due to a bug in the bytecode attribute
# caching there.

from __future__ import print_function

import codecs
import inspect
import json
import os
import site
import sys

import some_module
import some_package


def getKeyIndex(module, key):
    return list(module.__dict__).index(key)


def getFileFromLocalVariable():
    # Assigning "__file__" to a local variable in a function crashed the
    # optimization in standalone mode, where "__file__" becomes a path relative
    # to the program directory.
    filename = __file__
    return filename


def getFileFromChainedAssignment():
    first = second = __file__
    return first, second


def getFileFromTupleAssignment():
    first, second = __file__, __file__
    return first, second


def getFileFromClosure():
    def inner():
        return __file__

    return inner()


def getFileFromLoopAssignment():
    result = None

    for _unused in range(2):
        result = __file__

    return result


def getDunderValues():
    name = __name__
    package = __package__
    return name, package


def getLoaderValue():
    loader = __loader__
    return loader


def getSpecValue():
    spec = __spec__
    return spec


if "__compiled__" in globals():
    # Early/technical modules are stamped after they were executed.
    assert "__uncompiled__" in vars(codecs)
    assert "__compiled__" not in vars(codecs)

    # Bytecode modules loaded through the loader, including packages.
    assert "__uncompiled__" in vars(json)
    assert "__compiled__" not in vars(json)

    # Built-in modules are not provided by Nuitka.
    assert "__uncompiled__" not in vars(sys)

    # The "site" module gets a proper "__file__" into the runtime directory.
    assert site.__file__ == os.path.join(
        __compiled__.python_runtime_dir, "site.py"
    ), site.__file__

    if sys.version_info[:2] == (3, 11):
        import dataclasses

        compiled_module = some_module
        compiled_package = some_package

        # This is a targeted regression for compiled module/package alignment.
        compiled_module_builtins_index = getKeyIndex(compiled_module, "__builtins__")
        compiled_package_builtins_index = getKeyIndex(compiled_package, "__builtins__")
        assert compiled_module_builtins_index == compiled_package_builtins_index, (
            compiled_module_builtins_index,
            compiled_package_builtins_index,
            list(compiled_module.__dict__),
            list(compiled_package.__dict__),
        )

        compiled_module_file_index = getKeyIndex(compiled_module, "__file__")
        compiled_package_file_index = getKeyIndex(compiled_package, "__file__")
        assert compiled_module_file_index == compiled_package_file_index, (
            compiled_module_file_index,
            compiled_package_file_index,
            list(compiled_module.__dict__),
            list(compiled_package.__dict__),
        )

        # Bytecode modules loaded by the Nuitka loader must align with the
        # compiled ones as well, and use "__uncompiled__" instead of
        # "__compiled__".
        bytecode_module = dataclasses

        bytecode_module_builtins_index = getKeyIndex(bytecode_module, "__builtins__")
        assert bytecode_module_builtins_index == compiled_module_builtins_index, (
            bytecode_module_builtins_index,
            compiled_module_builtins_index,
            list(bytecode_module.__dict__),
            list(compiled_module.__dict__),
        )

        bytecode_module_file_index = getKeyIndex(bytecode_module, "__file__")
        assert bytecode_module_file_index == compiled_module_file_index, (
            bytecode_module_file_index,
            compiled_module_file_index,
            list(bytecode_module.__dict__),
            list(compiled_module.__dict__),
        )

        for _unused in range(32):
            inspect.getfile(compiled_module)

        package_filename = inspect.getfile(compiled_package)
        assert package_filename.endswith("__init__.py"), repr(package_filename)

assert getFileFromLocalVariable() == __file__, (getFileFromLocalVariable(), __file__)
assert getFileFromChainedAssignment() == (__file__, __file__), (
    getFileFromChainedAssignment(),
    __file__,
)
assert getFileFromTupleAssignment() == (__file__, __file__), (
    getFileFromTupleAssignment(),
    __file__,
)
assert getFileFromClosure() == __file__, (getFileFromClosure(), __file__)
assert getFileFromLoopAssignment() == __file__, (getFileFromLoopAssignment(), __file__)

assert some_module.getFileFromLocalVariable() == some_module.__file__, (
    some_module.getFileFromLocalVariable(),
    some_module.__file__,
)
assert some_package.getFileFromLocalVariable() == some_package.__file__, (
    some_package.getFileFromLocalVariable(),
    some_package.__file__,
)

name, package = getDunderValues()
assert name == __name__, (name, __name__)
assert package == __package__, (package, __package__)

if sys.version_info >= (3,):
    assert getLoaderValue() is __loader__, (getLoaderValue(), __loader__)
    assert getSpecValue() is __spec__, (getSpecValue(), __spec__)

print("OK")

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
