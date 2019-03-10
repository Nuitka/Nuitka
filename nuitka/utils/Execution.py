#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
import subprocess
from contextlib import contextmanager

from .Utils import getArchitecture, getOS, isWin32Windows


def callExec(args):
    """ Do exec in a portable way preserving exit code.

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

    return None


def getPythonExePathWindows(search, arch):
    """ Find Python on Windows.

    """

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
            arches = (
                winreg.KEY_WOW64_32KEY,  # @UndefinedVariable
                winreg.KEY_WOW64_64KEY,  # @UndefinedVariable
            )
        else:
            arches = (
                winreg.KEY_WOW64_64KEY,  # @UndefinedVariable
                winreg.KEY_WOW64_32KEY,  # @UndefinedVariable
            )
    elif arch == "x86":
        arches = (winreg.KEY_WOW64_32KEY,)  # @UndefinedVariable
    elif arch == "x86_64":
        arches = (winreg.KEY_WOW64_64KEY,)  # @UndefinedVariable
    else:
        assert False, arch

    for hkey_branch in (
        winreg.HKEY_LOCAL_MACHINE,  # @UndefinedVariable
        winreg.HKEY_CURRENT_USER,  # @UndefinedVariable
    ):
        for arch_key in arches:
            try:
                key = winreg.OpenKey(  # @UndefinedVariable
                    hkey_branch,
                    r"SOFTWARE\Python\PythonCore\%s\InstallPath" % search,
                    0,
                    winreg.KEY_READ | arch_key,  # @UndefinedVariable
                )

                candidate = os.path.join(
                    winreg.QueryValue(key, ""), "python.exe"  # @UndefinedVariable
                )
            except WindowsError:  # @UndefinedVariable
                continue

            if os.path.exists(candidate):
                return candidate


def check_output(*popenargs, **kwargs):
    """ Call a process and check result code.

        This is for Python 2.6 compatibility, which doesn't have that in its
        standard library.
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


@contextmanager
def withEnvironmentPathAdded(env_var_name, path):
    if type(path) in (tuple, list):
        path = os.pathsep.join(path)

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
