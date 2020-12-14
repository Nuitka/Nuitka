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
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.Download import getCachedDownload
from nuitka.utils.Execution import getPythonInstallPathWindows
from nuitka.utils.FileOperations import (
    getExternalUsePath,
    getLinkTarget,
    makePath,
    withFileLock,
)
from nuitka.utils.Utils import getOS, isWin32Windows

from .SconsUtils import (
    getExecutablePath,
    getSconsReportValue,
    setEnvironmentVariable,
)


def _getPythonDirCandidates(python_prefix):
    result = [python_prefix]

    for python_dir in (
        sys.prefix,
        os.environ.get("CONDA_PREFIX"),
        os.environ.get("CONDA"),
    ):
        if python_dir and python_dir not in result:
            result.append(python_dir)

    return result


def _getCcacheGuessedPaths(python_prefix):
    if isWin32Windows():
        # Search the compiling Python, the Scons Python (likely the same, but not necessarily)
        # and then Anaconda, if an environment variable present from activated, or installed in
        # CI like Github actions.
        for python_dir in _getPythonDirCandidates(python_prefix):
            yield os.path.join(python_dir, "bin", "ccache.exe")
            yield os.path.join(python_dir, "scripts", "ccache.exe")

    elif getOS() == "Darwin":
        # For macOS, we might find Homebrew ccache installed but not in PATH.
        yield "/usr/local/opt/ccache"


def _getClcacheGuessedPaths(python_prefix):
    assert isWin32Windows()

    # Search the compiling Python, the Scons Python (likely the same, but not necessarily)
    # and then Anaconda, if an environment variable present from activated, or installed in
    # CI like Github actions.
    for python_dir in _getPythonDirCandidates(python_prefix):
        yield os.path.join(python_dir, "scripts", "clcache.exe")
        yield os.path.join(python_dir, "bin", "clcache.exe")


def _injectCcache(
    the_compiler, cc_path, env, python_prefix, show_scons_mode, assume_yes_for_downloads
):
    ccache_binary = os.environ.get("NUITKA_CCACHE_BINARY")

    # If not provided, search it in PATH and guessed directories.
    if ccache_binary is None:
        ccache_binary = getExecutablePath("ccache", env=env)

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

        if ccache_binary is None and os.name == "nt":
            url = "https://github.com/ccache/ccache/releases/download/v3.7.12/ccache-3.7.12-windows-32.zip"
            ccache_binary = getCachedDownload(
                url=url,
                is_arch_specific=False,
                specifity=url.rsplit("/", 2)[1],
                flatten=True,
                binary="ccache.exe",
                message="Nuitka will make use of ccache to speed up repeated compilation.",
                reject=None,
                assume_yes_for_downloads=assume_yes_for_downloads,
            )

    else:
        if show_scons_mode:
            scons_logger.info(
                "Using ccache '%s' from NUITKA_CCACHE_BINARY environment variable."
                % ccache_binary
            )

    if ccache_binary is not None and os.path.exists(ccache_binary):
        # Make sure the
        # In case we are on Windows, make sure the Anaconda form runs outside of Anaconda
        # environment, by adding DLL folder to PATH.
        assert getExecutablePath(os.path.basename(the_compiler), env=env) == cc_path

        # We use absolute paths for CC, pass it like this, as ccache does not like absolute.
        env["CXX"] = env["CC"] = "%s %s" % (ccache_binary, os.path.basename(cc_path))

        # Spare ccache the detection of the compiler, seems it will also misbehave when it's
        # prefixed with "ccache" on old gcc versions in terms of detecting need for C++ linkage.
        env["LINK"] = cc_path

        # Do not consider scons cache anymore.
        if show_scons_mode:
            scons_logger.info(
                "Found ccache '%s' to cache C compilation result." % ccache_binary
            )
            scons_logger.info(
                "Providing real CC path '%s' via PATH extension." % cc_path
            )

        result = True
    else:
        if isWin32Windows():
            scons_logger.warning(
                "Didn't find ccache for C level caching, follow Nuitka user manual description."
            )

        result = False

    return result


