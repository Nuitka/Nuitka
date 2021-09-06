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
""" Spawning processes.

This is to replace the standard spawn implementation with one that tracks the
progress, and gives warnings about things taking very long.
"""

import os
import subprocess
import sys
import threading

from nuitka.Tracing import my_print, scons_logger
from nuitka.utils.Timing import TimerReport

from .SconsCaching import runClCache
from .SconsProgress import closeSconsProgressBar, updateSconsProgressBar
from .SconsUtils import decodeData


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
            min_report_time=60,
            logger=scons_logger,
        )

    def run(self):
        try:
            # execute the command, queue the result
            with self.timer_report:
                proc = subprocess.Popen(
                    self.cmdline,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    env=self.env,
                )

                self.data, self.err = proc.communicate()
                self.exit_code = proc.wait()
        except Exception as e:  # will rethrow all, pylint: disable=broad-except
            self.exception = e

    def getProcessResult(self):
        return self.data, self.err, self.exit_code, self.exception


def runProcessMonitored(cmdline, env):
    thread = SubprocessThread(cmdline, env)
    thread.start()

    # Allow a minute before warning for long compile time.
    thread.join(60)

    if thread.is_alive():
        scons_logger.info(
            "Slow C compilation detected, used %.0fs so far, this might indicate scalability problems."
            % thread.timer_report.getTimer().getDelta()
        )

    thread.join()

    updateSconsProgressBar()

    return thread.getProcessResult()


def _filterLinkOutput(module_mode, lto_mode, data, exit_code):
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
    if lto_mode and exit_code == 0:
        if len(data.split(b"\r\n")) == 2:
            data = b""

    return data


# To work around Windows not supporting command lines of greater than 10K by
# default:
def getWindowsSpawnFunction(module_mode, lto_mode, source_files):
    def spawnWindowsCommand(
        sh, escape, cmd, args, env
    ):  # pylint: disable=unused-argument

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

        newargs = " ".join(removeTrailingSlashQuote(arg) for arg in args[1:])
        cmdline = cmd + " " + newargs

        # Special hook for clcache inline copy
        if cmd == "<clcache>":
            data, err, rv = runClCache(args, env)
        else:
            data, err, rv, exception = runProcessMonitored(cmdline, env)

            if exception:
                closeSconsProgressBar()
                raise exception

        if cmd == "link":
            data = _filterLinkOutput(
                module_mode=module_mode, lto_mode=lto_mode, data=data, exit_code=rv
            )

        elif cmd in ("cl", "<clcache>"):
            # Skip forced output from cl.exe
            data = data[data.find(b"\r\n") + 2 :]

            source_basenames = [
                os.path.basename(source_file) for source_file in source_files
            ]

            def check(line):
                return line in (b"", b"Generating Code...") or line in source_basenames

            data = (
                b"\r\n".join(line for line in data.split(b"\r\n") if not check(line))
                + b"\r\n"
            )

        if data is not None and data.rstrip():
            my_print("Unexpected output from this command:", style="yellow")
            my_print(cmdline, style="yellow")

            if str is not bytes:
                data = decodeData(data)

            my_print(data, style="yellow", end="")

        if err:
            if str is not bytes:
                err = decodeData(err)

            my_print(err, style="yellow", end="")

        return rv

    return spawnWindowsCommand


def _unescape(arg):
    # Undo the damage that scons did to pass it to "sh"
    arg = arg.strip('"')

    slash = "\\"
    special = '"$()'

    arg = arg.replace(slash + slash, slash)
    for c in special:
        arg = arg.replace(slash + c, c)

    return arg


def isIgnoredError(line):
    # Many cases, pylint: disable=too-many-return-statements

    # Debian Python2 static libpython lto warnings:
    if b"function `posix_tmpnam':" in line:
        return True
    if b"function `posix_tempnam':" in line:
        return True

    # Self compiled Python2 static libpython lot warnings:
    if b"the use of `tmpnam_r' is dangerous" in line:
        return True
    if b"the use of `tempnam' is dangerous" in line:
        return True
    if line.startswith((b"Objects/structseq.c:", b"Python/import.c:")):
        return True
    if line == b"In function 'load_next',":
        return True
    if b"at Python/import.c" in line:
        return True

    # Bullseys when compiling in directory with spaces:
    if b"overriding recipe for target" in line:
        return True
    if b"ignoring old recipe for target" in line:
        return True
    if b"Error 1 (ignored)" in line:
        return True

    return False


def subprocess_spawn(args):
    sh, _cmd, args, env = args

    proc = subprocess.Popen(
        [sh, "-c", " ".join(args)], env=env, close_fds=True, stderr=subprocess.PIPE
    )

    _stdout, stderr = proc.communicate()

    stderr_lines = stderr.splitlines()

    ignore_next = False
    for line in stderr_lines:
        if ignore_next:
            ignore_next = False
            continue

        if isIgnoredError(line):
            ignore_next = True
            continue

        if str is not bytes:
            line = decodeData(line)

        my_print(line, style="yellow", file=sys.stderr)

    return proc.wait()


class SpawnThread(threading.Thread):
    def __init__(self, *args):
        threading.Thread.__init__(self)

        self.args = args

        self.timer_report = TimerReport(
            message="Running %s took %%.2f seconds"
            % (" ".join(_unescape(arg) for arg in self.args[2]).replace("%", "%%"),),
            min_report_time=60,
            logger=scons_logger,
        )

        self.result = None
        self.exception = None

    def run(self):
        try:
            # execute the command, queue the result
            with self.timer_report:
                self.result = subprocess_spawn(self.args)
        except Exception as e:  # will rethrow all, pylint: disable=broad-except
            self.exception = e

    def getSpawnResult(self):
        return self.result, self.exception


def runSpawnMonitored(sh, cmd, args, env):
    thread = SpawnThread(sh, cmd, args, env)
    thread.start()

    # Allow a minute before warning for long compile time.
    thread.join(60)

    if thread.is_alive():
        scons_logger.info(
            "Slow C compilation detected, used %.0fs so far, this might indicate scalability problems."
            % thread.timer_report.getTimer().getDelta()
        )

    thread.join()

    updateSconsProgressBar()

    return thread.getSpawnResult()


def getWrappedSpawnFunction():
    def spawnCommand(sh, escape, cmd, args, env):
        # signature needed towards Scons core, pylint: disable=unused-argument

        # Avoid using ccache on binary constants blob, not useful and not working
        # with old ccache.
        if '"__constants_data.o"' in args or '"__constants_data.os"' in args:
            env = dict(env)
            env["CCACHE_DISABLE"] = "1"

        result, exception = runSpawnMonitored(sh, cmd, args, env)

        if exception:
            closeSconsProgressBar()

            raise exception

        return result

    return spawnCommand


def enableSpawnMonitoring(env, win_target, module_mode, lto_mode, source_files):
    if win_target:
        env["SPAWN"] = getWindowsSpawnFunction(
            module_mode=module_mode, lto_mode=lto_mode, source_files=source_files
        )
    else:
        env["SPAWN"] = getWrappedSpawnFunction()
