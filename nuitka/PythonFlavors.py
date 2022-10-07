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
""" Python flavors specifics.

This abstracts the Python variants from different people. There is not just
CPython, but Anaconda, Debian, pyenv, Apple, lots of people who make Python
in a way the requires technical differences, e.g. static linking, LTO, or
DLL presence, link paths, etc.

"""

import os
import sys

from nuitka.utils.FileOperations import isPathBelowOrSameAs
from nuitka.utils.Utils import (
    isFedoraBasedLinux,
    isLinux,
    isMacOS,
    isWin32Windows,
    withNoDeprecationWarning,
)

from .PythonVersions import (
    getRunningPythonDLLPath,
    getSystemPrefixPath,
    isStaticallyLinkedPython,
    python_version,
    python_version_str,
)


def isNuitkaPython():
    """Is this our own fork of CPython named Nuitka-Python."""

    # spell-checker: ignore nuitkapython

    if python_version >= 0x300:
        return sys.implementation.name == "nuitkapython"
    else:
        return sys.subversion[0] == "nuitkapython"


_is_anaconda = None


def isAnacondaPython():
    """Detect if Python variant Anaconda"""

    # singleton, pylint: disable=global-statement
    global _is_anaconda

    if _is_anaconda is None:
        _is_anaconda = os.path.exists(os.path.join(sys.prefix, "conda-meta"))

    return _is_anaconda


def isApplePython():
    if not isMacOS():
        return False

    # Python2 on 10.15 or higher
    if "+internal-os" in sys.version:
        return True

    # Older macOS had that
    if isPathBelowOrSameAs(path="/usr/bin/", filename=getSystemPrefixPath()):
        return True
    # Newer macOS has that
    if isPathBelowOrSameAs(
        path="/Library/Developer/CommandLineTools/", filename=getSystemPrefixPath()
    ):
        return True

    # Xcode has that on macOS, we consider it an Apple Python for now, it might
    # be more usable than Apple Python, we but we delay that.
    if isPathBelowOrSameAs(
        path="/Applications/Xcode.app/Contents/Developer/",
        filename=getSystemPrefixPath(),
    ):
        return True

    return False


def isHomebrewPython():
    if not isMacOS():
        return False

    candidate = os.path.join(
        getSystemPrefixPath(), "lib", "python" + python_version_str, "sitecustomize.py"
    )

    if os.path.exists(candidate):
        with open(candidate, "rb") as site_file:
            line = site_file.readline()

        if b"Homebrew" in line:
            return True

    return False


def isPyenvPython():
    if isWin32Windows():
        return False

    return os.environ.get("PYENV_ROOT") and isPathBelowOrSameAs(
        path=os.environ["PYENV_ROOT"], filename=getSystemPrefixPath()
    )


def isMSYS2MingwPython():
    if not isWin32Windows() or "GCC" not in sys.version:
        return False

    import sysconfig

    return "-mingw_" in sysconfig.get_config_var("SO")


def isUninstalledPython():
    # Debian package.
    if isDebianPackagePython():
        return False

    if isStaticallyLinkedPython():
        return False

    if os.name == "nt":
        import ctypes.wintypes

        GetSystemDirectory = ctypes.windll.kernel32.GetSystemDirectoryW
        GetSystemDirectory.argtypes = (ctypes.wintypes.LPWSTR, ctypes.wintypes.DWORD)
        GetSystemDirectory.restype = ctypes.wintypes.DWORD

        MAX_PATH = 4096
        buf = ctypes.create_unicode_buffer(MAX_PATH)

        res = GetSystemDirectory(buf, MAX_PATH)
        assert res != 0

        system_path = os.path.normcase(buf.value)
        return not getRunningPythonDLLPath().startswith(system_path)

    return isAnacondaPython() or "WinPython" in sys.version


def isWinPython():
    return "WinPython" in sys.version


def isDebianPackagePython():
    """Is this Python from a debian package."""

    if not isLinux():
        return False

    if python_version < 0x300:
        return hasattr(sys, "_multiarch")
    else:
        with withNoDeprecationWarning():
            try:
                from distutils.dir_util import _multiarch
            except ImportError:
                return False
            else:
                return True


def isFedoraPackagePython():
    """Is the Python from a Fedora package."""
    if not isFedoraBasedLinux():
        return False

    system_prefix_path = getSystemPrefixPath()

    return system_prefix_path == "/usr"


def isCPythonOfficialPackage():
    """Official CPython download, kind of hard to detect since self-compiled doesn't change much."""

    # For macOS however, it's very knowable.
    if isMacOS() and sys.executable.startswith(
        "/Library/Frameworks/Python.framework/Versions/"
    ):
        return True

    return False
