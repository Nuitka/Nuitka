#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Scons interface.

Interaction with scons. Find the binary, and run it with a set of given
options.

"""


import contextlib
import os
import subprocess
import sys

from nuitka import Options, Tracing
from nuitka.PythonVersions import getTargetPythonDLLPath, python_version
from nuitka.utils import Execution, Utils


def getSconsDataPath():
    """ Return path to where data for scons lives, e.g. static C source files.

    """

    return os.path.dirname(__file__)


def _getSconsInlinePath():
    """ Return path to inline copy of scons. """

    return os.path.join(
        getSconsDataPath(),
        "inline_copy"
    )


def _getSconsBinaryCall():
    """ Return a way to execute Scons.

    Using potentially in-line copy if no system Scons is available
    or if we are on Windows, there it is mandatory.
    """
    if Utils.getOS() != "Windows":
        scons_path = Execution.getExecutablePath("scons")

        if scons_path is not None:
            return [
                _getPython2ExePath(),
                scons_path
            ]

    return [
        _getPython2ExePath(),
        os.path.join(
            _getSconsInlinePath(),
            "bin",
            "scons.py"
        )
    ]


def _getPython2ExePathWindows():
    """ Find Python2 on Windows.

    First try a few guesses, the look into registry for user or system wide
    installations of Python2. Both Python 2.6 and 2.7 will do.
    """

    # Shortcuts for the default installation directories, to avoid going to
    # registry at all unless necessary. Any Python2 will do for Scons, so it
    # might be avoided entirely.

    if os.path.isfile(r"c:\Python27\python.exe"):
        return r"c:\Python27\python.exe"
    elif os.path.isfile(r"c:\Python26\python.exe"):
        return r"c:\Python26\python.exe"

    # Windows only code, pylint: disable=import-error,undefined-variable,useless-suppression
    try:
        import _winreg as winreg
    except ImportError:
        import winreg  # lint:ok

    for search in ("2.7", "2.6"):
        for hkey_branch in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for arch_key in 0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY:
                try:
                    key = winreg.OpenKey(
                        hkey_branch,
                        r"SOFTWARE\Python\PythonCore\%s\InstallPath" % search,
                        0,
                        winreg.KEY_READ | arch_key
                    )

                    return os.path.join(
                        winreg.QueryValue(key, ""),
                        "python.exe"
                    )
                except WindowsError:  # @UndefinedVariable
                    pass


def _getPython2ExePath():
    """ Find a way to call any Python2.

    Scons needs it as it doesn't support Python3.
    """
    if python_version < 300:
        return sys.executable
    elif Utils.getOS() == "Windows":
        python_exe = _getPython2ExePathWindows()

        if python_exe is not None:
            return python_exe
        else:
            sys.exit("""\
Error, while Nuitka is fully Python3 compatible, it needs to find a
Python2 executable under C:\\Python26 or C:\\Python27 to execute
scons which is not yet Python3 compatible.""")

    candidate = Execution.getExecutablePath("python2.7")
    if candidate is None:
        candidate = Execution.getExecutablePath("python2.6")

        if candidate is None:
            candidate = Execution.getExecutablePath("python2")

    # Our weakest bet is that there is no "python3" named "python", but we
    # take it, as on some systems it's true.
    if candidate is None:
        candidate = "python"

    return candidate


@contextlib.contextmanager
def _setupSconsEnvironment():
    """ Setup the scons execution environment.

    For the scons inline copy on Windows needs to find the library, using
    the "SCONS_LIB_DIR" environment variable "NUITKA_SCONS". And for the
    target Python we provide "NUITKA_PYTHON_DLL_PATH" to see where the
    Python DLL lives, in case it needs to be copied, and then the
    "NUITKA_PYTHON_EXE_PATH" to find the Python installation itself.
    """

    if Utils.getOS() == "Windows":
        # On Windows this Scons variable must be set by us.
        os.environ["SCONS_LIB_DIR"] = os.path.join(
            _getSconsInlinePath(),
            "lib",
            "scons-2.3.2"
        )

        # On Windows, we use the Python.DLL path for some things. We pass it
        # via environment variable
        os.environ["NUITKA_PYTHON_DLL_PATH"] = getTargetPythonDLLPath()

        os.environ["NUITKA_PYTHON_EXE_PATH"] = sys.executable
    # Remove environment variables that can only harm if we have to switch
    # major Python versions, these cannot help Python2 to execute scons, this
    # is a bit of noise, but helpful.
    if python_version >= 300:
        if "PYTHONPATH" in os.environ:
            old_pythonpath = os.environ["PYTHONPATH"]
            del os.environ["PYTHONPATH"]
        else:
            old_pythonpath = None

        if "PYTHONHOME" in os.environ:
            old_pythonhome = os.environ["PYTHONHOME"]
            del os.environ["PYTHONHOME"]
        else:
            old_pythonhome = None

    yield

    if python_version >= 300:
        if old_pythonpath is not None:
            os.environ["PYTHONPATH"] = old_pythonpath

        if old_pythonhome is not None:
            os.environ["PYTHONHOME"] = old_pythonhome

    if Utils.getOS() == "Windows":
        del os.environ["NUITKA_PYTHON_DLL_PATH"]
        del os.environ["NUITKA_PYTHON_EXE_PATH"]


def _buildSconsCommand(quiet, options):
    """ Build the scons command to run.

    The options are a dictionary to be passed to scons as a command line,
    and other scons stuff is set.
    """

    scons_command = _getSconsBinaryCall()

    if quiet:
        scons_command.append("--quiet")

    scons_command += [
        # The scons file
        "-f",
        os.path.join(
            getSconsDataPath(),
            "SingleExe.scons"
        ),

        # Parallel compilation.
        "--jobs",
        str(Options.getJobLimit()),

        # Do not warn about deprecation from Scons
        "--warn=no-deprecated",

        # Don't load "site_scons" at all.
        "--no-site-dir",
    ]

    if Options.isShowScons():
        scons_command.append("--debug=explain")

    # Option values to provide to scons. Find these in the caller.
    for key, value in options.items():
        scons_command += [key + '=' + value]

    return scons_command


def runScons(options, quiet):
    with _setupSconsEnvironment():
        scons_command = _buildSconsCommand(quiet, options)

        if Options.isShowScons():
            Tracing.printLine("Scons command:", ' '.join(scons_command))

        Tracing.flushStdout()
        return subprocess.call(scons_command, shell = False) == 0
