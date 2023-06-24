#!/usr/bin/python
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

""" Run a construct based comparison test.

This executes a program with and without snippet of code and
stores the numbers about it, extracted with Valgrind for use
in comparisons.

"""

import hashlib
import os
import sys
from optparse import OptionParser

from nuitka.tools.testing.Common import (
    check_output,
    convertUsing2to3,
    decideNeeds2to3,
    getPythonSysPath,
    getPythonVersionString,
    getTempDir,
    my_print,
    setup,
)
from nuitka.tools.testing.Constructs import generateConstructCases
from nuitka.tools.testing.Valgrind import runValgrind
from nuitka.utils.Execution import check_call
from nuitka.utils.FileOperations import (
    copyFile,
    getFileContentByLine,
    getFileContents,
    putTextFileContents,
)


def _setPythonPath(case_name):
    if "Numpy" in case_name:
        os.environ["PYTHONPATH"] = getPythonSysPath()


def main():
    # Complex stuff, not broken down yet
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    parser = OptionParser()

    parser.add_option(
        "--nuitka", action="store", dest="nuitka", default=os.environ.get("NUITKA", "")
    )

    parser.add_option(
        "--cpython",
        action="store",
        dest="cpython",
        default=os.environ.get("PYTHON", sys.executable),
    )

    parser.add_option("--code-diff", action="store", dest="diff_filename", default="")

    parser.add_option("--copy-source-to", action="store", dest="target_dir", default="")

    options, positional_args = parser.parse_args()

    if len(positional_args) != 1:
        sys.exit("Error, need to give test case file name as positional argument.")

    test_case = positional_args[0]

    if os.path.exists(test_case):
        test_case = os.path.abspath(test_case)

    case_name = os.path.basename(test_case)

    if options.cpython == "no":
        options.cpython = ""

    nuitka = options.nuitka

    if os.path.exists(nuitka):
        nuitka = os.path.abspath(nuitka)
    elif nuitka:
        sys.exit("Error, nuitka binary '%s' not found." % nuitka)

    diff_filename = options.diff_filename
    if diff_filename:
        diff_filename = os.path.abspath(diff_filename)

    setup(silent=True, go_main=False)

    _setPythonPath(case_name)

    assert os.path.exists(test_case), (test_case, os.getcwd())

    my_print("PYTHON='%s'" % getPythonVersionString())
    my_print("PYTHON_BINARY='%s'" % os.environ["PYTHON"])
    my_print(
        "TEST_CASE_HASH='%s'"
        % hashlib.md5(getFileContents(test_case, "rb")).hexdigest()
    )

    needs_2to3 = decideNeeds2to3(test_case)

    if options.target_dir:
        copyFile(
            test_case, os.path.join(options.target_dir, os.path.basename(test_case))
        )

    # First produce two variants.
    temp_dir = getTempDir()

    test_case_1 = os.path.join(temp_dir, "Variant1_" + os.path.basename(test_case))
    test_case_2 = os.path.join(temp_dir, "Variant2_" + os.path.basename(test_case))

    case_1_source, case_2_source = generateConstructCases(getFileContents(test_case))

    putTextFileContents(test_case_1, case_1_source)
    putTextFileContents(test_case_2, case_2_source)

    if needs_2to3:
        test_case_1, _needs_delete = convertUsing2to3(test_case_1)
        test_case_2, _needs_delete = convertUsing2to3(test_case_2)

    os.environ["PYTHONHASHSEED"] = "0"

    if nuitka:
        nuitka_id = check_output(
            "cd %s; git rev-parse HEAD" % os.path.dirname(nuitka), shell=True
        )
        nuitka_id = nuitka_id.strip()

        if sys.version_info > (3,):
            nuitka_id = nuitka_id.decode()

        my_print("NUITKA_COMMIT='%s'" % nuitka_id)

    os.chdir(getTempDir())

    if nuitka:
        nuitka_call = [
            os.environ["PYTHON"],
            nuitka,
            "--quiet",
            "--no-progressbar",
            "--nofollow-imports",
            "--python-flag=no_site",
        ]

        nuitka_call.extend(os.environ.get("NUITKA_EXTRA_OPTIONS", "").split())

        nuitka_call.append(case_name)

        # We want to compile under the same filename to minimize differences, and
        # then copy the resulting files afterwards.
        copyFile(test_case_1, case_name)

        check_call(nuitka_call)

        if os.path.exists(case_name.replace(".py", ".exe")):
            exe_suffix = ".exe"
        else:
            exe_suffix = ".bin"

        os.rename(
            os.path.basename(test_case).replace(".py", ".build"),
            os.path.basename(test_case_1).replace(".py", ".build"),
        )
        os.rename(
            os.path.basename(test_case).replace(".py", exe_suffix),
            os.path.basename(test_case_1).replace(".py", exe_suffix),
        )

        copyFile(test_case_2, os.path.basename(test_case))

        check_call(nuitka_call)

        os.rename(
            os.path.basename(test_case).replace(".py", ".build"),
            os.path.basename(test_case_2).replace(".py", ".build"),
        )
        os.rename(
            os.path.basename(test_case).replace(".py", exe_suffix),
            os.path.basename(test_case_2).replace(".py", exe_suffix),
        )

        if diff_filename:
            suffixes = [".c", ".cpp"]

            for suffix in suffixes:
                cpp_1 = os.path.join(
                    test_case_1.replace(".py", ".build"), "module.__main__" + suffix
                )

                if os.path.exists(cpp_1):
                    break
            else:
                assert False

            for suffix in suffixes:
                cpp_2 = os.path.join(
                    test_case_2.replace(".py", ".build"), "module.__main__" + suffix
                )
                if os.path.exists(cpp_2):
                    break
            else:
                assert False

            import difflib

            putTextFileContents(
                diff_filename,
                difflib.HtmlDiff().make_table(
                    getFileContentByLine(cpp_1),
                    getFileContentByLine(cpp_2),
                    "Construct",
                    "Baseline",
                    True,
                ),
            )

        nuitka_1 = runValgrind(
            "Nuitka construct",
            "callgrind",
            (test_case_1.replace(".py", exe_suffix),),
            include_startup=True,
        )

        nuitka_2 = runValgrind(
            "Nuitka baseline",
            "callgrind",
            (test_case_2.replace(".py", exe_suffix),),
            include_startup=True,
        )

        nuitka_diff = nuitka_1 - nuitka_2

        my_print("NUITKA_COMMAND='%s'" % " ".join(nuitka_call), file=sys.stderr)
        my_print("NUITKA_RAW=%s" % nuitka_1)
        my_print("NUITKA_BASE=%s" % nuitka_2)
        my_print("NUITKA_CONSTRUCT=%s" % nuitka_diff)

    if options.cpython:
        os.environ["PYTHON"] = options.cpython

        cpython_call = [os.environ["PYTHON"], "-S", test_case_1]

        cpython_1 = runValgrind(
            "CPython construct",
            "callgrind",
            cpython_call,
            include_startup=True,
        )

        cpython_call = [os.environ["PYTHON"], "-S", test_case_2]

        cpython_2 = runValgrind(
            "CPython baseline",
            "callgrind",
            cpython_call,
            include_startup=True,
        )

        cpython_diff = cpython_1 - cpython_2

        my_print("CPYTHON_RAW=%d" % cpython_1)
        my_print("CPYTHON_BASE=%d" % cpython_2)
        my_print("CPYTHON_CONSTRUCT=%d" % cpython_diff)

    if options.cpython and options.nuitka:
        if nuitka_diff == 0:
            nuitka_gain = float("inf")
        else:
            nuitka_gain = float(100 * cpython_diff) / nuitka_diff

        my_print("NUITKA_GAIN=%.3f" % nuitka_gain)
        my_print("RAW_GAIN=%.3f" % (float(100 * cpython_1) / nuitka_1))
        my_print("BASE_GAIN=%.3f" % (float(100 * cpython_2) / nuitka_2))


if __name__ == "__main__":
    main()
