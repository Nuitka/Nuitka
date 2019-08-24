#!/usr/bin/env python
#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

import jinja2

from nuitka.tools.testing.Common import (
    compareWithCPython,
    createSearchMode,
    decideFilenameVersionSkip,
    decideNeeds2to3,
    my_print,
    setup,
)


def _createBigConstantsTest():
    # Create large constants test on the fly.
    with open("BigConstants.py", "w") as output:
        output.write(
            "'''Automatically generated test, not part of releases or git.\n\n'''\n"
        )
        output.write("print('%s')\n" % ("1234" * 17000))


def _createOperationsTest():
    with open("Operations.py", "w") as output:
        output.write(
            "'''Automatically generated test, not part of releases or git.\n\n'''\n"
        )
        output.write("from __future__ import print_function\n\n")
        output.write("cond = 8\n\n")

        candidates = (
            ("NoneType", "None", "None"),
            ("bool", "True", "False"),
            ("int", "17", "-9"),
            ("float", "17.2", "-8"),
            ("complex", "2j", "-4j"),
            ("str", "'lala'", "'lele'"),
            ("bytes", "b'lala'", "b'lele'"),
            ("list", "[1,2]", "[3]"),
            ("tuple", "(1,2)", "(3,)"),
            ("set", "set([1,2])", "set([3])"),
            ("dict", "{1:2}", "{3:4}"),
        )

        operation_template = """
def {{operation_id}}():
    left = {{left_1}}
    right = {{right_1}}

    try:
        # We expect this to be compile time computed.
        x = left {{operation}} right
    except Exception as e: # pylint: disable=broad-except
        print("{{operation_id}} compile time occurred:", e)
    else:
        print("{{operation_id}} compile time result:", x)

    # This allows the merge trace to know the type.
    left = {{left_1}} if cond else {{left_2}}
    right = {{right_1}} if cond else {{right_2}}

    try:
        # We expect this to be compile time error checked.
        x = left {{operation}} right
    except Exception as e: # pylint: disable=broad-except
        print("{{operation_id}} runtime occurred:", e)
    else:
        print("{{operation_id}} runtime result:", x)


{{operation_id}}()

"""

        template = jinja2.Template(operation_template)

        for op_name, operation in (
            ("Add", "+"),
            ("Sub", "-"),
            ("Mul", "*"),
            ("Div", "/"),
            ("FloorDiv", "//"),
            ("Mod", "%"),
        ):
            for l_type, left_value1, left_value2 in candidates:
                for r_type, right_value1, right_value2 in candidates:
                    output.write(
                        template.render(
                            operation_id=op_name + "_" + l_type + "_" + r_type,
                            operation=operation,
                            left_1=left_value1,
                            right_1=right_value1,
                            left_2=left_value2,
                            right_2=right_value2,
                        )
                    )


def _createTests():
    result = []

    _createOperationsTest()
    result.append("Operations.py")

    _createBigConstantsTest()
    result.append("BigConstants.py")

    return result


def main():
    _python_version = setup(suite="basics", needs_io_encoding=True)

    search_mode = createSearchMode()

    filenames = _createTests()

    # Now run all the tests in this directory.
    for filename in filenames:
        assert filename.endswith(".py")

        if not decideFilenameVersionSkip(filename):
            continue

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
        else:
            my_print("Skipping", filename)

    search_mode.finish()


if __name__ == "__main__":
    main()
