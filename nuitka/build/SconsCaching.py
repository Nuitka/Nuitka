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
""" Caching of C compiler output.

"""

import os
import re
import sys
from collections import defaultdict

from nuitka.Tracing import scons_logger
from nuitka.utils.Utils import getOS, isWin32Windows

from .SconsUtils import (
    getExecutablePath,
    getSconsReportValue,
    setEnvironmentVariable,
)


def _getCcacheGuessedPaths(python_prefix):

    # Hardcoded default for Windows, use it from MSYS64, as the only thing from there.
    if isWin32Windows():
        # Geared at Anaconda mostly.
        for python_dir in python_prefix, sys.prefix:
            yield os.path.join(python_dir, "bin", "ccache.exe")

        # Maybe an Anaconda is present via activated environment.
        if "CONDA_PREFIX" in os.environ:
            yield os.path.join(os.environ["CONDA_PREFIX"], "bin", "ccache.exe")

        # Maybe an Anaconda is present via environment variable, tthroas it's the case
        # on Github actions.
        if "CONDA" in os.environ:
            yield os.path.join(os.environ["CONDA"], "bin", "ccache.exe")

        # Maybe MSYS2 happens to be installed at the default location.
        yield r"C:\msys64\usr\bin\ccache.exe"

    # For macOS, we might find Homebrew ccache installed but not in PATH.
    if getOS() == "Darwin":
        yield "/usr/local/opt/ccache"


def enableCcache(env, source_dir, python_prefix, show_scons_mode):
    # The ccache needs absolute path, otherwise it will not work.
    ccache_logfile = os.path.abspath(
        os.path.join(source_dir, "ccache-%d.txt" % os.getpid())
    )

    setEnvironmentVariable(env, "CCACHE_LOGFILE", ccache_logfile)
    env["CCACHE_LOGFILE"] = ccache_logfile

    ccache_binary = os.environ.get("NUITKA_CCACHE_BINARY")

    # If not provided, search it in PATH and guessed directories.
    if ccache_binary is None:
        ccache_binary = getExecutablePath("ccache", env)

        if ccache_binary is None:
            for candidate in _getCcacheGuessedPaths(python_prefix):
                if show_scons_mode:
                    scons_logger.info(
                        "Checking if ccache is at '%s' guessed path." % candidate
                    )

                if os.path.exists(candidate):
                    ccache_binary = candidate

                    if show_scons_mode:
                        scons_logger.info(
                            "Using ccache '%s' from guessed path." % ccache_binary
                        )

                    break
    else:
        if show_scons_mode:
            scons_logger.info(
                "Using ccache '%s' from NUITKA_CCACHE_BINARY environment."
                % ccache_binary
            )

    if ccache_binary is not None and os.path.exists(ccache_binary):
        if show_scons_mode:
            scons_logger.info(
                "Providing real CC path '%s' via PATH extension." % env["CC"]
            )

        assert getExecutablePath(os.path.basename(env["CC"]), env) == getExecutablePath(
            env["CC"], env
        )

        # Since we use absolute paths for CC, pass it like this, as ccache does not like absolute.
        env["CC"] = "%s %s" % (ccache_binary, os.path.basename(env["CC"]))

        # Do not consider scons cache anymore.
        if show_scons_mode:
            scons_logger.info(
                "Scons: Found ccache '%s' to cache C compilation result."
                % ccache_binary
            )

        result = True
    else:
        if isWin32Windows():
            scons_logger.warning(
                "Didn't find ccache, follow Nuitka user manual description."
            )

        result = False

    return result


def _getCcacheStatistics(ccache_logfile):
    data = {}

    if os.path.exists(ccache_logfile):
        re_command = re.compile(r"\[.*? (\d+) *\] Command line: (.*)$")
        re_result = re.compile(r"\[.*? (\d+) *\] Result: (.*)$")

        # Remember command from the pid, so later decision logged against pid
        # can be matched against it.
        commands = {}

        for line in open(ccache_logfile):
            match = re_command.match(line)

            if match:
                pid, command = match.groups()
                commands[pid] = command

            match = re_result.match(line)
            if match:
                pid, result = match.groups()

                if result != "called for link":
                    try:
                        data[commands[pid]] = result
                    except KeyError:
                        # It seems writing to the file can be lossy, so we can have results for
                        # unknown commands, but we don't use the command yet anyway, so just
                        # be unique.
                        data[line] = result

    return data


def checkCachingSuccess(source_dir):
    ccache_logfile = getSconsReportValue(source_dir, "CCACHE_LOGFILE")

    if ccache_logfile is not None:
        stats = _getCcacheStatistics(ccache_logfile)

        if not stats:
            scons_logger.warning("You are not using ccache.")
        else:
            counts = defaultdict(int)

            for _command, result in stats.items():
                counts[result] += 1

            scons_logger.info("Compiled %d C files using ccache." % len(stats))
            for result, count in counts.items():
                scons_logger.info(
                    "Cached C files (using ccache) with result '%s': %d"
                    % (result, count)
                )
