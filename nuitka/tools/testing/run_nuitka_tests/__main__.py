#!/usr/bin/env python
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

""" Main front-end to the tests of Nuitka.

Has many options, read --help output.
"""

import os
import subprocess
import sys
from optparse import OptionParser

from nuitka.freezer.Onefile import checkOnefileReadiness
from nuitka.tools.Basics import goHome
from nuitka.tools.testing.Common import (
    getTempDir,
    my_print,
    withExtendedExtraOptions,
)
from nuitka.utils.Execution import (
    check_call,
    check_output,
    getExecutablePath,
    getNullOutput,
    getPythonExePathWindows,
)
from nuitka.utils.FileOperations import (
    getFileContents,
    openTextFile,
    putTextFileContents,
    withDirectoryChange,
)
from nuitka.utils.Timing import TimerReport
from nuitka.utils.Utils import hasOnefileSupportedOS, hasStandaloneSupportedOS


def parseOptions():
    # There are freaking many options to honor,
    # pylint: disable=too-many-branches,too-many-statements

    parser = OptionParser()

    parser.add_option(
        "--skip-basic-tests",
        action="store_false",
        dest="basic_tests",
        default=True,
        help="""\
The basic tests, execute these to check if Nuitka is healthy.
Default is %default.""",
    )

    parser.add_option(
        "--skip-syntax-tests",
        action="store_false",
        dest="syntax_tests",
        default=True,
        help="""\
The syntax tests, execute these to check if Nuitka handles Syntax errors fine.
Default is %default.""",
    )

    parser.add_option(
        "--skip-program-tests",
        action="store_false",
        dest="program_tests",
        default=True,
        help="""\
The programs tests, execute these to check if Nuitka handles programs, e.g.
import recursions, etc. fine. Default is %default.""",
    )

    parser.add_option(
        "--skip-package-tests",
        action="store_false",
        dest="package_tests",
        default=True,
        help="""\
The packages tests, execute these to check if Nuitka handles packages, e.g.
import recursions, etc. fine. Default is %default.""",
    )

    parser.add_option(
        "--skip-plugins-tests",
        action="store_false",
        dest="plugin_tests",
        default=True,
        help="""\
The plugins tests, execute these to check if Nuitka handles its own plugin
interfaces, e.g. user plugins, etc. fine. Default is %default.""",
    )

    parser.add_option(
        "--skip-optimizations-tests",
        action="store_false",
        dest="optimization_tests",
        default=True,
        help="""\
The optimization tests, execute these to check if Nuitka does optimize certain
constructs fully away. Default is %default.""",
    )

    parser.add_option(
        "--skip-standalone-tests",
        action="store_false",
        dest="standalone_tests",
        default=hasStandaloneSupportedOS(),
        help="""\
The standalone tests, execute these to check if Nuitka standalone mode, e.g.
not referring to outside, important 3rd library packages like PyQt fine.
Default is %default.""",
    )

    parser.add_option(
        "--skip-onefile-tests",
        action="store_false",
        dest="onefile_tests",
        default=hasOnefileSupportedOS(),
        help="""\
The onefile tests, execute these to check if Nuitka works in onefile mode, e.g.
not referring to outside, important 3rd library packages like PyQt fine.
Default is %default.""",
    )

    parser.add_option(
        "--skip-reflection-test",
        action="store_false",
        dest="reflection_test",
        default=True,
        help="""\
The reflection test compiles Nuitka with Nuitka, and then Nuitka with the
compile Nuitka and compares the outputs. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython26-tests",
        action="store_false",
        dest="cpython26",
        default=True,
        help="""\
The standard CPython2.6 test suite. Execute this for all corner cases to be
covered. With Python 2.7 this covers exception behavior quite well. Default
is %default.""",
    )

    parser.add_option(
        "--skip-cpython27-tests",
        action="store_false",
        dest="cpython27",
        default=True,
        help="""\
The standard CPython2.7 test suite. Execute this for all corner cases to be
covered. With Python 2.6 these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython32-tests",
        action="store_false",
        dest="cpython32",
        default=True,
        help="""\
The standard CPython3.2 test suite. Execute this for all corner cases to be
covered. With Python 2.6 these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython33-tests",
        action="store_false",
        dest="cpython33",
        default=True,
        help="""\
The standard CPython3.3 test suite. Execute this for all corner cases to be
covered. With Python 2.x these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython34-tests",
        action="store_false",
        dest="cpython34",
        default=True,
        help="""\
The standard CPython3.4 test suite. Execute this for all corner cases to be
covered. With Python 2.x these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython35-tests",
        action="store_false",
        dest="cpython35",
        default=True,
        help="""\
The standard CPython3.5 test suite. Execute this for all corner cases to be
covered. With Python 2.x these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython36-tests",
        action="store_false",
        dest="cpython36",
        default=True,
        help="""\
The standard CPython3.6 test suite. Execute this for all corner cases to be
covered. With Python 2.x these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython37-tests",
        action="store_false",
        dest="cpython37",
        default=True,
        help="""\
The standard CPython3.7 test suite. Execute this for all corner cases to be
covered. With Python 2.x these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython38-tests",
        action="store_false",
        dest="cpython38",
        default=True,
        help="""\
The standard CPython3.8 test suite. Execute this for all corner cases to be
covered. With Python 2.x these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython39-tests",
        action="store_false",
        dest="cpython39",
        default=True,
        help="""\
The standard CPython3.9 test suite. Execute this for all corner cases to be
covered. With Python 2.x these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-cpython310-tests",
        action="store_false",
        dest="cpython310",
        default=True,
        help="""\
The standard CPython3.10 test suite. Execute this for all corner cases to be
covered. With Python 2.x these are not run. Default is %default.""",
    )

    parser.add_option(
        "--skip-other-cpython-tests",
        action="store_true",
        dest="cpython_no_other",
        default=False,
        help="""\
Do not execute any CPython test suite other than the one matching the running
Python. Default is %default.""",
    )

    parser.add_option(
        "--skip-all-cpython-tests",
        action="store_true",
        dest="cpython_none",
        default=False,
        help="""\
Do not execute any CPython test suite other than the one matching the running
Python. Default is %default.""",
    )

    parser.add_option(
        "--no-other-python",
        action="store_true",
        dest="no_other",
        default=False,
        help="""\
Do not use any other Python than the one running, even if available on
the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python2.6",
        action="store_true",
        dest="no26",
        default=False,
        help="""\
Do not use Python2.6 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python2.7",
        action="store_true",
        dest="no27",
        default=False,
        help="""\
Do not use Python2.7 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python3.3",
        action="store_true",
        dest="no33",
        default=False,
        help="""\
Do not use Python3.3 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python3.4",
        action="store_true",
        dest="no34",
        default=False,
        help="""\
Do not use Python3.4 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python3.5",
        action="store_true",
        dest="no35",
        default=False,
        help="""\
Do not use Python3.5 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python3.6",
        action="store_true",
        dest="no36",
        default=False,
        help="""\
Do not use Python3.6 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python3.7",
        action="store_true",
        dest="no37",
        default=False,
        help="""\
Do not use Python3.7 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python3.8",
        action="store_true",
        dest="no38",
        default=False,
        help="""\
Do not use Python3.8 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python3.9",
        action="store_true",
        dest="no39",
        default=False,
        help="""\
Do not use Python3.9 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--no-python3.10",
        action="store_true",
        dest="no310",
        default=False,
        help="""\
Do not use Python3.10 even if available on the system. Default is %default.""",
    )

    parser.add_option(
        "--coverage",
        action="store_true",
        dest="coverage",
        default=False,
        help="""\
Make a coverage analysis, that does not really check. Default is %default.""",
    )

    parser.add_option(
        "--no-debug",
        action="store_false",
        dest="debug",
        default=True,
        help="""\
Make a coverage analysis, that does not really check. Default is %default.""",
    )

    parser.add_option(
        "--assume-yes-for-downloads",
        action="store_true",
        dest="assume_yes_for_downloads",
        default=False,
        help="""\
Allow Nuitka to download code if necessary, e.g. dependency walker on Windows. Default is %default.""",
    )

    parser.add_option(
        "--mingw64",
        action="store_true",
        dest="mingw64",
        default=False,
        help="""\
Enforce the use of MinGW64 on Windows. Defaults to off.""",
    )

    options, positional_args = parser.parse_args()

    if positional_args:
        parser.print_help()

        sys.exit("\nError, no positional argument allowed.")

    if options.no_other:
        if sys.version_info[0:2] != (2, 6):
            options.no26 = True
        if sys.version_info[0:2] != (2, 7):
            options.no27 = True
        if sys.version_info[0:2] != (3, 3):
            options.no33 = True
        if sys.version_info[0:2] != (3, 4):
            options.no34 = True
        if sys.version_info[0:2] != (3, 5):
            options.no35 = True
        if sys.version_info[0:2] != (3, 6):
            options.no36 = True
        if sys.version_info[0:2] != (3, 7):
            options.no37 = True
        if sys.version_info[0:2] != (3, 8):
            options.no38 = True
        if sys.version_info[0:2] != (3, 9):
            options.no39 = True
        if sys.version_info[0:2] != (3, 10):
            options.no310 = True

    if options.cpython_no_other:
        if sys.version_info[0:2] != (2, 6):
            options.cpython26 = False
        if sys.version_info[0:2] != (2, 7):
            options.cpython27 = False
        if sys.version_info[0:2] != (3, 2):
            options.cpython32 = False
        if sys.version_info[0:2] != (3, 3):
            options.cpython33 = False
        if sys.version_info[0:2] != (3, 4):
            options.cpython34 = False
        if sys.version_info[0:2] != (3, 5):
            options.cpython35 = False
        if sys.version_info[0:2] != (3, 6):
            options.cpython36 = False
        if sys.version_info[0:2] != (3, 7):
            options.cpython37 = False
        if sys.version_info[0:2] != (3, 8):
            options.cpython38 = False
        if sys.version_info[0:2] != (3, 9):
            options.cpython39 = False
        if sys.version_info[0:2] != (3, 10):
            options.cpython310 = False

    if options.cpython_none:
        options.cpython26 = False
        options.cpython27 = False
        options.cpython32 = False
        options.cpython33 = False
        options.cpython34 = False
        options.cpython35 = False
        options.cpython36 = False
        options.cpython37 = False
        options.cpython38 = False
        options.cpython39 = False
        options.cpython310 = False

    if options.coverage and os.path.exists(".coverage"):
        os.unlink(".coverage")

    return options


