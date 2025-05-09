#!/usr/bin/env python
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Runner for onefile program tests of Nuitka.

These tests aim at showing that one specific functions work in onefile
mode, trying to find issues with that form of packaging.

"""


import os
import sys

# Find nuitka package relative to us. The replacement is for POSIX python
# and Windows paths on command line.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__.replace("\\", os.sep))), "..", ".."
        )
    ),
)

# isort:start

from nuitka.reports.CompilationReportReader import (
    getCompilationOutputBinary,
    parseCompilationReport,
)
from nuitka.tools.testing.Common import (
    checkLoadedFileAccesses,
    checkTestRequirements,
    compareWithCPython,
    createSearchMode,
    displayFileContents,
    displayRuntimeTraces,
    getTempDir,
    reportSkip,
    scanDirectoryForTestCases,
    setup,
    test_logger,
)
from nuitka.tools.testing.RuntimeTracing import (
    doesSupportTakingRuntimeTrace,
    getRuntimeTraceOfLoadedFiles,
)
from nuitka.utils.FileOperations import deleteFile
from nuitka.utils.Timing import TimerReport
from nuitka.utils.Utils import isMacOS


def displayError(dirname, filename):
    assert dirname is None

    inclusion_log_path = filename[:-3] + ".py.inclusion.log"
    displayFileContents("inclusion log", inclusion_log_path)


def main():
    python_version = setup(suite="onefile", needs_io_encoding=True)

    search_mode = createSearchMode()

    for filename in scanDirectoryForTestCases("."):
        active = search_mode.consider(dirname=None, filename=filename)

        if not active:
            continue

        report_filename = "test-compilation-report.xml"

        extra_flags = [
            "expect_success",
            "remove_output",
            # Keep the binary, normally "remove_output" includes that.
            "--keep-binary",
            # Cache the CPython results for reuse, they will normally not change.
            "cpython_cache",
            # To understand what is slow.
            "timing",
            # The onefile can warn about zstandard not being installed.
            "ignore_warnings",
            # To be able to find where the binary ended up being created.
            "--report=%s" % report_filename,
        ]

        if filename == "KeyboardInterruptTest.py":
            if isMacOS():
                reportSkip(
                    "Exit code from KeyboardInterrupt on macOS is not yet good.",
                    ".",
                    filename,
                )
                continue

            if python_version < (3,):
                reportSkip(
                    "Python2 reports KeyboardInterrupt, but too late",
                    ".",
                    filename,
                )
                continue

            if os.name == "nt":
                reportSkip(
                    "Testing cannot send KeyboardInterrupt on Windows yet",
                    ".",
                    filename,
                )
                continue

            extra_flags.append("--send-ctrl-c")

        if filename == "ExternalDataTest.py":
            extra_flags.append("--output-dir=%s" % getTempDir())

        # skip each test if their respective requirements are not met
        requirements_met, error_message = checkTestRequirements(filename)
        if not requirements_met:
            reportSkip(error_message, ".", filename)
            continue

        test_logger.info(
            "Consider output of onefile mode compiled program: %s" % filename
        )

        # First compare so we know the program behaves identical.
        compareWithCPython(
            dirname=None,
            filename=filename,
            extra_flags=extra_flags,
            search_mode=search_mode,
            on_error=displayError,
        )

        compilation_report = parseCompilationReport(report_filename)

        binary_filename = getCompilationOutputBinary(
            compilation_report=compilation_report,
            prefixes=(
                (
                    "~",
                    os.path.expanduser("~"),
                ),
                (
                    "${cwd}",
                    os.getcwd(),
                ),
            ),
        )

        try:
            if not doesSupportTakingRuntimeTrace():
                test_logger.info("Runtime traces are not possible on this machine.")
                continue
            # This test case requires a kill, so kill it there.
            if filename == "KeyboardInterruptTest.py":
                test_logger.info(
                    "Runtime traces are not taken for case that needs killing."
                )
                continue

            # Then use "strace" on the result.
            with TimerReport(
                "Determining run time loaded files took %.2f", logger=test_logger
            ):
                loaded_filenames = getRuntimeTraceOfLoadedFiles(
                    logger=test_logger, command=[binary_filename]
                )

            illegal_accesses = checkLoadedFileAccesses(
                loaded_filenames=loaded_filenames, current_dir=os.getcwd()
            )

            if illegal_accesses:
                displayError(None, filename)
                displayRuntimeTraces(test_logger, binary_filename)

                test_logger.warning(
                    "Should not access these file(s): '%s'."
                    % ",".join(illegal_accesses)
                )

                search_mode.onErrorDetected(1)

        finally:
            deleteFile(binary_filename, must_exist=True)

    search_mode.finish()


if __name__ == "__main__":
    main()

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
