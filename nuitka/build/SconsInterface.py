#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
from nuitka.utils import Utils


def getSconsDataPath():
    return Utils.dirname(__file__)


def getSconsInlinePath():
    return Utils.joinpath(getSconsDataPath(), "inline_copy")


def getSconsBinaryCall():
    """ Return a way to execute Scons.

        Using potentially in-line copy if no system Scons is available
        or if we are on Windows.
    """
    if Utils.getOS() != "Windows" and Utils.isFile("/usr/bin/scons"):
        return ["/usr/bin/scons"]
    else:
        return [
            getPython2ExePath(),
            Utils.joinpath(getSconsInlinePath(), "bin", "scons.py")
        ]


def _getPython2ExePathWindows():
    # Shortcuts for the default installation directories, to avoid going to
    # registry at all unless necessary. Any Python2 will do for Scons, so it
    # can be avoided.

    if os.path.isfile(r"c:\Python27\python.exe"):
        return r"c:\Python27\python.exe"
    elif os.path.isfile(r"c:\Python26\python.exe"):
        return r"c:\Python26\python.exe"

    # Windows only code, pylint: disable=E0602,F0401,I0021
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

                    return Utils.joinpath(
                        winreg.QueryValue(key, ""),
                        "python.exe"
                    )
                except WindowsError:  # @UndefinedVariable
                    pass


def getPython2ExePath():
    """ Find a way to call Python2. Scons needs it."""
    if python_version < 300:
        return sys.executable
    elif Utils.getOS() == "Windows":
        python_exe = _getPython2ExePathWindows()

        if python_exe is not None:
            return python_exe
        else:
            sys.exit("""\
Error, need to find Python2 executable under C:\\Python26 or \
C:\\Python27 to execute scons which is not Python3 compatible.""")
    elif Utils.isFile("/usr/bin/python2.7"):
        return "/usr/bin/python2.7"
    elif Utils.isFile("/usr/bin/python2.6"):
        return "/usr/bin/python2.6"
    elif Utils.isFile("/usr/bin/python2"):
        return "/usr/bin/python2"
    else:
        return "python"

@contextlib.contextmanager
def setupSconsEnvironment():
    # For the scons file to find the static C++ files and include path. The
    # scons file is unable to use __file__ for the task.
    os.environ["NUITKA_SCONS"] = getSconsDataPath()

    if Utils.getOS() == "Windows":
        # On Windows this Scons variable must be set by us.
        os.environ["SCONS_LIB_DIR"] = Utils.joinpath(
            getSconsInlinePath(),
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


def buildSconsCommand(quiet, options):
    scons_command = getSconsBinaryCall()

    if quiet:
        scons_command.append("--quiet")

    scons_command += [
        # The scons file
        "-f",
        Utils.joinpath(getSconsDataPath(), "SingleExe.scons"),

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
    with setupSconsEnvironment():
        scons_command = buildSconsCommand(quiet, options)

        if Options.isShowScons():
            Tracing.printLine("Scons command:", ' '.join(scons_command))

        return subprocess.call(scons_command, shell = False) == 0