def publishCoverageData():
    def copyToGlobalCoverageData(source, target):
        coverage_dir = os.environ.get("COVERAGE_DIR")

        if coverage_dir is None:
            return

        check_call(("scp", source, os.path.join(coverage_dir, target)))

    if os.name == "nt":
        suffix = "win"
    else:
        import platform

        suffix = platform.uname()[0] + "." + platform.uname()[4]

    with openTextFile("data.coverage", "w") as data_file:
        source_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

        with withDirectoryChange(source_dir):
            nuitka_id = check_output("git rev-parse HEAD".split())
        nuitka_id = nuitka_id.strip()

        if sys.version_info > (3,):
            nuitka_id = nuitka_id.decode()

        data_file.write("NUITKA_SOURCE_DIR=%r\n" % source_dir)
        data_file.write("NUITKA_COMMIT=%r\n" % nuitka_id)

    copyToGlobalCoverageData("data.coverage", "meta.coverage." + suffix)

    def makeCoverageRelative(filename):
        """Normalize coverage data."""

        data = getFileContents(filename)

        data = data.replace(
            (os.path.abspath(".") + os.path.sep).replace("\\", "\\\\"), ""
        )

        if os.path.sep != "/":
            data.replace(os.path.sep, "/")

        putTextFileContents(filename, contents=data)

    coverage_file = os.environ.get("COVERAGE_FILE", ".coverage")

    makeCoverageRelative(coverage_file)
    copyToGlobalCoverageData(coverage_file, "data.coverage." + suffix)


