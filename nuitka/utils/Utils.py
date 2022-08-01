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
""" Utility module.

Here the small things that fit nowhere else and don't deserve their own module.

"""

import functools
import os
import sys
import time
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


def _parseOsReleaseFileContents(filename):
    result = None
    base = None
    version = None

    from .FileOperations import getFileContentByLine

    for line in getFileContentByLine(filename):
        if line.startswith("PRETTY_NAME=") and "/sid" in line:
            version = "sid"

        if line.startswith("ID="):
            result = line[3:].strip('"')

        if line.startswith("ID_LIKE="):
            base = line[8:].strip('"').lower()

            if "ubuntu" in base:
                base = "Ubuntu"
            elif "debian" in base:
                base = "Debian"
            elif "fedora" in base:
                base = "Fedora"

        if line.startswith("VERSION="):
            version = line[8:].strip('"')

        if "SUSE Linux Enterprise Server" in line:
            result = "SLES"  # spell-checker: ignore SLES

    return result, base, version


def getLinuxDistribution():
    """Name of the Linux distribution.

    We should usually avoid this, and rather test for the feature,
    but in some cases it's hard to manage that.
    """
    if getOS() != "Linux":
        return None, None, None

    # singleton, pylint: disable=global-statement
    global _linux_distribution_info

    if _linux_distribution_info is None:
        result = None
        base = None
        version = None

        if os.path.exists("/etc/os-release"):
            result, base, version = _parseOsReleaseFileContents("/etc/os-release")
        elif os.path.exists("/etc/SuSE-release"):
            result, base, version = _parseOsReleaseFileContents("/etc/SuSE-release")
        elif os.path.exists("/etc/issue"):
            result, base, version = _parseOsReleaseFileContents("/etc/issue")

        if result is None:
            from .Execution import check_output

            try:
                result = check_output(["lsb_release", "-i", "-s"], shell=False)

                if str is not bytes:
                    result = result.decode("utf8")
            except OSError:
                pass

        if result is None:
            from nuitka.Tracing import general

            general.warning(
                "Cannot detect Linux distribution, this may prevent optimization."
            )
            result = "Unknown"

        # Change e.g. "11 (Bullseye)"" to "11".
        if version is not None and version.strip():
            version = version.split()[0]

        _linux_distribution_info = result.title(), base, version

    return _linux_distribution_info


def getWindowsRelease():
    if not isWin32OrPosixWindows():
        return None

    import platform

    return platform.release()


def isDebianBasedLinux():
    dist_name, base, _dist_version = getLinuxDistribution()

    # False alarm, pylint: disable=superfluous-parens
    return (base or dist_name) in ("Debian", "Ubuntu")


def isFedoraBasedLinux():
    dist_name, base, _dist_version = getLinuxDistribution()

    return (base or dist_name) == "Fedora"


def isWin32Windows():
    """The Win32 variants of Python does have win32 only, not posix."""
    return os.name == "nt"


def isPosixWindows():
    """The MSYS2 variant of Python does have posix only, not Win32."""
    return os.name == "posix" and getOS() == "Windows"


def isWin32OrPosixWindows():
    return isWin32Windows() or isPosixWindows()


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


def getCPUCoreCount():
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

    # spell-checker: ignore getpwuid,getuid

    return pwd.getpwuid(os.getuid())[0]


@contextmanager
def withWarningRemoved(category):
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=category)

        # These do not inherit from DeprecationWarning by some decision we
        # are not to care about.
        if "pkg_resources" in sys.modules and category is DeprecationWarning:
            try:
                from pkg_resources import PkgResourcesDeprecationWarning
            except ImportError:
                pass
            else:
                warnings.filterwarnings(
                    "ignore", category=PkgResourcesDeprecationWarning
                )

        yield


@contextmanager
def withNoDeprecationWarning():
    with withWarningRemoved(DeprecationWarning):
        yield


@contextmanager
def withNoSyntaxWarning():
    with withWarningRemoved(SyntaxWarning):
        yield


def decoratorRetries(
    logger, purpose, consequence, attempts=5, sleep_time=1, exception_type=OSError
):
    """Make retries for errors on Windows.

    This executes a decorated function multiple times, and imposes a delay and
    a virus checker warning.
    """

    def inner(func):
        if os.name != "nt":
            return func

        @functools.wraps(func)
        def retryingFunction(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    result = func(*args, **kwargs)
                except exception_type as e:
                    if not isinstance(e, OSError):
                        logger.warning(
                            """\
Failed to %s in attempt %d due to %s.
Disable Anti-Virus, e.g. Windows Defender for build folders. Retrying after a second of delay."""
                            % (purpose, attempt, str(e))
                        )

                    else:
                        if isinstance(e, OSError) and e.errno in (110, 13):
                            logger.warning(
                                """\
Failed to %s in attempt %d.
Disable Anti-Virus, e.g. Windows Defender for build folders. Retrying after a second of delay."""
                                % (purpose, attempt)
                            )
                        else:
                            logger.warning(
                                """\
Failed to %s in attempt %d with error code %d.
Disable Anti-Virus, e.g. Windows Defender for build folders. Retrying after a second of delay."""
                                % (purpose, attempt, e.errno)
                            )

                    time.sleep(sleep_time)
                    continue

                else:
                    if attempt != 1:
                        logger.warning(
                            "Succeeded with %s in attempt %d." % (purpose, attempt)
                        )

                    return result

            logger.sysexit("Failed to %s, %s." % (purpose, consequence))

        return retryingFunction

    return inner
