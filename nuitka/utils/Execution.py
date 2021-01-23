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
""" Program execution related stuff.

Basically a layer for os, subprocess, shutil to come together. It can find
binaries (needed for exec) and run them capturing outputs.
"""


import os
import shutil
import subprocess
from contextlib import contextmanager

from nuitka.PythonVersions import python_version
from nuitka.Tracing import general

from .Utils import getArchitecture, getOS, isWin32Windows


def callExec(args):
    """Do exec in a portable way preserving exit code.

    On Windows, unfortunately there is no real exec, so we have to spawn
    a new process instead.
    """

    # On Windows os.execl does not work properly
    if isWin32Windows():
        args = list(args)
        del args[1]

        try:
            process = subprocess.Popen(args=args)
            process.communicate()
            # No point in cleaning up, pylint: disable=protected-access
            try:
                os._exit(process.returncode)
            except OverflowError:
                # Seems negative values go wrong otherwise,
                # see https://bugs.python.org/issue28474
                os._exit(process.returncode - 2 ** 32)
        except KeyboardInterrupt:
            # There was a more relevant stack trace already, so abort this
            # right here, pylint: disable=protected-access
            os._exit(2)
    else:
        # The star arguments is the API of execl
        os.execl(*args)


def getExecutablePath(filename):
    """ Find an execute in PATH environment. """

    if python_version >= 0x300:
        return shutil.which(filename)
    else:
        # Append ".exe" suffix  on Windows if not already present.
        if getOS() == "Windows" and not filename.lower().endswith(".exe"):
            filename += ".exe"

        # Search in PATH environment.
        search_path = os.environ.get("PATH", "")

        # Now check in each path element, much like the shell will.
        path_elements = search_path.split(os.pathsep)

        for path_element in path_elements:
            path_element = path_element.strip('"')

            full = os.path.join(path_element, filename)

            if os.path.exists(full):
                return full


def getPythonExePathWindows(search, arch):
    """Find Python on Windows."""

    # Shortcuts for the default installation directories, to avoid going to
    # registry at all unless necessary. Any Python2 will do for Scons, so it
    # might be avoided entirely.

    # Windows only code, pylint: disable=I0021,import-error,undefined-variable
    try:
        import _winreg as winreg
    except ImportError:
        import winreg  # lint:ok

    if arch is None:
        if getArchitecture() == "x86":
            arches = (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY)
        else:
            arches = (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY)
    elif arch == "x86":
        arches = (winreg.KEY_WOW64_32KEY,)
    elif arch == "x86_64":
        arches = (winreg.KEY_WOW64_64KEY,)
    else:
        assert False, arch

    for hkey_branch in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for arch_key in arches:
            try:
                key = winreg.OpenKey(
                    hkey_branch,
                    r"SOFTWARE\Python\PythonCore\%s\InstallPath" % search,
                    0,
                    winreg.KEY_READ | arch_key,
                )

                candidate = os.path.join(winreg.QueryValue(key, ""), "python.exe")
            except WindowsError:
                continue

            if os.path.exists(candidate):
                return candidate


def check_output(*popenargs, **kwargs):
    """Call a process and check result code.

    This is for Python 2.6 compatibility, which doesn't have that in its
    standard library.

    Note: We use same name as in Python stdlib, violating our rules to
    make it more recognizable what this does.
    """

    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")

    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, _unused_err = process.communicate()
    retcode = process.poll()

    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]

        raise subprocess.CalledProcessError(retcode, cmd, output=output)

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


@contextmanager
def withEnvironmentPathAdded(env_var_name, *paths):
    paths = [path for path in paths if path]
    path = os.pathsep.join(paths)

    if path:
        if str is not bytes and type(path) is bytes:
            path = path.decode("utf-8")

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
def withEnvironmentVarOverriden(env_var_name, value):
    """ Change an environment and restore it after context. """

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
def withEnvironmentVarsOverriden(mapping):
    """ Change multiple environment variables and restore them after context. """

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
    lldb_path = getExecutablePath("lldb")

    if gdb_path is None and lldb_path is None:
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


def getPythonInstallPathWindows(supported, decider=lambda x: True):
    """Find suitable Python on Windows.

    Go over a list of provided, supported versions, and first try a few
    guesses for their paths, then look into registry for user or system wide
    installations.

    The decider may reject a Python, then the search is continued, otherwise
    it's returned.
    """
    # Many cases to deal with, due to arches, caching, etc.
    # pylint: disable=too-many-branches

    seen = set()

    # Shortcuts for the default installation directories, to avoid going to
    # registry at all unless necessary. Any Python2 will do for Scons, so it
    # might be avoided entirely.
    for search in supported:
        candidate = r"C:\Python%s\python.exe" % search.replace(".", "")

        if os.path.isfile(candidate):
            install_dir = os.path.normcase(os.path.dirname(candidate))

            if decider(install_dir):
                return install_dir

            seen.add(install_dir)

    # Windows only code, pylint: disable=I0021,import-error,undefined-variable
    if python_version < 0x300:
        import _winreg as winreg  # pylint: disable=I0021,import-error,no-name-in-module
    else:
        import winreg  # pylint: disable=I0021,import-error,no-name-in-module

    for search in supported:
        for hkey_branch in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for arch_key in (0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
                for suffix in "", "-32":
                    try:
                        key = winreg.OpenKey(
                            hkey_branch,
                            r"SOFTWARE\Python\PythonCore\%s%s\InstallPath"
                            % (search, suffix),
                            0,
                            winreg.KEY_READ | arch_key,
                        )

                        install_dir = os.path.normpath(winreg.QueryValue(key, ""))
                    except WindowsError:
                        pass
                    else:
                        if install_dir not in seen:
                            if decider(install_dir):
                                return install_dir

                            seen.add(install_dir)


def getNullOutput():
    try:
        return subprocess.NULLDEV
    except AttributeError:
        return open(os.devnull, "wb")
