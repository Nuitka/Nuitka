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
""" Program execution related stuff.

Basically a layer for os, subprocess, shutil to come together. It can find
binaries (needed for exec) and run them capturing outputs.
"""


import os
from contextlib import contextmanager

from nuitka.__past__ import subprocess
from nuitka.Tracing import general

from .Download import getCachedDownloadedMinGW64
from .FileOperations import getExternalUsePath
from .Utils import getArchitecture, isWin32OrPosixWindows, isWin32Windows

# Cache, so we avoid repeated command lookups.
_executable_command_cache = {}

# We emulate and use APIs of stdlib, spell-checker: ignore popenargs,creationflags,preexec_fn,setsid


def _getExecutablePath(filename, search_path):
    # Append ".exe" suffix  on Windows if not already present.
    if isWin32OrPosixWindows() and not filename.lower().endswith(".exe"):
        filename += ".exe"

    # Now check in each path element, much like the shell will.
    path_elements = search_path.split(os.pathsep)

    for path_element in path_elements:
        path_element = path_element.strip('"')
        path_element = os.path.expanduser(path_element)

        if os.path.isfile(path_element):
            if os.path.normcase(os.path.basename(path_element)) == os.path.normcase(
                filename
            ):
                return path_element
        else:
            full = os.path.join(path_element, filename)

            if os.path.exists(full):
                return full


def getExecutablePath(filename, extra_dir=None):
    """Find an execute in PATH environment."""

    # Search in PATH environment.
    search_path = os.environ.get("PATH", "")

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

    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")

    if "stderr" not in kwargs:
        kwargs["stderr"] = subprocess.PIPE

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
    try:
        subprocess.check_call(*popenargs, **kwargs)
    except OSError:
        general.sysexit(
            "Error, failed to execute '%s'. Is it installed?" % popenargs[0]
        )


def callProcess(*popenargs, **kwargs):
    """Call a process and return result code."""
    subprocess.call(*popenargs, **kwargs)


@contextmanager
def withEnvironmentPathAdded(env_var_name, *paths):
    assert os.path.sep not in env_var_name

    paths = [path for path in paths if path]
    path = os.pathsep.join(paths)

    if path:
        if str is not bytes and type(path) is bytes:
            path = path.decode("utf8")

        if env_var_name in os.environ:
            old_path = os.environ[env_var_name]
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


def wrapCommandForDebuggerForExec(*args):
    """Wrap a command for system debugger to call exec

    Args:
        args: (list of str) args for call to be debugged
    Returns:
        args tuple with debugger command inserted

    Notes:
        Currently only gdb and lldb are supported, but adding more
        debuggers would be very welcome.
    """

    gdb_path = getExecutablePath("gdb")
    lldb_path = None

    # Windows extra ball, attempt the downloaded one.
    if isWin32Windows() and gdb_path is None:
        from nuitka.Options import assumeYesForDownloads

        mingw64_gcc_path = getCachedDownloadedMinGW64(
            target_arch=getArchitecture(),
            assume_yes_for_downloads=assumeYesForDownloads(),
        )

        with withEnvironmentPathAdded("PATH", os.path.dirname(mingw64_gcc_path)):
            lldb_path = getExecutablePath("lldb")

    if gdb_path is None and lldb_path is None:
        lldb_path = getExecutablePath("lldb")

        if lldb_path is None:
            general.sysexit("Error, no 'gdb' or 'lldb' binary found in path.")

    if gdb_path is not None:
        args = (gdb_path, "gdb", "-ex=run", "-ex=where", "-ex=quit", "--args") + args
    else:
        args = (lldb_path, "lldb", "-o", "run", "-o", "bt", "-o", "quit", "--") + args

    return args


def wrapCommandForDebuggerForSubprocess(*args):
    """Wrap a command for system debugger with subprocess module.

    Args:
        args: (list of str) args for call to be debugged
    Returns:
        args tuple with debugger command inserted

    Notes:
        Currently only gdb and lldb are supported, but adding more
        debuggers would be very welcome.
    """

    args = wrapCommandForDebuggerForExec(*args)

    # Discard exec only argument.
    args = args[0:1] + args[2:]

    return args


def getNullOutput():
    try:
        return subprocess.NULLDEV
    except AttributeError:
        return open(os.devnull, "wb")


def getNullInput():
    # spell-checker: ignore NULLDEV
    try:
        return subprocess.NULLDEV
    except AttributeError:
        # File is supposed to stay open, pylint: disable=consider-using-with
        subprocess.NULLDEV = open(os.devnull, "rb")
        return subprocess.NULLDEV


def executeToolChecked(logger, command, absence_message, stderr_filter=None):
    """Execute external tool, checking for success and no error outputs, returning result."""

    command = list(command)
    tool = command[0]

    if not isExecutableCommand(tool):
        logger.sysexit(absence_message)

    # Allow to avoid repeated scans in PATH for the tool.
    command[0] = getExecutablePath(tool)

    process = subprocess.Popen(
        command,
        stdin=getNullInput(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )

    stdout, stderr = process.communicate()
    result = process.poll()

    if stderr_filter is not None:
        new_result, stderr = stderr_filter(stderr)

        if new_result is not None:
            result = new_result

    if result != 0:
        logger.sysexit(
            "Error, call to '%s' failed: %s -> %s." % (tool, command, stderr)
        )
    elif stderr:
        logger.sysexit(
            "Error, call to '%s' gave warnings: %s -> %s." % (tool, command, stderr)
        )

    return stdout


def createProcess(
    command,
    env=None,
    stdin=False,
    stdout=None,
    stderr=None,
    shell=False,
    external_cwd=False,
    new_group=False,
):
    if not env:
        env = os.environ

    kw_args = {}
    if new_group:
        if isWin32Windows():
            kw_args["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kw_args["preexec_fn"] = os.setsid

    process = subprocess.Popen(
        command,
        # Note: Empty string should also be allowed for stdin, therefore check
        # for default "False" and "None" precisely.
        stdin=subprocess.PIPE if stdin not in (False, None) else getNullInput(),
        stdout=subprocess.PIPE if stdout is None else stdout,
        stderr=subprocess.PIPE if stderr is None else stderr,
        shell=shell,
        # On Windows, closing file descriptions is not working with capturing outputs.
        close_fds=not isWin32Windows(),
        env=env,
        # For tools that want short paths to work.
        cwd=getExternalUsePath(os.getcwd()) if external_cwd else None,
        **kw_args
    )

    return process


def executeProcess(command, env=None, stdin=False, shell=False, external_cwd=False):
    process = createProcess(
        command=command, env=env, stdin=stdin, shell=shell, external_cwd=external_cwd
    )

    if stdin is True:
        process_input = None
    elif stdin is not False:
        process_input = stdin
    else:
        process_input = None

    stdout, stderr = process.communicate(input=process_input)
    exit_code = process.wait()

    return stdout, stderr, exit_code
