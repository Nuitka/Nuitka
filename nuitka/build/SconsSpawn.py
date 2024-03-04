#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Spawning processes.

This is to replace the standard spawn implementation with one that tracks the
progress, and gives warnings about things taking very long.
"""

import os
import sys
import threading

from nuitka.Tracing import my_print, scons_logger
from nuitka.utils.Execution import executeProcess
from nuitka.utils.FileOperations import getReportPath
from nuitka.utils.Timing import TimerReport

from .SconsCaching import runClCache
from .SconsProgress import (
    closeSconsProgressBar,
    reportSlowCompilation,
    updateSconsProgressBar,
)
from .SconsUtils import decodeData, reportSconsUnexpectedOutput


# Thread class to run a command
class SubprocessThread(threading.Thread):
    def __init__(self, cmdline, env):
        threading.Thread.__init__(self)

        self.cmdline = cmdline
        self.env = env

        self.data = None
        self.err = None
        self.exit_code = None
        self.exception = None

        self.timer_report = TimerReport(
            message="Running %s took %%.2f seconds"
            % repr(self.cmdline).replace("%", "%%"),
            min_report_time=360,
            logger=scons_logger,
        )

    def run(self):
        try:
            # execute the command, queue the result
            with self.timer_report:
                self.data, self.err, self.exit_code = executeProcess(
                    command=self.cmdline, env=self.env
                )

        except Exception as e:  # will rethrow all, pylint: disable=broad-except
            self.exception = e

    def getProcessResult(self):
        return self.data, self.err, self.exit_code, self.exception


def _runProcessMonitored(env, cmdline, os_env):
    thread = SubprocessThread(cmdline, os_env)
    thread.start()

    # Allow 6 minutes before warning for long compile time.
    thread.join(360)

    if thread.is_alive():
        reportSlowCompilation(env, cmdline, thread.timer_report.getTimer().getDelta())

    thread.join()

    updateSconsProgressBar()

    return thread.getProcessResult()


def _filterMsvcLinkOutput(env, module_mode, data, exit_code):
    # Training newline in some cases, esp. LTO it seems.
    data = data.rstrip()

    if module_mode:
        data = b"\r\n".join(
            line
            for line in data.split(b"\r\n")
            if b"   Creating library" not in line
            # On localized compilers, the message to ignore is not as clear.
            if not (module_mode and b".exp" in line)
        )

    # The linker will say generating code at the end, due to localization
    # we don't know.
    if env.lto_mode and exit_code == 0:
        if len(data.split(b"\r\n")) == 2:
            data = b""

    if env.pgo_mode == "use" and exit_code == 0:
        # Very noisy, partially in native language for PGO link.
        data = b""

    return data


def _raiseCorruptedObjectFilesExit(cache_name):
    """Error exit due to corrupt object files and point to cache cleanup."""
    scons_logger.sysexit(
        """\
Error, the C linker reported a corrupt object file. You may need to run
Nuitka with '--clean-cache=%s' once to repair it, or else will
surely happen again."""
        % cache_name
    )


def _getNoSuchCommandErrorMessage():
    import ctypes

    return ctypes.WinError(3).args[1]


# To work around Windows not supporting command lines of greater than 10K by
# default:
def _getWindowsSpawnFunction(env, module_mode, source_files):
    # Too much error handling error, pylint: disable=too-many-branches

    def spawnWindowsCommand(
        sh, escape, cmd, args, os_env
    ):  # pylint: disable=unused-argument
        """Our own spawn implementation for use on Windows."""

        # The "del" appears to not work reliably, but is used with large amounts of
        # files to link. So, lets do this ourselves, plus it avoids a process
        # spawn.
        if cmd == "del":
            assert len(args) == 2

            os.unlink(args[1])
            return 0

        # For quoted arguments that end in a backslash, things don't work well
        # this is a workaround for it.
        def removeTrailingSlashQuote(arg):
            if arg.endswith(r"\""):
                return arg[:-1] + '\\"'
            else:
                return arg

        new_args = " ".join(removeTrailingSlashQuote(arg) for arg in args[1:])
        cmdline = cmd + " " + new_args

        # Special hook for clcache inline copy
        if cmd == "<clcache>":
            data, err, rv = runClCache(args, os_env)
        else:
            data, err, rv, exception = _runProcessMonitored(env, cmdline, os_env)

            if exception:
                closeSconsProgressBar()
                raise exception

        if rv != 0:
            closeSconsProgressBar()

        if cmd == "link":
            data = _filterMsvcLinkOutput(
                env=env, module_mode=module_mode, data=data, exit_code=rv
            )
        elif cmd in ("cl", "<clcache>"):
            # Skip forced output from cl.exe
            data = data[data.find(b"\r\n") + 2 :]

            source_base_names = [
                os.path.basename(source_file) for source_file in source_files
            ]

            def check(line):
                return line in (b"", b"Generating Code...") or line in source_base_names

            data = (
                b"\r\n".join(line for line in data.split(b"\r\n") if not check(line))
                + b"\r\n"
            )

        if data is not None and data.rstrip():
            my_print("Unexpected output from this command:", style="scons-unexpected")
            my_print(cmdline, style="scons-unexpected")

            if str is not bytes:
                data = decodeData(data)

            my_print(
                data, style="scons-unexpected", end="" if data.endswith("\n") else "\n"
            )

            reportSconsUnexpectedOutput(env, cmdline, stdout=data, stderr=None)

        if err:
            if str is not bytes:
                err = decodeData(err)

            err = "\r\n".join(
                line
                for line in err.split("\r\n")
                if not isIgnoredError(line)
                if not (
                    env.mingw_mode
                    and env.lto_mode
                    and line == _getNoSuchCommandErrorMessage()
                )
            )

            if err:
                if "corrupt file" in err:
                    _raiseCorruptedObjectFilesExit(cache_name="clcache")
                if "Bad magic value" in err:
                    _raiseCorruptedObjectFilesExit(cache_name="ccache")

                err += "\r\n"
                my_print(err, style="scons-unexpected", end="")

                reportSconsUnexpectedOutput(env, cmdline, stdout=None, stderr=err)

        return rv

    return spawnWindowsCommand


def _formatForOutput(arg):
    # Undo the damage that scons did to pass it to "sh"
    arg = arg.strip('"')

    slash = "\\"
    special = '"$()'

    arg = arg.replace(slash + slash, slash)
    for c in special:
        arg = arg.replace(slash + c, c)

    if arg.startswith("-I"):
        prefix = "-I"
        arg = arg[2:]
    else:
        prefix = ""

    return prefix + getReportPath(arg)


def isIgnoredError(line):
    # Many cases and return driven, pylint: disable=too-many-branches,too-many-return-statements

    # spell-checker: ignore tmpnam,tempnam,structseq,bytearrayobject

    # Debian Python2 static libpython lto warnings:
    if "function `posix_tmpnam':" in line:
        return True
    if "function `posix_tempnam':" in line:
        return True

    # Self compiled Python2 static libpython lot warnings:
    if "the use of `tmpnam_r' is dangerous" in line:
        return True
    if "the use of `tempnam' is dangerous" in line:
        return True
    if line.startswith(("Objects/structseq.c:", "Python/import.c:")):
        return True
    if line == "In function 'load_next',":
        return True
    if "at Python/import.c" in line:
        return True

    # Debian Bullseye when compiling in directory with spaces:
    if "overriding recipe for target" in line:
        return True
    if "ignoring old recipe for target" in line:
        return True
    if "Error 1 (ignored)" in line:
        return True

    # Trusty has buggy toolchain that does this with LTO.
    if (
        line
        == """\
