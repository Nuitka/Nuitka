#!/usr/bin/env python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Main program for PyLint checker tool.

spell-checker: ignore unpushed
"""

from optparse import OptionParser

from nuitka.PythonVersions import python_version
from nuitka.tools.Basics import addPYTHONPATH, getHomePath, goHome, setupPATH
from nuitka.tools.quality.Git import getModifiedPaths, getUnpushedPaths
from nuitka.tools.quality.pylint import PyLint
from nuitka.tools.quality.ScanSources import isPythonFile, scanTargets
from nuitka.tools.testing.Common import hasModule, setup
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.FileOperations import resolveShellPatternToFilenames


def isIgnoredFile(filename):
    if filename.startswith("Mini"):
        return True
    if filename.startswith("examples/"):
        return True
    if filename.startswith("tests/") and not filename.endswith("/run_all.py"):
        return True

    return False


def main():
    setup(go_main=False)

    # So PyLint finds nuitka package.
    addPYTHONPATH(getHomePath())
    setupPATH()

    parser = OptionParser()

    parser.add_option(
        "--diff",
        action="store_true",
        dest="diff",
        default=False,
        help="""\
Analyse the changed files in git. Default is %default.""",
    )

    parser.add_option(
        "--unpushed",
        action="store_true",
        dest="unpushed",
        default=False,
        help="""\
Analyse the changed files in git. Default is %default.""",
    )

    parser.add_option(
        "--show-todo",
        "--todo",
        action="store_true",
        dest="todo",
        default=False,
        help="""\
Show TODO items. Default is %default.""",
    )

    parser.add_option(
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="""\
Be verbose in output. Default is %default.""",
    )

    parser.add_option(
        "--one-by-one",
        action="store_true",
        dest="one_by_one",
        default=False,
        help="""\
Check files one by one. Default is %default.""",
    )

    parser.add_option(
        "--not-installed-is-no-error",
        action="store_true",
        dest="not_installed_is_no_error",
        default=False,
        help="""\
Insist on PyLint to be installed. Default is %default.""",
    )

    options, positional_args = parser.parse_args()

    if options.not_installed_is_no_error and not hasModule("pylint"):
        tools_logger.warning(
            "PyLint is not installed for this interpreter version: SKIPPED",
            style="yellow",
        )
        tools_logger.sysexit(exit_code=0)

    if positional_args:
        if options.diff or options.unpushed:
            tools_logger.sysexit(
                "Error, no filenames argument allowed in git diff mode."
            )

    else:
        goHome()

        if options.diff:
            positional_args = [
                filename
                for filename in getModifiedPaths()
                if isPythonFile(filename)
                if not isIgnoredFile(filename)
            ]
        else:
            positional_args = [
                filename
                for filename in getUnpushedPaths()
                if isPythonFile(filename)
                if not isIgnoredFile(filename)
            ]

        if not positional_args:
            positional_args = ["bin", "nuitka", "setup.py", "tests/*/run_all.py"]

    positional_args = sum(
        (
            resolveShellPatternToFilenames(positional_arg)
            for positional_arg in positional_args
        ),
        [],
    )

    if not positional_args:
        tools_logger.sysexit("No files found.")

    my_print("Working on: %s" % " ".join(positional_args))

    ignore_list = []

    # Avoid checking the Python2 runner along with the one for Python3, it has name collisions.
    if python_version >= 0x300:
        ignore_list.append("nuitka")

    filenames = list(
        scanTargets(
            positional_args, suffixes=(".py", ".scons"), ignore_list=ignore_list
        )
    )
    PyLint.executePyLint(
        filenames=filenames,
        show_todo=options.todo,
        verbose=options.verbose,
        one_by_one=options.one_by_one,
    )

    if not filenames:
        tools_logger.sysexit("No matching files found.")

    tools_logger.sysexit(exit_code=PyLint.our_exit_code)
