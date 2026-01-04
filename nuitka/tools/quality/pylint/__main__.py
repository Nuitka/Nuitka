#!/usr/bin/env python
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Main program for PyLint checker tool."""

import time

from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.PythonVersions import python_version
from nuitka.tools.Basics import addPYTHONPATH, getHomePath, setupPATH
from nuitka.tools.quality.Git import addGitArguments, getGitPaths
from nuitka.tools.quality.pylint.PyLint import executePyLint
from nuitka.tools.quality.ScanSources import isPythonFile, scanTargets
from nuitka.tools.testing.Common import hasModule, setup
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.FileOperations import (
    getFileModificationTime,
    resolveShellPatternToFilenames,
)


def isIgnoredFile(filename):
    if filename.startswith("Mini"):
        return True
    if filename.startswith("examples/"):
        return True
    if filename.startswith("tests/") and not filename.endswith("/run_all.py"):
        return True
    if "inline_copy" in filename:
        return True

    return False


def _resolveFilenames(options, positional_args):
    positional_args = getGitPaths(
        options=options,
        positional_args=positional_args,
        default_positional_args=(
            "bin",
            "nuitka",
            "setup.py",
            "tests/*/run_all.py",
        ),
    )

    if options.verbose:
        my_print("Working on: %s" % " ".join(positional_args))

    positional_args = sum(
        (
            resolveShellPatternToFilenames(positional_arg)
            for positional_arg in positional_args
        ),
        [],
    )

    ignore_list = []

    # Avoid checking the Python2 runner along with the one for Python3, it has name collisions.
    if python_version >= 0x300:
        ignore_list.append("nuitka")

    filenames = list(
        scanTargets(
            positional_args, suffixes=(".py", ".scons"), ignore_list=ignore_list
        )
    )

    # TODO: Filter this during scanTargets and during getGitPaths already
    filenames = [
        filename
        for filename in filenames
        if isPythonFile(filename)
        if not isIgnoredFile(filename)
    ]

    return filenames


def _parseArguments():
    parser = makeOptionsParser(usage=None, epilog=None)

    addGitArguments(parser)

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

    parser.add_option(
        "--watch",
        action="store_true",
        dest="watch",
        default=False,
        help="""\
Watch files for changes. Default is %default.""",
    )

    options, positional_args = parser.parse_args()

    return options, positional_args


def main():
    setup()

    # So PyLint finds nuitka package.
    addPYTHONPATH(getHomePath())
    setupPATH()

    options, positional_args = _parseArguments()

    if options.not_installed_is_no_error and not hasModule("pylint"):
        tools_logger.warning(
            "PyLint is not installed for this interpreter version: SKIPPED",
            style="yellow",
        )

        return tools_logger.sysexit(exit_code=0)

    # Scan files for changes periodically, for use in Visual Code task to
    # present errors.
    if options.watch:
        prev_filenames = set()
        prev_modification_times = {}

        while True:
            try:
                filenames = _resolveFilenames(
                    options=options, positional_args=positional_args
                )

                # Check for changes
                new_filenames = set(filenames)
                new_modification_times = {}

                for filename in filenames:
                    try:
                        new_modification_times[filename] = getFileModificationTime(
                            filename
                        )
                    except OSError:
                        new_modification_times[filename] = None

                changed = new_filenames != prev_filenames
                if not changed:
                    for filename, modification_time in new_modification_times.items():
                        if (
                            filename not in prev_modification_times
                            or prev_modification_times[filename] != modification_time
                        ):
                            changed = True
                            break

                if changed:
                    my_print(">>> Pylint Start")
                    try:
                        executePyLint(
                            filenames=filenames,
                            show_todo=options.todo,
                            verbose=options.verbose,
                            one_by_one=options.one_by_one,
                        )
                    except SystemExit:
                        pass

                    my_print(">>> Pylint End")

                    prev_filenames = new_filenames
                    prev_modification_times = new_modification_times

                time.sleep(0.5)

            except KeyboardInterrupt:
                break

        return tools_logger.sysexit(exit_code=0)

    filenames = _resolveFilenames(options=options, positional_args=positional_args)

    if not filenames:
        return tools_logger.sysexit("No matching files found.")

    exit_code = executePyLint(
        filenames=filenames,
        show_todo=options.todo,
        verbose=options.verbose,
        one_by_one=options.one_by_one,
    )

    return tools_logger.sysexit(exit_code=exit_code)


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
