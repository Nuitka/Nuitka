#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
import re
import subprocess
import threading

from nuitka.Tracing import my_print, scons_logger
from nuitka.utils.Timing import TimerReport

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

        self.timer_report = TimerReport(
            message="Running %s took %%.2f seconds" % repr(self.cmdline).replace('%', '%%'),
            min_report_time=60,
            logger=scons_logger,
        )

    def run(self):
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

    def getProcessResult(self):
        return self.data, self.err, self.exit_code


def runProcessMonitored(cmdline, env):
    thread = SubprocessThread(cmdline, env)
    thread.start()

    # Allow a minute before warning for long compile time.
    thread.join(60)

    if thread.isAlive():
        scons_logger.info(
            "Slow C compilation detected, used %.0fs so far, this might indicate scalability problems."
            % thread.timer_report.getTimer().getDelta()
        )

    thread.join()

    return thread.getProcessResult()


# To work around Windows not supporting command lines of greater than 10K by
# default:
def getWindowsSpawnFunction(module_mode, source_files):
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

        # Remove useless quoted include directories to "windres", which does not
        # handle them properly in its command line parsing, while they are not
        # used at all.
        if cmd == "windres":
            cmdline = re.sub('--include-dir ".*?"', "", cmdline)

        data, err, rv = runProcessMonitored(cmdline, env)

        if cmd == "rc":
            data = data[data.find(b"reserved.\r") + 13 :]

            data = b"\n".join(
                line
                for line in data.split(b"\n")
                if b"identifier truncated to" not in line
            )
        elif cmd == "link" and module_mode:
            data = b"\r\n".join(
                line
                for line in data.split(b"\r\n")
                if b"   Creating library" not in line
                # On localized compilers, the message to ignore is not as clear.
                if not (module_mode and b".exp" in line)
            )
        elif cmd == "cl" or os.path.basename(cmd).lower() == "clcache.exe":
            data = data[data.find(b"\r\n") + 2 :]

            source_basenames = [
                os.path.basename(source_file) for source_file in source_files
            ]

            def check(line):
                return line in (b"", b"Generating Code...") or line in source_basenames

            data = b"\r\n".join(line for line in data.split(b"\r\n") if not check(line))

        if data.rstrip():
            if not decodeData:
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


class SpawnThread(threading.Thread):
    def __init__(self, spawn, *args):
        threading.Thread.__init__(self)

        self.spawn = spawn
        self.args = args

        self.timer_report = TimerReport(
            message="Running %s took %%.2f seconds" % (repr(self.args).replace('%', '%%'),),
            min_report_time=60,
            logger=scons_logger,
        )

        self.result = None

    def run(self):
        # execute the command, queue the result
        with self.timer_report:
            self.result = self.spawn(*self.args)

    def getSpawnResult(self):
        return self.result


def runSpawnMonitored(spawn, sh, escape, cmd, args, env):
    thread = SpawnThread(spawn, sh, escape, cmd, args, env)
    thread.start()

    # Allow a minute before warning for long compile time.
    thread.join(60)

    if thread.isAlive():
        scons_logger.info(
            "Slow C compilation detected, used %.0fs so far, this might indicate scalability problems."
            % thread.timer_report.getTimer().getDelta()
        )

    thread.join()

    return thread.getSpawnResult()


def getWrappedSpawnFunction(spawn):
    def spawnCommand(sh, escape, cmd, args, env):
        return runSpawnMonitored(spawn, sh, escape, cmd, args, env)

    return spawnCommand
