#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Global constant values.

"""

from nuitka import Options
from nuitka.__past__ import long
from nuitka.PythonVersions import python_version


def getConstantDefaultPopulation():
    """These are values for non-trivial constants.

    Constants that have a direct name, e.g. Py_True are trivial, these are for things that must
    be constructed through code.
    """

    # Lots of cases, pylint: disable=too-many-branches

    # Note: Can't work with set here, because we need to put in some values that
    # cannot be hashed.

    result = [
        # Basic values that the helper code uses all the times.
        (),
        {},
        0,
        1,
        -1,
        # Some math operations shortcut to these
        0.0,
        -0.0,
        1.0,
        -1.0,
        long(0),
        "",
        # For Python3 empty bytes, no effect for Python2, same as "", used for
        # code objects.
        b"",
        # Python mechanics, used in various helpers.
        "__module__",
        "__class__",
        "__name__",
        "__package__",
        "__metaclass__",
        "__dict__",
        "__doc__",
        "__file__",
        "__path__",
        "__enter__",
        "__exit__",
        "__builtins__",
        "__all__",
        "__cmp__",
        "__iter__",
        # Nuitka specific
        "__compiled__",
        # Patched module name.
        "inspect",
        # Names of built-ins used in helper code.
        "compile",
        "range",
        "open",
        "sum",
        "format",
        "__import__",
        "bytearray",
        "staticmethod",
        "classmethod",
        # Arguments of __import__ built-in used in helper code.
        "name",
        "globals",
        "locals",
        "fromlist",
        "level",
        # Meta path based loader.
        "read",
        "rb",
    ]

    # Pickling of instance methods.
    if python_version < 0x340:
        result += ("__newobj__",)
    else:
        result += ("getattr",)

    if python_version >= 0x300:
        # For Python3 modules
        result += ("__cached__", "__loader__")

        # For Python3 print
        result += ("print", "end", "file")

        # For Python3 "bytes" built-in.
        result.append("bytes")

    # For meta path based loader, iter_modules and Python3 "__name__" to
    # "__package__" parsing
    result.append(".")

    if python_version >= 0x300:
        # Modules have that attribute starting with Python3
        result.append("__loader__")

    if python_version >= 0x340:
        result.append(
            # YIELD_FROM uses this starting 3.4, with 3.3 other code is used.
            "send"
        )

    if python_version >= 0x300:
        result += (
            # YIELD_FROM uses this
            "throw",
            "close",
        )

    if python_version < 0x300:
        # For patching Python2 internal class type
        result += ("__getattr__", "__setattr__", "__delattr__")

        # For setting Python2 "sys" attributes for current exception
        result += ("exc_type", "exc_value", "exc_traceback")

    # The xrange built-in is Python2 only.
    if python_version < 0x300:
        result.append("xrange")

    # Executables only
    if not Options.shallMakeModule():
        # The "site" module is referenced in inspect patching.
        result.append("site")

    # Built-in original values
    if not Options.shallMakeModule():
        result += ("type", "len", "range", "repr", "int", "iter")

        if python_version < 0x300:
            result.append("long")

    if python_version >= 0x340:
        # Work with the __spec__ module attribute.
        result += ("__spec__", "_initializing", "parent")

    if python_version >= 0x350:
        # Patching the types module.
        result.append("types")

    if not Options.shallMakeModule():
        result.append("__main__")

    if python_version >= 0x370:
        result.append("__class_getitem__")

    return result
