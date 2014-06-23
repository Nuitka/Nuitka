#!/usr/bin/python
#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Softwar where
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

import os, sys, subprocess, shutil, md5, commands

sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath( __file__ )),
            "..",
            "..",
        )
    )
)

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

if options.cpython == "no":
    options.cpython = ""


from test_common import (
    my_print,
    setup,
    convertUsing2to3,
    getTempDir,
    decideFilenameVersionSkip,
    compareWithCPython,
    hasDebugPython
)

python_version = setup(silent = True)

assert os.path.exists(test_case), (test_case, os.getcwd())

print("PYTHON='%s'" % python_version)
print("TEST_CASE_HASH='%s'" % md5.md5(open(test_case).read()).hexdigest())


needs_2to3 = python_version.startswith("3") and \
             not test_case.endswith("32.py") and \
             not test_case.endswith("33.py")

if options.target_dir:
    shutil.copy(
        test_case,
        os.path.join(options.target_dir, os.path.basename(test_case))
    )

if needs_2to3:
    test_case = convertUsing2to3(test_case)

def runValgrind( descr, test_case, args ):
    print(descr, file=sys.stderr, end="... ")

    log_base = test_case[:-3] if test_case.endswith( ".py" ) else test_case
    log_file = log_base + ".log"

    valgrind_options = "-q --tool=callgrind --callgrind-out-file=%s" % log_file

    command = ["valgrind"] + valgrind_options.split() + list(args)

    process = subprocess.Popen(
        args   = command,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    _stdout_valgrind, stderr_valgrind = process.communicate()
    exit_valgrind = process.returncode

    assert exit_valgrind == 0, stderr_valgrind
    print("OK", file=sys.stderr)
    try:
        for line in open(log_file):
            if line.startswith( "summary:" ):
                return int(line.split()[1])

        else:
            assert False
    finally:
        os.unlink(log_file)



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

case_1_file = open(test_case_1, "w")
case_2_file = open(test_case_2, "w")

inside = False
case = 0

for line in open(test_case):
    if not inside or case == 1:
        case_1_file.write(line)
    else:
        case_1_file.write("\n")

    if "# construct_end" in line:
        inside = False

    if "# construct_alternative" in line:
        case = 2

    if not inside or case == 2:
        case_2_file.write(line)
    else:
        case_2_file.write("\n")

    if "# construct_begin" in line:
        inside = True
        case = 1

case_1_file.close()
case_2_file.close()

os.environ["PYTHONHASHSEED"] = "0"

nuitka = options.nuitka

if os.path.exists(nuitka):
    nuitka = os.path.abspath(nuitka)
elif nuitka:
    sys.exit("Error, nuitka binary not found.")

if nuitka:

    nuitka_id = commands.getoutput(
        "cd %s; git rev-parse HEAD" % os.path.dirname(nuitka)
    )
    print("NUITKA_COMMIT='%s'" % nuitka_id)

os.chdir(getTempDir())

if nuitka:
    shutil.copy(test_case_1, os.path.basename(test_case))

    subprocess.check_call(
        [ nuitka, os.path.basename(test_case) ]
    )
    os.rename(
        os.path.basename(test_case).replace(".py", ".build"),
        os.path.basename(test_case_1).replace(".py", ".build")
    )
    os.rename(
        os.path.basename(test_case).replace(".py", ".exe"),
        os.path.basename(test_case_1).replace(".py", ".exe")
    )

    shutil.copy(test_case_2, os.path.basename(test_case))
    subprocess.check_call(
        [ nuitka, os.path.basename(test_case) ]
    )
    os.rename(
        os.path.basename(test_case).replace(".py", ".build"),
        os.path.basename(test_case_2).replace(".py", ".build")
    )
    os.rename(
        os.path.basename(test_case).replace(".py", ".exe"),
        os.path.basename(test_case_2).replace(".py", ".exe")
    )

    if options.diff_filename:
        cpp_1 = os.path.join(
            test_case_1.replace(".py", ".build"),
            "module.__main__.cpp",
        )
        cpp_2 = os.path.join(
            test_case_2.replace(".py", ".build"),
            "module.__main__.cpp",
        )
        import difflib
        open(options.diff_filename,"w").write(
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
        test_case_1,
        (test_case_1.replace(".py", ".exe"),)
    )

    nuitka_2 = runValgrind(
        "Nuitka baseline",
        test_case_2,
        (test_case_2.replace(".py", ".exe"),)
    )

    nuitka_diff = nuitka_1 - nuitka_2

    print("NUITKA_RAW=%s" % nuitka_1)
    print("NUITKA_BASE=%s" % nuitka_2)
    print("NUITKA_CONSTRUCT=%s" % nuitka_diff)

if options.cpython:
    cpython_1 = runValgrind(
        "CPython construct",
        test_case_1,
        ("python", test_case_1)
    )
    cpython_2 = runValgrind(
        "CPython baseline",
        test_case_2,
        ("python", test_case_2)
    )

    cpython_diff = cpython_1 - cpython_2

    print("CPYTHON_RAW=%d" % cpython_1)
    print("CPYTHON_BASE=%d" % cpython_2)
    print("CPYTHON_CONSTRUCT=%d" % cpython_diff)

if options.cpython and options.nuitka:
    print(
        "NUITKA_GAIN=%.3f" % (
            float(100 * cpython_diff) / nuitka_diff
        )
    )
