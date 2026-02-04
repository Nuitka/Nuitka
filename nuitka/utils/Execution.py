#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Program execution related stuff.

Basically a layer for os, subprocess, shutil to come together. It can find
binaries (needed for exec) and run them capturing outputs.
"""

import errno
import os
import shlex
from contextlib import contextmanager

from nuitka.__past__ import iterItems, selectors, subprocess
from nuitka.Tracing import general

from .Download import getCachedDownloadedMinGW64
from .FileOperations import getExternalUsePath
from .Utils import getArchitecture, isWin32OrPosixWindows, isWin32Windows

# Cache, so we avoid repeated command lookups.
_executable_command_cache = {}

# We emulate and use APIs of stdlib and use special commands
# spell-checker: ignore popenargs,creationflags,preexec_fn,setsid,debuginfod,memcheck


def _getExecutablePath(filename, search_path):
    # Append ".exe" suffix  on Windows if not already present.
    if isWin32OrPosixWindows() and not filename.lower().endswith(
        (".exe", ".cmd", ".bat")
    ):
        filename += ".exe"

    # Now check in each path element, much like the shell will.
    path_elements = search_path.split(os.pathsep)

    for path_element in path_elements:
        path_element = path_element.strip('"')
        path_element = os.path.expanduser(path_element)

        candidate = None

        if os.path.isfile(path_element):
            if os.path.normcase(os.path.basename(path_element)) == os.path.normcase(
                filename
            ):
                candidate = path_element
        else:
            full = os.path.join(path_element, filename)

            if os.path.exists(full):
                candidate = full

        if candidate is not None:
            if os.access(candidate, os.X_OK):
                return candidate


def getExecutablePath(filename, extra_dir=None):
    """Find an execute in PATH environment."""

    # Search in PATH environment.
    search_path = os.getenv("PATH", "")

    if extra_dir is not None:
        search_path = extra_dir + os.pathsep + search_path

    key = (filename, search_path)
    if key not in _executable_command_cache:
        _executable_command_cache[key] = _getExecutablePath(filename, search_path)

    return _executable_command_cache[key]


def isExecutableCommand(command):
    return getExecutablePath(command) is not None


class NuitkaCalledProcessError(subprocess.CalledProcessError):
    def __init__(self, exit_code, cmd, output, stderr):
        # False alarm, pylint: disable=super-init-not-called

        subprocess.CalledProcessError(self, exit_code, cmd)

        # Python2 doesn't have this otherwise, but needs it.
        self.stderr = stderr
        self.output = output
        self.cmd = cmd
        self.returncode = exit_code

    def __str__(self):
        result = subprocess.CalledProcessError.__str__(self)

        if self.output:
            result += " Output was %r." % self.output.strip()

        if self.stderr:
            result += " Error was %r." % self.stderr.strip()

        return result


def check_output(*popenargs, **kwargs):
    """Call a process and check result code.

    This is for Python 2.6 compatibility, which doesn't have that in its
    standard library.

    Note: We use same name as in Python stdlib, violating our rules to
    make it more recognizable what this does.
    """
    logger = kwargs.pop("logger", None)

    if logger is not None:
        logger.info("Executing command '%s'." % popenargs[0], keep_format=True)

    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")

    if "stderr" not in kwargs:
        kwargs["stderr"] = subprocess.PIPE

    if "env" in kwargs:
        _checkEnvironment(kwargs["env"])

    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)

    output, stderr = process.communicate()
    exit_code = process.poll()

    if exit_code:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]

        raise NuitkaCalledProcessError(exit_code, cmd, output=output, stderr=stderr)

    return output


def check_call(*popenargs, **kwargs):
    """Call a process and check result code.

    Note: This catches the error, and makes it nicer, and an error
    exit. So this is for tooling only.

    Note: We use same name as in Python stdlib, violating our rules to
    make it more recognizable what this does.
    """
    logger = kwargs.pop("logger", None)

    if logger is not None:
        logger.info("Executing command '%s'." % popenargs[0], keep_format=True)

    try:
        if "env" in kwargs:
            _checkEnvironment(kwargs["env"])

        subprocess.check_call(*popenargs, **kwargs)
    except OSError:
        return general.sysexit(
            "Error, failed to execute '%s'. Is it installed?" % popenargs[0]
        )


def callProcess(*popenargs, **kwargs):
    """Call a process and return result code."""
    logger = kwargs.pop("logger", None)

    if logger is not None:
        logger.info("Executing command '%s'." % popenargs[0], keep_format=True)

    if "env" in kwargs:
        _checkEnvironment(kwargs["env"])

    return subprocess.call(*popenargs, **kwargs)


def callProcessChunked(command, chunks, **kwargs):
    """Call a process with arguments chunked to avoid Windows command line limits."""

    # Chunking to avoid command line length limit on Windows.
    # Windows limit is 32767 characters. We stay safely below.
    MAX_CMD_LEN = 20000

    chunk = []
    current_len = sum(len(arg) + 1 for arg in command)

    result = 0

    for filename in chunks:
        arg_len = len(filename) + 1

        if current_len + arg_len > MAX_CMD_LEN:
            chunk_result = callProcess(command + chunk, **kwargs)
            if chunk_result != 0:
                result = chunk_result

            chunk = []
            current_len = sum(len(arg) + 1 for arg in command)

        chunk.append(filename)
        current_len += arg_len

    if chunk:
        chunk_result = callProcess(command + chunk, **kwargs)
        if chunk_result != 0:
            result = chunk_result

    return result


@contextmanager
def withEnvironmentPathAdded(env_var_name, *paths, **kw):
    # Workaround star args with keyword args on older Python
    prefix = kw.pop("prefix", False)
    assert not kw, kw

    assert os.path.sep not in env_var_name

    paths = [path for path in paths if path]
    path = os.pathsep.join(paths)

    if path:
        if str is not bytes and type(path) is bytes:
            path = path.decode("utf8")

        if env_var_name in os.environ:
            old_path = os.environ[env_var_name]

            if not old_path:
                os.environ[env_var_name] = path
            elif prefix:
                os.environ[env_var_name] = path + os.pathsep + os.environ[env_var_name]
            else:
                os.environ[env_var_name] += os.pathsep + path
        else:
            old_path = None
            os.environ[env_var_name] = path

    yield

    if path:
        if old_path is None:
            del os.environ[env_var_name]
        else:
            os.environ[env_var_name] = old_path


@contextmanager
def withEnvironmentVarOverridden(env_var_name, value):
    """Change an environment and restore it after context."""

    if env_var_name in os.environ:
        old_value = os.environ[env_var_name]
    else:
        old_value = None

    if value is not None:
        os.environ[env_var_name] = value
    elif old_value is not None:
        del os.environ[env_var_name]

    yield

    if old_value is None:
        if value is not None:
            del os.environ[env_var_name]
    else:
        os.environ[env_var_name] = old_value


@contextmanager
def withEnvironmentVarsOverridden(mapping):
    """Change multiple environment variables and restore them after context."""

    if mapping is None:
        mapping = {}

    old_values = {}

    for env_var_name, value in mapping.items():
        if env_var_name in os.environ:
            old_values[env_var_name] = os.environ[env_var_name]
        else:
            old_values[env_var_name] = None

        if value is not None:
            os.environ[env_var_name] = value
        elif old_values[env_var_name] is not None:
            del os.environ[env_var_name]

    yield

    for env_var_name, value in mapping.items():
        if old_values[env_var_name] is None:
            if value is not None:
                del os.environ[env_var_name]
        else:
            os.environ[env_var_name] = old_values[env_var_name]


def wrapCommandForDebuggerForExec(command, debugger):
    """Wrap a command for system debugger to call exec

    Args:
        command: (iterable of str) args for call to be debugged
    Returns:
        args tuple with debugger command inserted

    Notes:
        Currently only gdb and lldb are supported, but adding more
        debuggers would be very welcome.
    """

    # The path needs to be absolute for some debuggers to work e.g. valgrind
    modified_command = list(command)
    modified_command[0] = os.path.abspath(command[0])
    command = tuple(modified_command)

    gdb_path = getExecutablePath("gdb")
    lldb_path = getExecutablePath("lldb")
    valgrind_path = getExecutablePath("valgrind")

    if debugger not in ("gdb", "lldb", "valgrind-memcheck", None):
        # We don't know how to do anything special for this debugger -- just
        # hope that the user set it up correctly.
        debugger_command_parts = shlex.split(debugger)

        debugger_name = debugger_command_parts[0]
        rest = tuple(debugger_command_parts[1:])

        debugger_path = getExecutablePath(debugger_name)
        if debugger_path is None:
            return general.sysexit(
                "Error, the selected debugger '%s' was not found in path."
                % debugger_name
            )
        return (debugger_path, debugger) + rest + command

    # Windows extra ball, attempt the downloaded one.
    if isWin32Windows() and gdb_path is None and lldb_path is None:
        from nuitka.options.Options import (
            assumeYesForDownloads,
            isExperimental,
        )

        mingw64_gcc_path = getCachedDownloadedMinGW64(
            target_arch=getArchitecture(),
            assume_yes_for_downloads=assumeYesForDownloads(),
            download_ok=True,
            experimental=isExperimental("winlibs-new"),
        )

        with withEnvironmentPathAdded("PATH", os.path.dirname(mingw64_gcc_path)):
            lldb_path = getExecutablePath("lldb")

    if gdb_path is None and lldb_path is None and valgrind_path is None:
        if lldb_path is None:
            return general.sysexit(
                "Error, no 'gdb', 'lldb', or 'valgrind' binary found in path."
            )

    if gdb_path is not None and debugger not in ("lldb", "valgrind-memcheck"):
        args = (
            gdb_path,
            "gdb",
            "-q",
            "-ex=set pagination off",
            "-ex=set debuginfod enabled off",
            "-ex=run",
            "-ex=where",
            "-ex=quit",
            "--args",
        ) + command
    elif lldb_path is not None and debugger not in ("gdb", "valgrind-memcheck"):
        args = (
            lldb_path,
            "lldb",
            "-o",
            "run",
            "-o",
            "bt",
            "-o",
            "quit",
            "--",
        ) + command
    elif valgrind_path is not None and debugger not in ("gdb", "lldb"):
        args = (
            valgrind_path,
            "valgrind",
            "--tool=memcheck",
            "--num-callers=25",
            #            "--leak-check=full",
        ) + command
    else:
        return general.sysexit(
            "Error, the selected debugger '%s' was not found in path."
        )

    return args


def wrapCommandForDebuggerForSubprocess(command, debugger):
    """Wrap a command for system debugger with subprocess module.

    Args:
        args: (list of str) args for call to be debugged
    Returns:
        args tuple with debugger command inserted

    Notes:
        Currently only gdb and lldb are supported, but adding more
        debuggers would be very welcome.
    """

    args = wrapCommandForDebuggerForExec(command=command, debugger=debugger)

    # Discard exec only argument.
    args = args[0:1] + args[2:]

    return args


@contextmanager
def getNullOutput():
    r = open(os.devnull, "wb")

    try:
        yield r
    finally:
        r.close()


@contextmanager
def getNullInput():
    r = open(os.devnull, "rb")

    try:
        yield r
    finally:
        r.close()


def filterOutputByLine(output, filter_func):
    """For use by stderr filters of executeToolChecked."""
    non_errors = []

    for line in output.splitlines():
        if line and not filter_func(line):
            non_errors.append(line)

    output = b"\n".join(non_errors)

    return (0 if non_errors else None), output


def executeToolChecked(
    logger,
    command,
    absence_message,
    stderr_filter=None,
    optional=False,
    decoding=False,
    context=None,
):
    """Execute external tool, checking for success and no error outputs, returning result."""

    # We are doing many returns, because for logger.sysexit() we need to
    # return from the function, for proper pylint support.
    # pylint: disable=too-many-return-statements

    command = list(command)
    tool = command[0]

    if not isExecutableCommand(tool):
        if optional:
            logger.warning(absence_message)
            return b"" if decoding else ""
        else:
            return logger.sysexit(absence_message)

    # Allow to avoid repeated scans in PATH for the tool.
    command[0] = getExecutablePath(tool)

    if None in command:
        return logger.sysexit(
            "Error, call to '%s' failed due to 'None' value: %s index %d."
            % (tool, command, command.index(None))
        )

    try:
        with withEnvironmentVarOverridden("LC_ALL", "C"):
            with getNullInput() as null_input:
                process = subprocess.Popen(
                    command,
                    stdin=null_input,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                )

        stdout, stderr = process.communicate()
        result = process.poll()
    except OSError as e:
        if e.errno != errno.E2BIG:
            raise

        return logger.sysexit(
            "Error, call to '%s' failed, command line was too long: %r"
            % (tool, command)
        )

    if stderr_filter is not None:
        new_result, stderr = stderr_filter(stderr, **(context or {}))

        if new_result is not None:
            result = new_result

    if result != 0:
        return logger.sysexit(
            "Error, call to '%s' failed: %s -> %s." % (tool, command, stderr)
        )
    elif stderr:
        return logger.sysexit(
            "Error, call to '%s' gave warnings: %s -> %s." % (tool, command, stderr)
        )

    if decoding:
        stdout = stdout.decode("utf8")

    return stdout


def _checkEnvironment(env):
    if not env:
        return

    # Make sure environment contains no None values
    for key, value in iterItems(env):
        if key is None:
            # This is probably not possible, but just in case.
            raise RuntimeError("Environment variable key cannot be None.")
        if value is None:
            raise RuntimeError("Environment variable '%s' value is None." % key)

        if not isinstance(key, str) or not isinstance(value, str):
            general.warning(
                "Illegal environment variable %r: %r (types %s, %s)"
                % (key, value, type(key), type(value))
            )

            # Dump the whole thing.
            general.warning("Environment was: %r" % env)

            raise TypeError(
                "Environment variable %r has wrong type %s"
                % (key, type(key) if not isinstance(key, str) else type(value))
            )


def createProcess(
    command,
    env=None,
    stdin=False,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    shell=False,
    external_cwd=False,
    new_group=False,
):
    if not env:
        env = os.environ

    _checkEnvironment(env)

    kw_args = {}
    if new_group:
        if isWin32Windows():
            kw_args["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kw_args["preexec_fn"] = os.setsid

    with getNullInput() as null_input:
        process = subprocess.Popen(
            command,
            # Note: Empty string should also be allowed for stdin, therefore check
            # for default "False" and "None" precisely.
            stdin=subprocess.PIPE if stdin not in (False, None) else null_input,
            stdout=stdout,
            stderr=stderr,
            shell=shell,
            # On Windows, closing file descriptions is not working with capturing outputs.
            close_fds=not isWin32Windows(),
            env=env,
            # For tools that want short paths to work.
            cwd=getExternalUsePath(os.getcwd()) if external_cwd else None,
            **kw_args
        )

    return process


def executeProcess(
    command,
    env=None,
    stdin=False,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    shell=False,
    external_cwd=False,
    rusage=False,
    timeout=None,
    logger=None,
):
    process = Process(
        command=command,
        env=env,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        shell=shell,
        external_cwd=external_cwd,
        rusage=rusage,
        timeout=timeout,
        logger=logger,
    )

    return process.communicate()


class Process(object):
    def __init__(
        self,
        command,
        env=None,
        stdin=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        external_cwd=False,
        rusage=False,
        timeout=None,
        logger=None,
    ):
        self.stdin = stdin
        self.timeout = timeout
        self.rusage = rusage

        # When running.
        self.process = None

        if logger is not None:
            logger.info("Executing command '%s'." % " ".join(command), keep_format=True)

        self.process = createProcess(
            command=command,
            env=env,
            stdin=self.stdin,
            stdout=stdout,
            stderr=stderr,
            shell=shell,
            external_cwd=external_cwd,
        )

    def communicate(self):
        if self.stdin is True:
            process_input = None
        elif self.stdin is not False:
            process_input = self.stdin
        else:
            process_input = None

        kw_args = {}
        if self.timeout is not None:
            # Apply timeout if possible.
            if "timeout" in subprocess.Popen.communicate.__code__.co_varnames:
                kw_args["timeout"] = self.timeout

        # TODO: May introduce a namedtuple for the return value.
        if self.rusage:
            return _communicateWithRusage(
                proc=self.process, process_input=process_input
            )
        else:
            stdout, stderr = self.process.communicate(input=process_input)
            exit_code = self.process.wait()

            return stdout, stderr, exit_code

    def stop(self):
        if self.process is not None:
            self.process.terminate()


def _communicateWithRusage(proc, process_input):
    """
    A correct implementation of communicate() that also returns resource usage.
    This version uses the high-level 'selectors' module for robust I/O handling.
    """

    # Complex code to replace communicate of Python, pylint: disable=too-many-branches,too-many-locals

    if selectors is None or not hasattr(os, "wait4"):
        stdout, stderr = proc.communicate(input=process_input)
        exit_code = proc.wait()
        rusage = {}
    else:
        # Use the best selector available for the current OS
        with selectors.DefaultSelector() as selector:
            # Register stdout and stderr for reading
            if proc.stdout:
                selector.register(proc.stdout, selectors.EVENT_READ)
            if proc.stderr:
                selector.register(proc.stderr, selectors.EVENT_READ)
            if proc.stdin and process_input:
                selector.register(proc.stdin, selectors.EVENT_WRITE)

            input_offset = 0
            if process_input is None:
                process_input = b""

            stdout_chunks = []
            stderr_chunks = []

            # The loop runs as long as there are file descriptors registered.
            # This is the correct way to check if we're done.
            while selector.get_map():
                # Wait for any of the registered file descriptors to be ready
                ready_events = selector.select()

                for key, mask in ready_events:
                    if mask & selectors.EVENT_READ:
                        # key.fileobj is the original file object (e.g., proc.stdout)
                        chunk = key.fileobj.read1(8192)

                        if not chunk:
                            # If we read empty bytes, the pipe has closed.
                            # Unregister it so the loop can terminate.
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                        elif key.fileobj is proc.stdout:
                            stdout_chunks.append(chunk)
                        else:  # key.fileobj is proc.stderr
                            stderr_chunks.append(chunk)
                    if mask & selectors.EVENT_WRITE:
                        chunk = process_input[input_offset : input_offset + 8192]
                        bytes_written = os.write(key.fileobj.fileno(), chunk)
                        input_offset += bytes_written

                        if input_offset >= len(process_input):
                            # All input written, close and unregister stdin.
                            selector.unregister(key.fileobj)
                            key.fileobj.close()

        # All I/O is done. Now, wait for the process and get the resource usage,
        # spell-checker: ignore ECHILD,WEXITSTATUS
        try:
            _pid, status, rusage = os.wait4(proc.pid, 0)
            exit_code = os.WEXITSTATUS(status)
        except OSError as e:
            # The ECHILD means the process is already reaped, which can happen with SCons
            # due to races in error cases.
            if e.errno == errno.ECHILD:
                exit_code = proc.wait()
                rusage = {}
            else:
                raise

        # Set the returncode on the original object for consistency
        proc.returncode = exit_code

        stdout = b"".join(stdout_chunks)
        stderr = b"".join(stderr_chunks)

    return stdout, stderr, exit_code, rusage


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
