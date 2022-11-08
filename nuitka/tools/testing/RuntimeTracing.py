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
import sys

from nuitka.__past__ import subprocess
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.freezer.DependsExe import getDependsExePath, parseDependsExeOutput
from nuitka.Options import isExperimental
from nuitka.utils.Execution import (
    callProcess,
    isExecutableCommand,
    withEnvironmentVarOverridden,
)
from nuitka.utils.FileOperations import (
    deleteFile,
    getFileContentByLine,
    putTextFileContents,
    withTemporaryFile,
)
from nuitka.utils.Utils import isFreeBSD, isMacOS, isWin32Windows


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


def _getRuntimeTraceOfLoadedFilesMacOSWithFsUsage(logger, command):
    # Very many details due to parsing fs_usage and micro managing
    # processes.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    path = command[0]

    if not isExecutableCommand("fs_usage"):
        logger.sysexit(
            """\
Error, needs 'fs_usage' on your system to scan used libraries."""
        )

    with withTemporaryFile() as run_binary_file:
        runner_filename = run_binary_file.name

        putTextFileContents(
            runner_filename,
            r"""
import os, sys
# Inform about our pid.
sys.stdout.write(str(os.getpid()) + "\n")
sys.stdout.flush()
# Wait for confirmation
sys.stdin.readline()
command = list(%s)
command.insert(0, command[0])
os.execl(*command)
"""
            % repr(command),
        )

        run_command = (sys.executable, runner_filename)
        logger.info(" ".join(run_command), style="pink")

        # Need to do it more manually, to catch pid
        process = subprocess.Popen(
            args=run_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        process_pid = int(process.stdout.readline())

    trace_command = ("sudo", "fs_usage", "-f", "filesys", "-w", str(process_pid))

    with withTemporaryFile() as trace_temp_file:
        trace_filename = trace_temp_file.name

        logger.info(" ".join(trace_command), style="pink")

        trace_process = subprocess.Popen(
            args=trace_command,
            stdout=trace_temp_file,
        )

        # Try to be more sure it started tracing before we launch.
        import time

        time.sleep(2)

        # Tell the process to continue now that tracing is active.
        process.stdin.write(b"go\n")
        logger.info(" ".join(command), style="pink")

        # Now the process can be normally executed.
        _stdout_process, stderr_process = process.communicate()
        process.wait()
        exit_process = process.returncode

        if exit_process != 0:
            if str is not bytes:
                stderr_process = stderr_process.decode("utf8")

            logger.warning(stderr_process)
            logger.sysexit("Failed to run '%s'." % path)

        # Allow fs_trace to do its thing.
        try:
            trace_process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            pass

        # Launched with sudo, we need to kill with sudo too.
        callProcess(("sudo", "kill", "-TERM", str(trace_process.pid)))
        trace_process.communicate()

        result = OrderedSet()

        process_dir = os.getcwd()

        for line in getFileContentByLine(trace_filename):
            parts = line.split()

            system_call_name = parts[1]

            if system_call_name == "open":
                filename = parts[4]
            elif system_call_name == "stat64":
                if "]" in line:
                    filename = line[line.find("]") :].split()[1]
                else:
                    filename = parts[2]
            elif system_call_name == "lstat64":
                if "]" in line:
                    filename = line[line.find("]") :].split()[1]
                else:
                    filename = parts[2]
            elif system_call_name == "readlink":
                filename = line[line.find("]") :].split()[1]
            elif system_call_name.startswith("chdir"):
                process_dir = parts[2]
            elif system_call_name.startswith("RdData"):
                continue
            elif system_call_name.startswith("RdMeta"):
                continue
            elif system_call_name in (
                "getattrlist",
                "getdirentries64",
                "fstatfs64",
                "ioctl",
                "fstat64",
                "access",
                "fsgetpath",
                "close",
                "lseek",
                "read",
                "write",
                "pread",
                "fcntl",
                "mmap",
                "exit",
            ):
                continue

            else:
                assert False, (system_call_name, line)

            assert not filename.startswith("["), line
            assert not filename.startswith("("), line

            assert "LC_TIME" not in filename, line

            # Strange ones, stat without filename or in "/".
            if filename.startswith("private/"):
                continue
            if filename.startswith("0.00"):
                continue

            filename = os.path.join(process_dir, filename)

            result.add(filename)

    return result


def _parseSystemCallTraceOutput(logger, command):
    tracing_tool = command[0] if command[0] != "sudo" else command[1]
    path = command[1] if command[0] != "sudo" else command[2]

    result = []

    # Ensure executable is not polluted with third party stuff,
    # tests may fail otherwise due to unexpected libs being loaded
    # spell-checker: ignore ENOENT
    with withEnvironmentVarOverridden("LD_PRELOAD", None):
        process = subprocess.Popen(
            args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        _stdout_strace, stderr_strace = process.communicate()
        exit_strace = process.returncode

        if exit_strace != 0:
            if str is not bytes:
                stderr_strace = stderr_strace.decode("utf8")

            logger.warning(stderr_strace)
            logger.sysexit("Failed to run '%s'." % tracing_tool)

        with open(path + "." + tracing_tool, "wb") as f:
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

    command = ("sudo", "dtruss", "-t", "open", os.path.abspath(command[0])) + tuple(
        command[1:]
    )

    return _parseSystemCallTraceOutput(logger, command)


def _getRuntimeTraceOfLoadedFilesStrace(logger, command):
    if not isExecutableCommand("strace"):
        logger.sysexit(
            """\
Error, needs 'strace' on your system to scan used libraries."""
        )

    command = (
        "strace",
        "-e",
        "file",
        "-s4096",  # Some paths are truncated in output otherwise
        os.path.abspath(command[0]),
    ) + tuple(command[1:])

    return _parseSystemCallTraceOutput(logger, command)


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
    elif isMacOS():
        if isExecutableCommand("dtruss") and not isExperimental("macos-use-fs_trace"):
            result = _getRuntimeTraceOfLoadedFilesDtruss(logger=logger, command=command)
        else:
            result = _getRuntimeTraceOfLoadedFilesMacOSWithFsUsage(
                logger=logger, command=command
            )

    elif isFreeBSD():
        # On FreeBSD, we can use dtruss, which is similar to strace.
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
