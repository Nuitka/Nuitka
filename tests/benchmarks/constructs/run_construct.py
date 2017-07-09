#!/usr/bin/python
#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

import os, sys, subprocess, shutil, hashlib

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            ".."
        )
    )
)

from nuitka.tools.testing.Common import (
    my_print,
    setup,
    convertUsing2to3,
    getTempDir,
    check_output
)
from nuitka.tools.testing.Valgrind import runValgrind
from nuitka.tools.testing.Constructs import generateConstructCases

from optparse import OptionParser

parser = OptionParser()

parser.add_option(
    "--nuitka",
    action  = "store",
    dest    = "nuitka",
    default = os.environ.get("NUITKA", ""),
)

parser.add_option(
    "--cpython",
    action  = "store",
    dest    = "cpython",
    default = os.environ.get("PYTHON", sys.executable),
)

parser.add_option(
    "--code-diff",
    action  = "store",
    dest    = "diff_filename",
    default = "",
)

parser.add_option(
    "--copy-source-to",
    action  = "store",
    dest    = "target_dir",
    default = "",
)


options, positional_args = parser.parse_args()

if len(positional_args) != 1:
    sys.exit("Error, need to give test case file name as positional argument.")

test_case = positional_args[0]

if os.path.exists(test_case):
    test_case = os.path.abspath(test_case)

if options.cpython == "no":
    options.cpython = ""

nuitka = options.nuitka

if os.path.exists(nuitka):
    nuitka = os.path.abspath(nuitka)
elif nuitka:
    sys.exit("Error, nuitka binary '%s' not found." % nuitka)

python_version = setup(silent = True)

assert os.path.exists(test_case), (test_case, os.getcwd())

my_print("PYTHON='%s'" % python_version)
my_print("PYTHON_BINARY='%s'" % os.environ["PYTHON"])
my_print("TEST_CASE_HASH='%s'" % hashlib.md5(open(test_case, "rb").read()).hexdigest())


needs_2to3 = python_version.startswith('3') and \
             not test_case.endswith("32.py") and \
             not test_case.endswith("33.py")

if options.target_dir:
    shutil.copy(
        test_case,
        os.path.join(options.target_dir, os.path.basename(test_case))
    )



# First produce two variants.
temp_dir = getTempDir()

test_case_1 = os.path.join(
    temp_dir,
    "Variant1_" + os.path.basename(test_case)
)
test_case_2 = os.path.join(
    temp_dir,
    "Variant2_" + os.path.basename(test_case)
)

case_1_source, case_2_source = generateConstructCases(open(test_case).read())

with open(test_case_1, 'w') as case_1_file:
    case_1_file.write(case_1_source)

with open(test_case_2, 'w') as case_2_file:
    case_2_file.write(case_2_source)

if needs_2to3:
    test_case_1, needs_delete = convertUsing2to3(test_case_1)
    test_case_2, needs_delete = convertUsing2to3(test_case_2)

os.environ["PYTHONHASHSEED"] = '0'

if nuitka:
    nuitka_id = check_output(
        "cd %s; git rev-parse HEAD" % os.path.dirname(nuitka),
        shell = True
    )
    nuitka_id = nuitka_id.strip()

    if sys.version_info > (3,):
        nuitka_id = nuitka_id.decode()

    my_print("NUITKA_COMMIT='%s'" % nuitka_id)

os.chdir(getTempDir())

if nuitka:
    nuitka_call = [
        nuitka,
        "--python-flag=-S",
        "--python-version=" + ".".join(python_version.split(".")[:2]),
        os.path.basename(test_case)
    ]
    nuitka_call.extend(os.environ.get("NUITKA_EXTRA_OPTIONS", "").split())


    # We want to compile under the same filename to minimize differences, and
    # then copy te resulting files afterwards.
    shutil.copy(test_case_1, os.path.basename(test_case))

    subprocess.check_call(nuitka_call)

    os.rename(
        os.path.basename(test_case).replace(".py", ".build"),
        os.path.basename(test_case_1).replace(".py", ".build")
    )
    os.rename(
        os.path.basename(test_case).replace(".py", ".exe"),
        os.path.basename(test_case_1).replace(".py", ".exe")
    )

    shutil.copy(test_case_2, os.path.basename(test_case))

    subprocess.check_call(nuitka_call)

    os.rename(
        os.path.basename(test_case).replace(".py", ".build"),
        os.path.basename(test_case_2).replace(".py", ".build")
    )
    os.rename(
        os.path.basename(test_case).replace(".py", ".exe"),
        os.path.basename(test_case_2).replace(".py", ".exe")
    )

    if options.diff_filename:
        suffixes = [".c", ".cpp"]

        for suffix in suffixes:
            cpp_1 = os.path.join(
                test_case_1.replace(".py", ".build"),
                "module.__main__" + suffix,
            )

            if os.path.exists(cpp_1):
                break
        else:
            assert False

        for suffix in suffixes:

            cpp_2 = os.path.join(
                test_case_2.replace(".py", ".build"),
                "module.__main__" + suffix,
            )
            if os.path.exists(cpp_2):
                break
        else:
            assert False

        import difflib
        open(options.diff_filename,'w').write(
            difflib.HtmlDiff().make_table(
                open(cpp_1).readlines(),
                open(cpp_2).readlines(),
                "Construct",
                "Baseline",
                True
            )
        )

    nuitka_1 = runValgrind(
        "Nuitka construct",
        "callgrind",
        (test_case_1.replace(".py", ".exe"),),
        include_startup = True
    )

    nuitka_2 = runValgrind(
        "Nuitka baseline",
        "callgrind",
        (test_case_2.replace(".py", ".exe"),),
        include_startup = True
    )

    nuitka_diff = nuitka_1 - nuitka_2

    my_print("NUITKA_COMMAND='%s'" % " ".join(nuitka_call), file = sys.stderr)
    my_print("NUITKA_RAW=%s" % nuitka_1)
    my_print("NUITKA_BASE=%s" % nuitka_2)
    my_print("NUITKA_CONSTRUCT=%s" % nuitka_diff)

if options.cpython:
    cpython_1 = runValgrind(
        "CPython construct",
        "callgrind",
        (os.environ["PYTHON"], "-S", test_case_1),
        include_startup = True
    )
    cpython_2 = runValgrind(
        "CPython baseline",
        "callgrind",
        (os.environ["PYTHON"], "-S", test_case_2),
        include_startup = True
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

    my_print(
        "NUITKA_GAIN=%.3f" % nuitka_gain
    )
    my_print(
        "RAW_GAIN=%.3f" % (
            float(100 * cpython_1) / nuitka_1
        )
    )
    my_print(
        "BASE_GAIN=%.3f" % (
            float(100 * cpython_2) / nuitka_2
        )
    )