def enableCcache(
    the_compiler,
    env,
    source_dir,
    python_prefix,
    show_scons_mode,
    assume_yes_for_downloads,
):
    # The ccache needs absolute path, otherwise it will not work.
    ccache_logfile = os.path.abspath(
        os.path.join(source_dir, "ccache-%d.txt" % os.getpid())
    )

    setEnvironmentVariable(env, "CCACHE_LOGFILE", ccache_logfile)
    env["CCACHE_LOGFILE"] = ccache_logfile

    # Unless asked to do otherwise, store ccache files in our own directory.
    if "CCACHE_DIR" not in os.environ:
        ccache_dir = os.path.join(getCacheDir(), "ccache")
        makePath(ccache_dir)
        ccache_dir = getExternalUsePath(ccache_dir)
        setEnvironmentVariable(env, "CCACHE_DIR", ccache_dir)
        env["CCACHE_DIR"] = ccache_dir

    # First check if it's not already supposed to be a ccache, then do nothing.
    cc_path = getExecutablePath(the_compiler, env=env)

    cc_is_link, cc_link_path = getLinkTarget(cc_path)
    if cc_is_link and os.path.basename(cc_link_path) == "ccache":
        if show_scons_mode:
            scons_logger.info(
                "Chosen compiler %s is pointing to ccache %s already."
                % (cc_path, cc_link_path)
            )

        return True

    return _injectCcache(
        the_compiler=the_compiler,
        cc_path=cc_path,
        env=env,
        python_prefix=python_prefix,
        show_scons_mode=show_scons_mode,
        assume_yes_for_downloads=assume_yes_for_downloads,
    )


def enableClcache(the_compiler, env, source_dir, python_prefix, show_scons_mode):
    # Many branches to deal with, pylint: disable=too-many-branches

    # The ccache needs absolute path, otherwise it will not work.
    clcache_logfile = os.path.abspath(
        os.path.join(source_dir, "clcache-%d.txt" % os.getpid())
    )

    # Our spawn function will pick it up from the output.
    setEnvironmentVariable(env, "CLCACHE_LOG", clcache_logfile)
    env["CLCACHE_LOG"] = clcache_logfile

    clcache_binary = os.environ.get("NUITKA_CLCACHE_BINARY")

    # If not provided, search it in PATH and guessed directories.
    if clcache_binary is None:
        clcache_binary = getExecutablePath("clcache", env)

        if clcache_binary is None:
            for candidate in _getClcacheGuessedPaths(python_prefix):
                if show_scons_mode:
                    scons_logger.info(
                        "Checking if clcache is at '%s' guessed path." % candidate
                    )

                if os.path.exists(candidate):
                    clcache_binary = candidate

                    if show_scons_mode:
                        scons_logger.info(
                            "Using clcache '%s' from guessed path." % clcache_binary
                        )

                    break

        if clcache_binary is None and os.name == "nt":

            def checkClcache(install_dir):
                candidate = os.path.join(install_dir, "scripts", "clcache.exe")

                if show_scons_mode:
                    scons_logger.info(
                        "Checking if clcache is at '%s' python installation path."
                        % candidate
                    )

                if os.path.exists(candidate):
                    return True

            candidate = getPythonInstallPathWindows(
                supported=("3.6", "3.7", "3.8", "3.9"), decider=checkClcache
            )

            if candidate is not None:
                clcache_binary = os.path.join(candidate, "scripts", "clcache.exe")

                if show_scons_mode:
                    scons_logger.info(
                        "Using clcache '%s' from registry path." % clcache_binary
                    )

    else:
        if show_scons_mode:
            scons_logger.info(
                "Using clcache '%s' from NUITKA_CLCACHE_BINARY environment variable."
                % clcache_binary
            )

    if clcache_binary is not None and os.path.exists(clcache_binary):
        cl_binary = getExecutablePath(the_compiler, env)

        # The compiler is passed via environment.
        setEnvironmentVariable(env, "CLCACHE_CL", cl_binary)
        env["CXX"] = env["CC"] = clcache_binary

        if show_scons_mode:
            scons_logger.info(
                "Found clcache '%s' to cache C compilation result." % clcache_binary
            )
            scons_logger.info(
                "Providing real cl.exe path '%s' via environment." % cl_binary
            )

        result = True
    else:
        scons_logger.warning(
            "Didn't find clcache for C level caching, follow Nuitka user manual description."
        )

        result = False

    return result


