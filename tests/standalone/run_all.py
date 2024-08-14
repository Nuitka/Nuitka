#!/usr/bin/env python
#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Runner for standalone program tests of Nuitka.

These tests aim at showing that one specific module works in standalone
mode, trying to find issues with that packaging.

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
    displayFolderContents,
    displayRuntimeTraces,
    reportSkip,
    scanDirectoryForTestCases,
    setup,
    test_logger,
)
from nuitka.tools.testing.RuntimeTracing import (
    doesSupportTakingRuntimeTrace,
    getRuntimeTraceOfLoadedFiles,
)
from nuitka.utils.FileOperations import removeDirectory
from nuitka.utils.Timing import TimerReport
from nuitka.utils.Utils import isBSD, isLinux, isMacOS, isWin32Windows


def displayError(dirname, filename):
    assert dirname is None

    dist_path = filename[:-3] + ".dist"
    displayFolderContents("dist folder", dist_path)

    inclusion_log_path = filename[:-3] + ".py.inclusion.log"
    displayFileContents("inclusion log", inclusion_log_path)


def _checkForLibcBinaries(dist_path):
    found_glibc_libs = []
    for dist_filename in os.listdir(os.path.join(dist_path)):
        if os.path.basename(dist_filename).startswith(
            (
                "ld-linux-x86-64.so",
                "libc.so.",
                "libpthread.so.",
                "libm.so.",
                "libdl.so.",
                "libBrokenLocale.so.",
                "libSegFault.so",
                "libanl.so.",
                "libcidn.so.",
                "libcrypt.so.",
                "libmemusage.so",
                "libmvec.so.",
                "libnsl.so.",
                "libnss_compat.so.",
                "libnss_db.so.",
                "libnss_dns.so.",
                "libnss_files.so.",
                "libnss_hesiod.so.",
                "libnss_nis.so.",
                "libnss_nisplus.so.",
                "libpcprofile.so",
                "libresolv.so.",
                "librt.so.",
                "libthread_db-1.0.so",
                "libthread_db.so.",
                "libutil.so.",
            )
        ):
            found_glibc_libs.append(dist_filename)

    if found_glibc_libs:
        test_logger.sysexit(
            "Should not ship glibc libraries with the standalone executable (found %s)"
            % found_glibc_libs
        )


def main():
    # Complex stuff, even more should become common code or project options though.
    # pylint: disable=too-many-branches,too-many-statements

    python_version = setup(suite="standalone", needs_io_encoding=True)

    search_mode = createSearchMode()

    for filename in scanDirectoryForTestCases("."):
        active = search_mode.consider(dirname=None, filename=filename)

        if not active:
            continue

        # skip each test if their respective requirements are not met
        requirements_met, error_message = checkTestRequirements(filename)
        if not requirements_met:
            reportSkip(error_message, ".", filename)
            continue

        report_filename = "test-compilation-report.xml"

        extra_flags = [
            "expect_success",
            "--standalone",
            "remove_output",
            # Cache the CPython results for reuse, they will normally not change.
            "cpython_cache",
            # To understand what is slow.
            "timing",
            # Don't care here, this is mostly for coverage.
            "--nowarn-mnemonic=debian-dist-packages",
            "--report=%s" % report_filename,
        ]

        if filename == "Urllib3Using.py" and os.name == "nt":
            reportSkip(
                "Socket module early import not working on Windows currently",
                ".",
                filename,
            )
            continue

        if "Idna" in filename:
            # For the warnings of Python2.
            if python_version < (3,):
                extra_flags.append("ignore_stderr")

        if filename == "GtkUsing.py":
            # Don't test on platforms not supported by current Debian testing, and
            # which should be considered irrelevant by now.
            if python_version < (2, 7):
                reportSkip("irrelevant Python version", ".", filename)
                continue

            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename.startswith("Win"):
            if os.name != "nt":
                reportSkip("Windows only test", ".", filename)
                continue

        if filename == "TkInterUsing.py":
            if isMacOS():
                reportSkip("Not working macOS yet", ".", filename)
                continue

            if isWin32Windows() == "Windows":
                reportSkip("Can hang on Windows CI.", ".", filename)
                continue

            # For the plug-in information.
            extra_flags.append("plugin_enable:tk-inter")

        if filename == "FlaskUsing.py":
            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename == "MetadataPackagesUsing.py":
            # TODO: Disabled for now.
            reportSkip(
                "MetadataPackagesUsing is environment dependent somehow, not fully working yet",
                ".",
                filename,
            )
            continue

        if filename == "PmwUsing.py":
            extra_flags.append("plugin_enable:pmw-freezer")

        if filename == "OpenGLUsing.py":
            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename == "PasslibUsing.py":
            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename == "Win32ComUsing.py":
            # For the warnings.
            extra_flags.append("ignore_warnings")

        if filename.startswith(("PySide2", "PySide6", "PyQt5", "PyQt6")):
            # Don't test on platforms not supported by current Debian testing, and
            # which should be considered irrelevant by now.
            if python_version < (2, 7) or ((3,) <= python_version < (3, 7)):
                reportSkip("irrelevant Python version", ".", filename)
                continue

            if filename != "PySide6":
                extra_flags.append("ignore_warnings")

        if filename.startswith("PyQt6") and isMacOS():
            reportSkip("not currently supported", ".", filename)
            continue

        test_logger.info(
            "Consider output of standalone mode compiled program: %s" % filename
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
            prefixes=(("${cwd}", os.getcwd()),),
        )
        output_dist_path = os.path.dirname(binary_filename)

        # Second check if libc libraries haven't been accidentally
        # shipped with the standalone executable
        if isLinux() or isBSD():
            _checkForLibcBinaries(output_dist_path)

        try:
            if not doesSupportTakingRuntimeTrace():
                test_logger.info("Runtime traces are not possible on this machine.")
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
                    "Should not access these file(s): '%r'." % illegal_accesses
                )

                search_mode.onErrorDetected(1)
        finally:
            removeDirectory(
                filename[:-3] + ".dist",
                logger=test_logger,
                ignore_errors=True,
                extra_recommendation=None,
            )

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
