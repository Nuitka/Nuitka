#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""
Scons interface.

Interaction with scons. Find the binary, and run it with a set of given
options.

"""


import os
import subprocess
import sys

from nuitka import Options, Tracing, Utils


def getSconsDataPath():
    return Utils.dirname(__file__)


def getSconsInlinePath():
    return Utils.joinpath(getSconsDataPath(), "inline_copy")


def getSconsBinaryCall():
    """ Return a way to execute Scons.

        Using potentially inline copy if no system Scons is available
        or if we are on Windows.
    """
    if Utils.isFile("/usr/bin/scons"):
        return ["/usr/bin/scons"]
    else:
        return [
            getPython2ExePath(),
            Utils.joinpath(getSconsInlinePath(), "bin", "scons.py")
        ]


def _getPython2ExePathWindows():
    # Shortcuts for the default installation directories, to avoid going to
    # registry at all.

    if os.path.isfile(r"c:\Python27\python.exe"):
        return r"c:\Python27\python.exe"
    elif os.path.isfile(r"c:\Python26\python.exe"):
        return r"c:\Python26\python.exe"

    # Windows only code, pylint: disable=E0602,F0401
    try:
        import _winreg as winreg
    except ImportError:
        import winreg  # lint:ok

    for search in ("2.7", "2.6"):
        for arch_key in 0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY:
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Python\PythonCore\%s\InstallPath" % search,
                    0,
                    winreg.KEY_READ | arch_key
                )

                return Utils.joinpath(
                    winreg.QueryValue(key, ''),
                    "python.exe"
                )
            except WindowsError:  # lint:ok
                pass


def getPython2ExePath():
    """ Find a way to call Python2. Scons needs it."""
    if Utils.python_version < 300:
        return sys.executable
    elif Utils.getOS() == "Windows":
        python_exe = _getPython2ExePathWindows()

        if python_exe is not None:
            return python_exe
        else:
            sys.exit("""\
Error, need to find Python2 executable under C:\\Python26 or \
C:\\Python27 to execute scons which is not Python3 compatible.""")
    elif os.path.exists("/usr/bin/python2"):
        return "python2"
    else:
        return "python"


def runScons(options, quiet):
    # For the scons file to find the static C++ files and include path. The
    # scons file is unable to use __file__ for the task.
    os.environ["NUITKA_SCONS"] = getSconsDataPath()

    if Utils.getOS() == "Windows":
        # On Windows this Scons variable must be set by us.
        os.environ["SCONS_LIB_DIR"] = Utils.joinpath(
            getSconsInlinePath(),
            "lib",
            "scons-2.3.0"
        )

        # Also, for MinGW we can avoid the user having to add the path if he
        # used the default path or installed it on the same drive by appending
        # to the PATH variable before executing scons.
        os.environ["PATH"] += r";\MinGW\bin;C:\MinGW\bin"

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

        # Do not warn about deprecations of Scons
        "--warn=no-deprecated",

        # Don't load "site_scons" at all.
        "--no-site-dir",
    ]

    if Options.isShowScons():
        scons_command.append("--debug=explain")

    # Option values to provide to scons.
    for key, value in options.items():
        scons_command += [key + "=" + value]

    if Options.isShowScons():
        Tracing.printLine("Scons command:", " ".join(scons_command))

    return 0 == subprocess.call(scons_command, shell = False)
