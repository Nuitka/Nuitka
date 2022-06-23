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
""" Runtime tracing

At this time we detect DLLs used by a program with this code, such
that we can check if it loads things outside of the program, but we
can also use this to determine what to include, so some plugins will
be using this.

"""

import os
import re

from nuitka.__past__ import subprocess
from nuitka.utils.Execution import (
    callProcess,
    isExecutableCommand,
    withEnvironmentVarOverridden,
)
from nuitka.utils.Utils import getOS

from .DependsExe import getDependsExePath, parseDependsExeOutput


def getRuntimeTraceOfLoadedFiles(logger, command, required=False):
    """Returns the files loaded when executing a binary."""

    # This will make a crazy amount of work,
    # pylint: disable=I0021,too-many-branches,too-many-locals,too-many-statements

    path = command[0]

    if not os.path.exists(path):
        logger.sysexit("Error, cannot find %r (%r)." % (path, os.path.abspath(path)))

    result = []

    if os.name == "posix":
        if getOS() in ("Darwin", "FreeBSD"):
            if not isExecutableCommand("dtruss"):
                logger.sysexit(
                    """\
Error, needs 'dtruss' on your system to scan used libraries."""
                )

            if not isExecutableCommand("sudo"):
                logger.sysexit(
                    """\
Error, needs 'sudo' on your system to scan used libraries."""
                )

            args = ("sudo", "dtruss", "-t", "open", os.path.abspath(path))
        else:
            if not isExecutableCommand("strace"):
                logger.sysexit(
                    """\
Error, needs 'strace' on your system to scan used libraries."""
                )

            args = (
                "strace",
                "-e",
                "file",
                "-s4096",  # Some paths are truncated in output otherwise
                os.path.abspath(path),
            )

        # Ensure executable is not polluted with third party stuff,
        # tests may fail otherwise due to unexpected libs being loaded
        with withEnvironmentVarOverridden("LD_PRELOAD", None):
            tracing_command = args[0] if args[0] != "sudo" else args[1]

            process = subprocess.Popen(
                args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            _stdout_strace, stderr_strace = process.communicate()
            exit_strace = process.returncode

            if exit_strace != 0:
                if str is not bytes:
                    stderr_strace = stderr_strace.decode("utf8")

                logger.warning(stderr_strace)
                logger.sysexit("Failed to run %r." % tracing_command)

            with open(path + ".strace", "wb") as f:
                f.write(stderr_strace)

            for line in stderr_strace.split(b"\n"):
                if process.returncode != 0:
                    logger.my_print(line)

                if not line:
                    continue

                # Don't consider files not found. The "site" module checks lots
                # of things.
                if b"ENOENT" in line:
                    continue

                if line.startswith(b"stat(") and b"S_IFDIR" in line:
                    continue

                result.extend(
                    os.path.abspath(match)
                    for match in re.findall(b'"(.*?)(?:\\\\0)?"', line)
                )

            if str is not bytes:
                result = [s.decode("utf8") for s in result]
    elif os.name == "nt":
        command = (
            getDependsExePath(),
            "-c",  # Console mode
            "-ot%s" % path + ".depends",
            "-f1",
            "-pb",
            "-pa1",  # Turn on all profiling options.
            "-ps1",  # Simulate ShellExecute with app dirs in PATH.
            "-pp1",  # Do not long DllMain calls.
            "-po1",  # Log DllMain call for all other messages.
            "-ph1",  # Hook the process.
            "-pl1",  # Log LoadLibrary calls.
            "-pt1",  # Thread information.
            "-pe1",  # First chance exceptions.
            "-pg1",  # Log GetProcAddress calls.
            "-pf1",  # Use full paths.
            "-pc1",  # Profile child processes.
        ) + tuple(command)

        # TODO: Move the handling of this into nuitka.tools.Execution module methods.
        try:
            callProcess(command, timeout=5 * 60)
        except Exception as e:  # Catch all the things, pylint: disable=broad-except
            if e.__class__.__name__ == "TimeoutExpired":
                if required:
                    logger.sysexit(
                        "Timeout encountered when running dependency walker."
                    )

                logger.warning("Timeout encountered when running dependency walker.")
                return []
            else:
                raise

        result = parseDependsExeOutput(path + ".depends")

        os.unlink(path + ".depends")

    result = list(sorted(set(result)))

    return result


if __name__ == "__main__":
    import sys

    from nuitka.Tracing import general
    from nuitka.utils.FileOperations import withTemporaryFile

    source_code = """
import sys
from PySide2.QtQuick import QQuickView
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QUrl
QApplication(sys.argv)
viewer = QQuickView()
viewer.setSource(QUrl.fromLocalFile(sys.argv[1]))
"""

    qml_code = """
import QtQuick 2.0
"""

    with withTemporaryFile(suffix=".qml", delete=False) as qml_file:
        qml_file.write(qml_code)
        qml_filename = qml_file.name

        with withTemporaryFile(suffix=".py", delete=False) as temp_file:
            temp_file.write(source_code)
            temp_filename = temp_file.name

    getRuntimeTraceOfLoadedFiles(
        logger=general, command=[sys.executable, temp_filename, qml_filename]
    )
