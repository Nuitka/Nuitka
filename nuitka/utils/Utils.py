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
""" Utility module.

Here the small things that fit nowhere else and don't deserve their own module.

"""

import os
import sys

from nuitka.PythonVersions import python_version


def getOS():
    if os.name == "nt":
        return "Windows"
    elif os.name == "posix":
        result = os.uname()[0]

        # Handle msys2 posix nature still meaning it's Windows.
        if result.startswith(("MSYS_NT-", "MINGW64_NT-")):
            result = "Windows"

        return result
    else:
        assert False, os.name


def isWin32Windows():
    """The Win32 variants of Python does have win32 only, not posix."""
    return os.name == "nt"


def isPosixWindows():
    """The MSYS2 variant of Python does have posix only, not Win32."""
    return os.name == "posix" and getOS() == "Windows"


_is_alpine = None


def isAlpineLinux():
    if os.name == "posix":

        # Avoid repeated file system lookup, pylint: disable=global-statement
        global _is_alpine
        if _is_alpine is None:
            _is_alpine = os.path.isfile("/etc/alpine-release")

        return _is_alpine
    else:
        return False


def getArchitecture():
    if getOS() == "Windows":
        if "AMD64" in sys.version:
            return "x86_64"
        else:
            return "x86"
    else:
        return os.uname()[4]


def getCoreCount():
    cpu_count = 0

    # Try to sum up the CPU cores, if the kernel shows them.
    try:
        # Try to get the number of logical processors
        with open("/proc/cpuinfo") as cpuinfo_file:
            cpu_count = cpuinfo_file.read().count("processor\t:")
    except IOError:
        pass

    if not cpu_count:
        import multiprocessing

        cpu_count = multiprocessing.cpu_count()

    return cpu_count


def encodeNonAscii(var_name):
    """Encode variable name that is potentially not ASCII to ASCII only.

    For Python3, unicode identifiers can be used, but these are not
    possible in C, so we need to replace them.
    """
    if python_version < 0x300:
        return var_name
    else:
        # Using a escaping here, because that makes it safe in terms of not
        # to occur in the encoding escape sequence for unicode use.
        var_name = var_name.replace("$$", "$_$")

        var_name = var_name.encode("ascii", "xmlcharrefreplace")
        var_name = var_name.decode("ascii")

        return var_name.replace("&#", "$$").replace(";", "")


def hasOnefileSupportedOS():
    return getOS() in ("Linux", "Windows")