def main():
    # There are many cases to deal with,
    # pylint: disable=too-many-branches,too-many-statements

    # Lets honor this Debian option here.
    if "nocheck" in os.environ.get("DEB_BUILD_OPTIONS", "").split():
        my_print("Skipped all tests as per DEB_BUILD_OPTIONS environment.")
        sys.exit(0)

    # Make sure our resolving of "python2" to "python" doesn't get in the way.
    os.environ["PYTHON_DISALLOW_AMBIGUOUS_VERSION"] = "0"

    goHome()

    options = parseOptions()

    # Add the local bin directory to search path start.
    os.environ["PATH"] = (
        os.path.join(os.getcwd(), "bin") + os.pathsep + os.environ["PATH"]
    )

    def checkExecutableCommand(command):
        """Check if a command is executable."""

        # Many cases, pylint: disable=too-many-branches,too-many-return-statements

        # Do respect given options to disable specific Python versions
        if command == "python2.6" and options.no26:
            return False
        if command == "python2.7" and options.no27:
            return False
        if command == "python3.3" and options.no33:
            return False
        if command == "python3.4" and options.no34:
            return False
        if command == "python3.5" and options.no35:
            return False
        if command == "python3.6" and options.no36:
            return False
        if command == "python3.7" and options.no37:
            return False
        if command == "python3.8" and options.no38:
            return False
        if command == "python3.9" and options.no39:
            return False
        if command == "python3.10" and options.no310:
            return False

        # Shortcuts for python versions, also needed for Windows as it won't have
        # the version number in the Python binaries at all.
        if command == "python2.6" and sys.version_info[0:2] == (2, 6):
            return True
        if command == "python2.7" and sys.version_info[0:2] == (2, 7):
            return True
        if command == "python3.3" and sys.version_info[0:2] == (3, 3):
            return True
        if command == "python3.4" and sys.version_info[0:2] == (3, 4):
            return True
        if command == "python3.5" and sys.version_info[0:2] == (3, 5):
            return True
        if command == "python3.6" and sys.version_info[0:2] == (3, 6):
            return True
        if command == "python3.7" and sys.version_info[0:2] == (3, 7):
            return True
        if command == "python3.8" and sys.version_info[0:2] == (3, 8):
            return True
        if command == "python3.9" and sys.version_info[0:2] == (3, 9):
            return True
        if command == "python3.10" and sys.version_info[0:2] == (3, 10):
            return True

        path = os.environ["PATH"]

        suffixes = (".exe",) if os.name == "nt" else ("",)

        for part in path.split(os.pathsep):
            if not part:
                continue

            for suffix in suffixes:
                if os.path.exists(os.path.join(part, command + suffix)):
                    return True

        if os.name == "nt":
            if command.startswith("python"):
                remainder = command[6:]

                if len(remainder) == 3 and remainder[1] == ".":
                    command = getPythonExePathWindows(search=remainder, arch=None)

                    return True

        return False

    def getExtraFlags(where, name, flags):
        if options.assume_yes_for_downloads and name in ("onefile", "standalone"):
            yield "--assume-yes-for-downloads"

        if os.name == "nt" and options.mingw64:
            yield "--mingw64"

        if where is not None:
            tmp_dir = getTempDir()

            where = os.path.join(tmp_dir, name, where)

            if not os.path.exists(where):
                os.makedirs(where)

            yield "--output-dir=%s" % where

        yield flags

    def executeSubTest(command, hide_output=False):
        with TimerReport(
            message="Overall execution of %r took %%.2f seconds" % command
        ):
            _executeSubTest(command, hide_output)

    def _executeSubTest(command, hide_output):
        if options.coverage and "search" in command:
            command = command.replace("search", "coverage")

        parts = command.split()
        parts[0] = parts[0].replace("/", os.path.sep)

        # The running Python will be good enough, on some platforms there is no
        # "python", and we need to pass this alone then.
        parts.insert(0, sys.executable)

        my_print("Run '%s' in '%s'." % (" ".join(parts), os.getcwd()))

        if hide_output:
            result = subprocess.call(parts, stdout=getNullOutput())
        else:
            result = subprocess.call(parts)

        if result != 0:
            sys.exit(result)

    def execute_tests(where, use_python, flags):
        # Many cases, pylint: disable=too-many-branches,too-many-statements

        my_print(
            "Executing test case called '%s' with CPython '%s' and extra flags '%s'."
            % (where, use_python, flags)
        )

        intended_version = use_python[6:]
        if sys.version.startswith(intended_version):
            os.environ["PYTHON"] = sys.executable
        else:
            if os.name == "nt":
                os.environ["PYTHON"] = getPythonExePathWindows(
                    search=intended_version, arch=None
                )
            else:
                os.environ["PYTHON"] = getExecutablePath(use_python)

        if options.basic_tests:
            my_print(
                "Running the basic tests with options '%s' with '%s':"
                % (flags, use_python)
            )
            with withExtendedExtraOptions(*getExtraFlags(where, "basics", flags)):
                executeSubTest("./tests/basics/run_all.py search")

        if options.syntax_tests:
            my_print(
                "Running the syntax tests with options '%s' with '%s':"
                % (flags, use_python)
            )
            with withExtendedExtraOptions(*getExtraFlags(where, "syntax", flags)):
                executeSubTest("./tests/syntax/run_all.py search")

        if options.program_tests:
            my_print(
                "Running the program tests with options '%s' with '%s':"
                % (flags, use_python)
            )
            with withExtendedExtraOptions(*getExtraFlags(where, "programs", flags)):
                executeSubTest("./tests/programs/run_all.py search")

        if options.package_tests:
            my_print(
                "Running the package tests with options '%s' with '%s':"
                % (flags, use_python)
            )
            with withExtendedExtraOptions(*getExtraFlags(where, "packages", flags)):
                executeSubTest("./tests/packages/run_all.py search")

        if options.plugin_tests:
            my_print(
                "Running the plugin tests with options '%s' with '%s':"
                % (flags, use_python)
            )
            with withExtendedExtraOptions(*getExtraFlags(where, "plugins", flags)):
                executeSubTest("./tests/plugins/run_all.py search")

        # At least one Debian Jessie, these versions won't have lxml installed, so
        # don't run them there. Also these won't be very version dependent in their
        # results.
        if use_python != "python2.6":
            if options.optimization_tests:
                my_print(
                    "Running the optimizations tests with options '%s' with '%s':"
                    % (flags, use_python)
                )
                with withExtendedExtraOptions(
                    *getExtraFlags(where, "optimizations", flags)
                ):
                    executeSubTest("./tests/optimizations/run_all.py search")

        if options.standalone_tests and not options.coverage:
            my_print(
                "Running the standalone tests with options '%s' with '%s':"
                % (flags, use_python)
            )
            with withExtendedExtraOptions(*getExtraFlags(None, "standalone", flags)):
                executeSubTest("./tests/standalone/run_all.py search")

        if options.onefile_tests and not options.coverage:
            if checkOnefileReadiness(
                assume_yes_for_downloads=options.assume_yes_for_downloads
            ):
                my_print(
                    "Running the onefile tests with options '%s' with '%s':"
                    % (flags, use_python)
                )
                with withExtendedExtraOptions(*getExtraFlags(None, "onefile", flags)):
                    executeSubTest("./tests/onefile/run_all.py search")
            else:
                my_print("The onefile tests are not run due to missing requirements.")

        if options.reflection_test and not options.coverage:
            my_print(
                "Running the reflection test with options '%s' with '%s':"
                % (flags, use_python)
            )
            with withExtendedExtraOptions(*getExtraFlags(None, "reflected", flags)):
                executeSubTest("./tests/reflected/compile_itself.py search")

        if not use_python.startswith("python3"):
            if os.path.exists("./tests/CPython26/run_all.py"):
                if options.cpython26:
                    my_print(
                        "Running the CPython 2.6 tests with options '%s' with '%s':"
                        % (flags, use_python)
                    )

                    with withExtendedExtraOptions(
                        *getExtraFlags(where, "26tests", flags)
                    ):
                        executeSubTest("./tests/CPython26/run_all.py search")
            else:
                my_print("The CPython2.6 tests are not present, not run.")

            # Running the Python 2.7 test suite with CPython 2.6 gives little
            # insight, because "importlib" will not be there and that's it.
            if use_python != "python2.6":
                if os.path.exists("./tests/CPython27/run_all.py"):
                    if options.cpython27:
                        my_print(
                            "Running the CPython 2.7 tests with options '%s' with '%s':"
                            % (flags, use_python)
                        )
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "27tests", flags)
                        ):
                            executeSubTest("./tests/CPython27/run_all.py search")
                else:
                    my_print("The CPython2.7 tests are not present, not run.")

        if "--debug" not in flags:
            # Not running the Python 3.2 test suite with CPython2.6, as that's about
            # the same as CPython2.7 and won't have any new insights.
            if use_python not in ("python2.6", "python2.7") or not options.coverage:
                if options.cpython32:
                    if os.path.exists("./tests/CPython32/run_all.py"):
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "32tests", flags)
                        ):
                            executeSubTest("./tests/CPython32/run_all.py search")
                    else:
                        my_print("The CPython3.2 tests are not present, not run.")

            # Running the Python 3.3 test suite only with CPython3.x.
            if not use_python.startswith("python2"):
                if options.cpython33:
                    if os.path.exists("./tests/CPython33/run_all.py"):
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "33tests", flags)
                        ):
                            executeSubTest("./tests/CPython33/run_all.py search")
                    else:
                        my_print("The CPython3.3 tests are not present, not run.")

            # Running the Python 3.4 test suite only with CPython3.x.
            if not use_python.startswith("python2"):
                if options.cpython34:
                    if os.path.exists("./tests/CPython34/run_all.py"):
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "34tests", flags)
                        ):
                            executeSubTest("./tests/CPython34/run_all.py search")
                    else:
                        my_print("The CPython3.4 tests are not present, not run.")

            # Running the Python 3.5 test suite only with CPython3.x.
            if not use_python.startswith("python2"):
                if options.cpython35:
                    if os.path.exists("./tests/CPython35/run_all.py"):
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "35tests", flags)
                        ):
                            executeSubTest("./tests/CPython35/run_all.py search")
                    else:
                        my_print("The CPython3.5 tests are not present, not run.")

            # Running the Python 3.6 test suite only with CPython3.x.
            if not use_python.startswith("python2"):
                if options.cpython36:
                    if os.path.exists("./tests/CPython36/run_all.py"):
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "36tests", flags)
                        ):
                            executeSubTest("./tests/CPython36/run_all.py search")
                    else:
                        my_print("The CPython3.6 tests are not present, not run.")

            # Running the Python 3.7 test suite only with CPython3.x.
            if not use_python.startswith("python2"):
                if options.cpython37:
                    if os.path.exists("./tests/CPython37/run_all.py"):
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "37tests", flags)
                        ):
                            executeSubTest("./tests/CPython37/run_all.py search")
                    else:
                        my_print("The CPython3.7 tests are not present, not run.")

            # Running the Python 3.8 test suite only with CPython3.x.
            if not use_python.startswith("python2"):
                if options.cpython38:
                    if os.path.exists("./tests/CPython38/run_all.py"):
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "38tests", flags)
                        ):
                            executeSubTest("./tests/CPython38/run_all.py search")
                    else:
                        my_print("The CPython3.8 tests are not present, not run.")

            # Running the Python 3.9 test suite only with CPython3.x.
            if not use_python.startswith("python2"):
                if options.cpython39:
                    if os.path.exists("./tests/CPython39/run_all.py"):
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "39tests", flags)
                        ):
                            executeSubTest("./tests/CPython39/run_all.py search")
                    else:
                        my_print("The CPython3.9 tests are not present, not run.")

            # Running the Python 3.10 test suite only with CPython3.x.
            if not use_python.startswith("python2"):
                if options.cpython310:
                    if os.path.exists("./tests/CPython310/run_all.py"):
                        with withExtendedExtraOptions(
                            *getExtraFlags(where, "310tests", flags)
                        ):
                            executeSubTest("./tests/CPython310/run_all.py search")
                    else:
                        my_print("The CPython3.10 tests are not present, not run.")

    assert (
        checkExecutableCommand("python2.6")
        or checkExecutableCommand("python2.7")
        or checkExecutableCommand("python3.3")
        or checkExecutableCommand("python3.4")
        or checkExecutableCommand("python3.5")
        or checkExecutableCommand("python3.6")
        or checkExecutableCommand("python3.7")
        or checkExecutableCommand("python3.8")
        or checkExecutableCommand("python3.9")
        or checkExecutableCommand("python3.10")
    )

    if options.debug:
        if checkExecutableCommand("python2.6"):
            execute_tests("python2.6-debug", "python2.6", "--debug")
        else:
            my_print("Cannot execute tests with Python 2.6, disabled or not installed.")

        if checkExecutableCommand("python2.7"):
            execute_tests("python2.7-debug", "python2.7", "--debug")
        else:
            my_print("Cannot execute tests with Python 2.7, disabled or not installed.")

    if checkExecutableCommand("python2.6"):
        execute_tests("python2.6-nodebug", "python2.6", "")
    else:
        my_print("Cannot execute tests with Python 2.6, disabled or not installed.")

    if checkExecutableCommand("python2.7"):
        execute_tests("python2.7-nodebug", "python2.7", "")
    else:
        my_print("Cannot execute tests with Python 2.7, disabled or not installed.")

    if checkExecutableCommand("python3.3"):
        execute_tests("python3.3-nodebug", "python3.3", "")
    else:
        my_print("Cannot execute tests with Python 3.3, disabled or not installed.")

    if checkExecutableCommand("python3.4"):
        execute_tests("python3.4-nodebug", "python3.4", "")
    else:
        my_print("Cannot execute tests with Python 3.4, disabled or not installed.")

    if checkExecutableCommand("python3.5"):
        execute_tests("python3.5-nodebug", "python3.5", "")
    else:
        my_print("Cannot execute tests with Python 3.5, disabled or not installed.")

    if checkExecutableCommand("python3.6"):
        execute_tests("python3.6-nodebug", "python3.6", "")
    else:
        my_print("Cannot execute tests with Python 3.6, disabled or not installed.")

    if checkExecutableCommand("python3.7"):
        execute_tests("python3.7-nodebug", "python3.7", "")
    else:
        my_print("Cannot execute tests with Python 3.7, disabled or not installed.")

    if checkExecutableCommand("python3.8"):
        execute_tests("python3.8-nodebug", "python3.8", "")
    else:
        my_print("Cannot execute tests with Python 3.8, disabled or not installed.")

    if checkExecutableCommand("python3.9"):
        execute_tests("python3.9-nodebug", "python3.9", "")
    else:
        my_print("Cannot execute tests with Python 3.9, disabled or not installed.")

    if checkExecutableCommand("python3.10"):
        execute_tests("python3.10-nodebug", "python3.10", "")
    else:
        my_print("Cannot execute tests with Python 3.10, disabled or not installed.")

    if options.coverage:
        publishCoverageData()

    my_print("OK.")


if __name__ == "__main__":
    main()
