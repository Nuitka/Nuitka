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
""" Scons interface.

Interaction with scons. Find the binary, and run it with a set of given
options.

"""


import contextlib
import os
import subprocess
import sys

from nuitka import Options, Tracing
from nuitka.__past__ import unicode  # pylint: disable=I0021,redefined-builtin
from nuitka.PythonVersions import getTargetPythonDLLPath, python_version
from nuitka.utils import Execution, Utils
from nuitka.utils.FileOperations import getWindowsShortPathName


def getSconsDataPath():
    """ Return path to where data for scons lives, e.g. static C source files.

    """

    return os.path.dirname(__file__)


def _getSconsInlinePath():
    """ Return path to inline copy of scons. """

    return os.path.join(getSconsDataPath(), "inline_copy")


def _getSconsBinaryCall():
    """ Return a way to execute Scons.

    Using potentially in-line copy if no system Scons is available
    or if we are on Windows, there it is mandatory.
    """
    if Utils.getOS() != "Windows":
        scons_path = Execution.getExecutablePath("scons")

        if scons_path is not None:
            return [scons_path]

    return [
        _getPythonForSconsExePath(),
        "-W",
        "ignore",  # Disable Python warnings in case of debug Python.
        os.path.join(_getSconsInlinePath(), "bin", "scons.py"),
    ]


def _getPythonSconsExePathWindows():
    """ Find Python2 on Windows.

    First try a few guesses, the look into registry for user or system wide
    installations of Python2. Both Python 2.6 and 2.7, and 3.5 or higher
    will do.
    """

    # Ordered in the list of preference.
    scons_supported = ("2.7", "2.6", "3.5", "3.6", "3.7")

    # Shortcuts for the default installation directories, to avoid going to
    # registry at all unless necessary. Any Python2 will do for Scons, so it
    # might be avoided entirely.
    for search in scons_supported:
        candidate = r"c:\Python%s\python.exe" % search.replace(".", "")

        if os.path.isfile(candidate):
            return candidate

    # Windows only code, pylint: disable=I0021,import-error,undefined-variable
    if python_version < 300:
        import _winreg as winreg  # @UnresolvedImport @UnusedImport pylint: disable=I0021,import-error,no-name-in-module
    else:
        import winreg  # @Reimport @UnresolvedImport pylint: disable=I0021,import-error,no-name-in-module

    for search in scons_supported:
        for hkey_branch in (
            winreg.HKEY_LOCAL_MACHINE,  # @UndefinedVariable
            winreg.HKEY_CURRENT_USER,  # @UndefinedVariable
        ):
            for arch_key in (
                0,
                winreg.KEY_WOW64_32KEY,  # @UndefinedVariable
                winreg.KEY_WOW64_64KEY,  # @UndefinedVariable
            ):  # @UndefinedVariable
                try:
                    key = winreg.OpenKey(  # @UndefinedVariable
                        hkey_branch,
                        r"SOFTWARE\Python\PythonCore\%s\InstallPath" % search,
                        0,
                        winreg.KEY_READ | arch_key,  # @UndefinedVariable
                    )

                    return os.path.join(
                        winreg.QueryValue(key, ""), "python.exe"  # @UndefinedVariable
                    )
                except WindowsError:  # @UndefinedVariable
                    pass


def _getPythonForSconsExePath():
    """ Find a way to call any Python2.

    Scons needs it as it doesn't support Python3.
    """
    python_exe = Options.getPythonPathForScons()

    if python_exe is not None:
        return python_exe

    if python_version < 300 or python_version >= 350:
        return sys.executable
    elif Utils.getOS() == "Windows":
        python_exe = _getPythonSconsExePathWindows()

        if python_exe is not None:
            return python_exe
        else:
            sys.exit(
                """\
Error, while Nuitka works with Python 3.2 to 3.4, scons does not, and Nuitka
needs to find a Python executable 2.6/2.7 or 3.5 or higher. Simply under the
C:\\PythonXY, e.g. C:\\Python27 to execute the scons utility which is used
to build the C files to binary.

You may provide it using option "--python-for-scons=path_to_python.exe"
in case it is not visible in registry, e.g. due to using uninstalled
AnaConda Python.
"""
            )

    for version_candidate in ("2.7", "2.6", "3.5", "3.6", "3.7"):
        candidate = Execution.getExecutablePath("python" + version_candidate)

        if candidate is not None:
            return candidate

    # Lets be optimistic, this is most often going to be new enough or a
    # Python2 variant.
    return "python"


@contextlib.contextmanager
def _setupSconsEnvironment():
    """ Setup the scons execution environment.

    For the scons inline copy on Windows needs to find the library, using
    the "SCONS_LIB_DIR" environment variable "NUITKA_SCONS". And for the
    target Python we provide "NUITKA_PYTHON_DLL_PATH" to see where the
    Python DLL lives, in case it needs to be copied, and then the
    "NUITKA_PYTHON_EXE_PATH" to find the Python binary itself.
    """

    # For Python2, avoid unicode working directory.
    if Utils.isWin32Windows() and python_version < 300:
        if os.getcwd() != os.getcwdu():
            os.chdir(getWindowsShortPathName(os.getcwdu()))

    if Utils.isWin32Windows():
        # On Win32, we use the Python.DLL path for some things. We pass it
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

    if Utils.isWin32Windows():
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
        os.path.join(getSconsDataPath(), "SingleExe.scons"),
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

    # Python2, encoding unicode values
    def encode(value):
        if str is bytes and type(value) is unicode:
            return value.encode("utf8")
        else:
            return value

    # Option values to provide to scons. Find these in the caller.
    for key, value in options.items():
        scons_command.append(key + "=" + encode(value))

    # Python2, make argument encoding recognizable.
    if str is bytes:
        scons_command.append("arg_encoding=utf8")

    return scons_command


def runScons(options, quiet):
    with _setupSconsEnvironment():
        scons_command = _buildSconsCommand(quiet, options)

        if Options.isShowScons():
            Tracing.printLine("Scons command:", " ".join(scons_command))

        Tracing.flushStdout()
        return subprocess.call(scons_command, shell=False) == 0