bytearrayobject.o (symbol from plugin): warning: memset used with constant zero \
length parameter; this could be due to transposed parameters"""
    ):
        return True

    # The gcc LTO with debug information is deeply buggy with many messages:
    if "Dwarf Error:" in line:
        return True

    # gcc from MinGW64 12.1 gives these, that seem non-consequential.
    if line.startswith("mingw32-make:") and line.endswith("Error 1 (ignored)"):
        return True

    return False


def subprocess_spawn(env, args):
    sh, _cmd, args, os_env = args

    _stdout, stderr, exit_code = executeProcess(
        command=[sh, "-c", " ".join(args)], env=os_env
    )

    if str is not bytes:
        stderr = decodeData(stderr)

    ignore_next = False
    for line in stderr.splitlines():
        if ignore_next:
            ignore_next = False
            continue

        # Corrupt object files, probably from ccache being interrupted at the wrong time.
        if "Bad magic value" in line:
            _raiseCorruptedObjectFilesExit(cache_name="ccache")

        if isIgnoredError(line):
            ignore_next = True
            continue

        if exit_code != 0 and "terminated with signal 11" in line:
            exit_code = -11

        my_print(line, style="scons-unexpected", file=sys.stderr)

        reportSconsUnexpectedOutput(env, args, stdout=None, stderr=line)

    return exit_code


class SpawnThread(threading.Thread):
    def __init__(self, env, *args):
        threading.Thread.__init__(self)

        self.env = env
        self.args = args

        self.timer_report = TimerReport(
            message="Running %s took %%.2f seconds"
            % (
                " ".join(_formatForOutput(arg) for arg in self.args[2]).replace(
                    "%", "%%"
                ),
            ),
            min_report_time=360,
            logger=scons_logger,
        )

        self.result = None
        self.exception = None

    def run(self):
        try:
            # execute the command, queue the result
            with self.timer_report:
                self.result = subprocess_spawn(env=self.env, args=self.args)
        except Exception as e:  # will rethrow all, pylint: disable=broad-except
            self.exception = e

    def getSpawnResult(self):
        return self.result, self.exception


def _runSpawnMonitored(env, sh, cmd, args, os_env):
    thread = SpawnThread(env, sh, cmd, args, os_env)
    thread.start()

    # Allow 6 minutes before warning for long compile time.
    thread.join(360)

    if thread.is_alive():
        reportSlowCompilation(env, cmd, thread.timer_report.getTimer().getDelta())

    thread.join()

    updateSconsProgressBar()

    return thread.getSpawnResult()


def _getWrappedSpawnFunction(env):
    def spawnCommand(sh, escape, cmd, args, os_env):
        # signature needed towards Scons core, pylint: disable=unused-argument

        # Avoid using ccache on binary constants blob, not useful and not working
        # with old ccache.
        if '"__constants_data.o"' in args or '"__constants_data.os"' in args:
            os_env = dict(os_env)
            os_env["CCACHE_DISABLE"] = "1"

        result, exception = _runSpawnMonitored(env, sh, cmd, args, os_env)

        if exception:
            closeSconsProgressBar()
            raise exception

        if result != 0:
            closeSconsProgressBar()

        # Segmentation fault should give a clear error.
        if result == -11:
            scons_logger.sysexit(
                """\
Error, the C compiler '%s' crashed with segfault. Consider upgrading \
it or using '--clang' option."""
                % env.the_compiler
            )

        return result

    return spawnCommand


def enableSpawnMonitoring(env, module_mode, source_files):
    if os.name == "nt":
        env["SPAWN"] = _getWindowsSpawnFunction(
            env=env, module_mode=module_mode, source_files=source_files
        )
    else:
        env["SPAWN"] = _getWrappedSpawnFunction(env=env)


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