def _getCcacheStatistics(ccache_logfile):
    data = {}

    if os.path.exists(ccache_logfile):
        re_command = re.compile(r"\[.*? (\d+) *\] Command line: (.*)$")
        re_result = re.compile(r"\[.*? (\d+) *\] Result: (.*)$")
        re_anything = re.compile(r"\[.*? (\d+) *\] (.*)$")

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
                result = result.strip()

                try:
                    command = data[commands[pid]]
                except KeyError:
                    # It seems writing to the file can be lossy, so we can have results for
                    # unknown commands, but we don't use the command yet anyway, so just
                    # be unique.
                    command = "unknown command leading to " + line

                # Older ccache on e.g. RHEL6 wasn't explicit about linking.
                if result == "unsupported compiler option":
                    if " -o " in command or "unknown command" in command:
                        result = "called for link"

                # But still try to catch this with log output if it happens.
                if result == "unsupported compiler option":
                    scons_logger.warning(
                        "Encountered unsupported compiler option for ccache in '%s'."
                        % command
                    )

                    all_text = []

                    for line2 in open(ccache_logfile):
                        match = re_anything.match(line2)

                        if match:
                            pid2, result = match.groups()
                            if pid == pid2:
                                all_text.append(result)

                    scons_logger.warning("Full scons output: %s" % all_text)

                if result != "called for link":
                    data[command] = result

    return data


def _getClcacheStatistics(clcache_logfile):
    data = {}

    if os.path.exists(clcache_logfile):
        for line in open(clcache_logfile):
            filename, cache_result = line.rstrip().rsplit("=", 1)
            data[filename] = cache_result

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

    clcache_logfile = getSconsReportValue(source_dir, "CLCACHE_LOG")

    if clcache_logfile is not None:
        stats = _getClcacheStatistics(clcache_logfile)

        if not stats:
            scons_logger.warning("You are not using clcache.")
        else:
            counts = defaultdict(int)

            for _command, result in stats.items():
                counts[result] += 1

            scons_logger.info("Compiled %d C files using clcache." % len(stats))
            for result, count in counts.items():
                scons_logger.info(
                    "Cached C files (using clcache) with result '%s': %d"
                    % (result, count)
                )


clcache_data = {}


def _writeClcacheLog(filename, cache_result):
    with withFileLock():
        with open(os.environ["CLCACHE_LOG"], "a") as clcache_log:
            clcache_log.write("%s=%s\n" % (filename, cache_result))


def extractClcacheLogFromOutput(data):
    clcache_output = []
    normal_output = []

    for line in data.split(b"\n"):
        # Remove the "\r", clcache and compiler may or may not output it.
        line = line.strip()

        if b"clcache.py" in line:
            clcache_output.append(line)
        else:
            normal_output.append(line)

    # Make sure we have Windows new lines for the compiler output though.
    data = b"\r\n".join(normal_output)
    if data:
        data += b"\r\n"

    for clcache_line in clcache_output:
        match = re.search(b"Reusing cached object.*?for object file (.*)", clcache_line)

        if match:
            _writeClcacheLog(match.group(1), "cache hit")
            return data

        match = re.search(b"Adding file (.*?) to cache", clcache_line)
        if match:
            _writeClcacheLog(match.group(1), "cache miss")
            return data

        match = re.search(b"Real compiler returned code (\\d+)", clcache_line)
        if match and match.group(1) != b"0":
            _writeClcacheLog(match.group(1), "compile error")
            return data

        match = re.search(b"Compiler source files: \\['(.*?)'\\]", clcache_line)
        if match:
            _writeClcacheLog(match.group(1), "cache miss")
            return data

    if clcache_output:
        # Sometimes no message at all might be recognized.
        scons_logger.warning("Caching with clcache could not be decoded, got this:")
        scons_logger.warning(b"\n".join(clcache_output))

    return data
