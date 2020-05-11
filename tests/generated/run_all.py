#!/usr/bin/env python
#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

""" Runner for generated tests of Nuitka.

These tests are created on the fly, and some use Nuitka internals to
decide what to test for or how, e.g. to check that a type indeed does
have a certain slot.


"""

import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

from nuitka.tools.testing.Common import (
    compareWithCPython,
    createSearchMode,
    decideNeeds2to3,
    scanDirectoryForTestCases,
    setup,
)

# For templating.
operations = (
    ("Add", "+"),
    ("Sub", "-"),
    ("Pow", "**"),
    ("Mult", "*"),
    ("FloorDiv", "//"),
    ("Div", "/"),
    ("Mod", "%"),
    ("Pow", "**"),
    ("LShift", "<<"),
    ("RShift", ">>"),
    ("BitAnd", "&"),
    ("BitOr", "|"),
    ("BitXor", "^"),
    ("Divmod", "divmod"),
)

# For typical constant values to use in operation tests.
candidates = (
    ("NoneType", "None", "None"),
    ("bool", "True", "False"),
    ("int", "17", "-9"),
    ("float", "17.2", "-8"),
    ("complex", "2j", "-4j"),
    ("str", "'lala'", "'lele'"),
    ("bytearray", "bytearray(b'lulu')", "bytearray(b'lolo')"),
    ("list", "[1,2]", "[3]"),
    ("tuple", "(1,2)", "(3,)"),
    ("set", "set([1,2])", "set([3])"),
    ("frozenset", "frozenset([1,2])", "frozenset([3])"),
    ("dict", "{1:2}", "{3:4}"),
)

# For making an operator usage, needed because divmod is function style.
def makeOperatorUsage(operator, left, right):
    if operator == "divmod":
        return "divmod(%s, %s)" % (left, right)
    else:
        return "%s %s %s" % (left, operator, right)


def main():
    python_version = setup(suite="basics", needs_io_encoding=True)

    search_mode = createSearchMode()

    # Singleton, pylint: disable=global-statement
    global operations
    global candidates

    if python_version >= "3.5":
        operations += (("MatMult", "@"),)

    if python_version < "3":
        candidates += (("long", "17L", "-9L"),)
        candidates += (("unicode", "u'lala'", "u'lele'"),)
    else:
        candidates += (("bytes", "b'lala'", "b'lele'"),)

    template_context = {
        "operations": operations,
        "ioperations": tuple(
            operation for operation in operations if operation[0] != "Divmod"
        ),
        "candidates": candidates,
        "makeOperatorUsage": makeOperatorUsage,
    }

    # Now run all the tests in this directory.
    for filename in scanDirectoryForTestCases(".", template_context=template_context):
        extra_flags = [
            # No error exits normally, unless we break tests, and that we would
            # like to know.
            "expect_success",
            # Keep no temporary files.
            "remove_output",
            # Include imported files, mostly nothing though.
            "recurse_all",
            # Use the original __file__ value, at least one case warns about things
            # with filename included.
            "original_file",
            # Cache the CPython results for re-use, they will normally not change.
            "cpython_cache",
            # We annotate some tests, use that to lower warnings.
            "plugin_enable:pylint-warnings",
        ]

        # This test should be run with the debug Python, and makes outputs to

        active = search_mode.consider(dirname=None, filename=filename)

        if active:
            compareWithCPython(
                dirname=None,
                filename=filename,
                extra_flags=extra_flags,
                search_mode=search_mode,
                needs_2to3=decideNeeds2to3(filename),
            )

            if search_mode.abortIfExecuted():
                break

    search_mode.finish()


if __name__ == "__main__":
    main()
