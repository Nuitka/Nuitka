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
from contextlib import contextmanager


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


_linux_distribution_info = None


def getLinuxDistribution():
    """Name of the Linux distribution.

    We should usually avoid this, and rather test for the feature,
    but in some cases it's hard to manage that.
    """
    # singleton, pylint: disable=global-statement
    global _linux_distribution_info

    if getOS() != "Linux":
        return None, None

    if _linux_distribution_info is None:
        import platform

        # pylint: disable=I0021,deprecated-method,no-member
        try:
            result = platform.dist()[0]
            version = platform.dist()[1]
        except AttributeError:
            result = None
            version = None

            if os.path.exists("/etc/os-release"):
                from .FileOperations import getFileContentByLine

                for line in getFileContentByLine("/etc/os-release"):
                    if line.startswith("ID="):
                        result = line[3:].strip('"')
                    if line.startswith("VERSION="):
                        version = line[8:].strip('"')

            if result is None:
                from .Execution import check_output

                try:
                    result = check_output(["lsb_release", "-i", "-s"], shell=False)

                    if str is not bytes:
                        result = result.decode("utf8")
                except FileNotFoundError:
                    pass

            if result is None:
                from nuitka.Tracing import general

                general.sysexit("Error, cannot detect Linux distribution.")

        # Change e.g. "11 (Bullseye)"" to "11".
        if version is not None and version.strip():
            version = version.split()[0]

        _linux_distribution_info = result.title(), version

    return _linux_distribution_info


def getWindowsRelease():
    if getOS() != "Windows":
        return None

    import platform

    return platform.release()


def isDebianBasedLinux():
    # TODO: What is with Mint, maybe others, this list should be expanded potentially.
    dist_name, _dist_version = getLinuxDistribution()

    return dist_name in ("Debian", "Ubuntu")


def isWin32Windows():
    """The Win32 variants of Python does have win32 only, not posix."""
    return os.name == "nt"


def isPosixWindows():
    """The MSYS2 variant of Python does have posix only, not Win32."""
    return os.name == "posix" and getOS() == "Windows"


def isLinux():
    """The Linux OS."""
    return getOS() == "Linux"


def isMacOS():
    """The macOS platform."""
    return getOS() == "Darwin"


def isNetBSD():
    """The NetBSD OS."""
    return getOS() == "NetBSD"


def isFreeBSD():
    """The FreeBSD OS."""
    return getOS() == "FreeBSD"


def isOpenBSD():
    """The FreeBSD OS."""
    return getOS() == "OpenBSD"


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

    if getOS() != "Windows":
        # Try to sum up the CPU cores, if the kernel shows them, getting the number
        # of logical processors
        try:
            # Encoding is not needed, pylint: disable=unspecified-encoding
            with open("/proc/cpuinfo") as cpuinfo_file:
                cpu_count = cpuinfo_file.read().count("processor\t:")
        except IOError:
            pass

    # Multiprocessing knows the way.
    if not cpu_count:
        import multiprocessing

        cpu_count = multiprocessing.cpu_count()

    return cpu_count


def encodeNonAscii(var_name):
    """Encode variable name that is potentially not ASCII to ASCII only.

    For Python3, unicode identifiers can be used, but these are not
    possible in C, so we need to replace them.
    """
    if str is bytes:
        return var_name
    else:
        # Using a escaping here, because that makes it safe in terms of not
        # to occur in the encoding escape sequence for unicode use.
        var_name = var_name.replace("$$", "$_$")

        var_name = var_name.encode("ascii", "xmlcharrefreplace")
        var_name = var_name.decode("ascii")

        return var_name.replace("&#", "$$").replace(";", "")


def hasOnefileSupportedOS():
    return getOS() in ("Linux", "Windows", "Darwin", "FreeBSD")


def hasStandaloneSupportedOS():
    return getOS() in ("Linux", "Windows", "Darwin", "FreeBSD", "OpenBSD")


def getUserName():
    """Return the user name.

    Notes: Currently doesn't work on Windows.
    """
    import pwd  # pylint: disable=I0021,import-error

    return pwd.getpwuid(os.getuid())[0]


@contextmanager
def withNoDeprecationWarning():
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # These do not inherit from DeprecationWarning by some decision we
        # are not to care about.
        if "pkg_resources" in sys.modules:
            try:
                from pkg_resources import PkgResourcesDeprecationWarning
            except ImportError:
                pass
            else:
                warnings.filterwarnings(
                    "ignore", category=PkgResourcesDeprecationWarning
                )

        yield
