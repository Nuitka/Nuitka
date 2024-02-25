#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Runtime tracing

At this time we detect DLLs used by a program with this code, such
that we can check if it loads things outside of the program, but we
can also use this to determine what to include, so some plugins will
be using this.

"""

import os
import re
import sys

from nuitka.freezer.DependsExe import getDependsExePath, parseDependsExeOutput
from nuitka.utils.Execution import (
    callProcess,
    executeProcess,
    isExecutableCommand,
    withEnvironmentVarOverridden,
)
from nuitka.utils.FileOperations import deleteFile
from nuitka.utils.Utils import isFreeBSD, isMacOS, isWin32Windows

from .Common import traceExecutedCommand


def _getRuntimeTraceOfLoadedFilesWin32(logger, command, required):
    path = command[0]

    output_filename = path + ".depends"

    command = (
        getDependsExePath(),
        "-c",  # Console mode
        "-ot%s" % output_filename,
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
                logger.sysexit("Timeout encountered when running dependency walker.")

            logger.warning("Timeout encountered when running dependency walker.")
            return []
        else:
            raise

    result = parseDependsExeOutput(output_filename)

    deleteFile(output_filename, must_exist=False)

    return result


def _takeSystemCallTraceOutput(logger, path, command):
    tracing_tool = command[0] if command[0] != "sudo" else command[1]

    result = []

    # Ensure executable is not polluted with third party stuff,
    # tests may fail otherwise due to unexpected libs being loaded
    # spell-checker: ignore ENOENT,write_nocancel
    with withEnvironmentVarOverridden("LD_PRELOAD", None):
        if os.getenv("NUITKA_TRACE_COMMANDS", "0") != "0":
            traceExecutedCommand("Tracing with:", command)

        _stdout_strace, stderr_strace, exit_strace = executeProcess(
            command, stdin=False, timeout=5 * 60
        )

        if exit_strace != 0:
            if str is not bytes:
                stderr_strace = stderr_strace.decode("utf8")

            logger.warning(stderr_strace)
            logger.sysexit("Failed to run '%s'." % tracing_tool)

        if b"dtrace: system integrity protection is on" in stderr_strace:
            logger.sysexit("System integrity protection prevents system call tracing.")

        with open(path + "." + tracing_tool, "wb") as f:
            f.write(stderr_strace)

        for line in stderr_strace.split(b"\n"):
            if exit_strace != 0:
                logger.my_print(line)

            if not line:
                continue

            # Don't consider files not found. The "site" module checks lots
            # of things.
            if b"ENOENT" in line:
                continue

            if line.startswith((b"write(", b"write_nocancel(", b"read(")):
                continue

            if line.startswith((b"stat(", b"newfstatat(")) and b"S_IFDIR" in line:
                continue

            # Don't consider files not found.
            if line.startswith(b"stat64(") and b"= -1" in line:
                continue

            result.extend(
                os.path.abspath(match)
                for match in re.findall(b'"(.*?)(?:\\\\0)?"', line)
            )

        if str is not bytes:
            result = [s.decode("utf8") for s in result]

    return result


def _getRuntimeTraceOfLoadedFilesDtruss(logger, command):
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

    binary_path = os.path.abspath(command[0])
    command = ("sudo", "dtruss", binary_path) + tuple(command[1:])

    return _takeSystemCallTraceOutput(logger=logger, command=command, path=binary_path)


def _getRuntimeTraceOfLoadedFilesStrace(logger, command):
    if not isExecutableCommand("strace"):
        logger.sysexit(
            """\
Error, needs 'strace' on your system to scan used libraries."""
        )

    binary_path = os.path.abspath(command[0])

    command = (
        "strace",
        "-e",
        "file",
        "-s4096",  # Some paths are truncated in output otherwise
        binary_path,
    ) + tuple(command[1:])

    return _takeSystemCallTraceOutput(logger=logger, command=command, path=binary_path)


_supports_taking_runtime_traces = None


def doesSupportTakingRuntimeTrace():
    if not isMacOS():
        return True

    # Python2 hangs calling dtruss for no good reason, probably a bug in
    # subprocess32 with Python2 that we do not care about.
    if str is bytes:
        return False

    # singleton, pylint: disable=global-statement
    global _supports_taking_runtime_traces

    if _supports_taking_runtime_traces is None:
        command = ("sudo", "dtruss", "echo")

        _stdout, stderr, exit_code = executeProcess(
            command, stdin=False, timeout=5 * 60
        )

        _supports_taking_runtime_traces = (
            exit_code == 0
            and b"dtrace: system integrity protection is on" not in stderr
        )

    return _supports_taking_runtime_traces


def getRuntimeTraceOfLoadedFiles(logger, command, required=False):
    """Returns the files loaded when executing a binary."""

    # This will make a crazy amount of work,
    # pylint: disable=I0021,too-many-branches,too-many-locals,too-many-statements

    path = command[0]

    if not os.path.exists(path):
        logger.sysexit(
            "Error, cannot find '%s' ('%s')." % (path, os.path.abspath(path))
        )

    result = []

    if isWin32Windows():
        result = _getRuntimeTraceOfLoadedFilesWin32(
            logger=logger, command=command, required=required
        )
    elif isMacOS() or isFreeBSD():
        # On macOS and FreeBSD, we can use dtruss, which is similar to strace.
        result = _getRuntimeTraceOfLoadedFilesDtruss(logger=logger, command=command)
    elif os.name == "posix":
        result = _getRuntimeTraceOfLoadedFilesStrace(logger=logger, command=command)

    result = tuple(sorted(set(result)))

    return result


def main():
    from nuitka.Tracing import tools_logger

    for filename in getRuntimeTraceOfLoadedFiles(
        logger=tools_logger, command=sys.argv[1:]
    ):
        print(filename)


if __name__ == "__main__":
    main()

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
