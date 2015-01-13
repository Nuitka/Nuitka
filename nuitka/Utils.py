#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

Here the small things for file/dir names, Python version, CPU counting,
memory usage, etc. that fit nowhere else and don't deserve their own names.

"""

import os
import subprocess
import sys

from nuitka.PythonVersions import python_version


def getOS():
    if os.name == "nt":
        return "Windows"
    elif os.name == "posix":
        return os.uname()[0]
    else:
        assert False, os.name


def getArchitecture():
    if getOS() == "Windows":
        if "AMD64" in sys.version:
            return "x86_64"
        else:
            return "x86"
    else:
        return os.uname()[4]


def relpath(path):
    try:
        return os.path.relpath(path)
    except ValueError:
        # On Windows, paths on different devices prevent it to work. Use that
        # full path then.
        if getOS() == "Windows":
            return os.path.abspath(path)
        raise


def abspath(path):
    return os.path.abspath(path)


def joinpath(*parts):
    return os.path.join(*parts)


def splitpath(path):
    return tuple(
        element
        for element in
        os.path.split(path)
        if element
    )


def basename(path):
    return os.path.basename(path)


def dirname(path):
    return os.path.dirname(path)


def normpath(path):
    return os.path.normpath(path)


def normcase(path):
    return os.path.normcase(path)


def getExtension(path):
    return os.path.splitext(path)[1]


def isFile(path):
    return os.path.isfile(path)


def isDir(path):
    return os.path.isdir(path)


def isLink(path):
    return os.path.islink(path)


def readLink(path):
    return os.readlink(path)


def listDir(path):
    """ Give a sorted path, basename pairs of a directory."""

    return sorted(
        [
            (
                joinpath(path, filename),
                filename
            )
            for filename in
            os.listdir(path)
        ]
    )


def deleteFile(path, must_exist):
    if must_exist or isFile(path):
        os.unlink(path)


def makePath(path):
    os.makedirs(path)


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


def callExec(args):
    """ Do exec in a portable way preserving exit code.

        On Windows, unfortunately there is no real exec, so we have to spawn
        a new process instead.
    """

    # On Windows os.execl does not work properly
    if getOS() != "Windows":
        # The star arguments is the API of execl, pylint: disable=W0142
        os.execl(*args)
    else:
        args = list(args)
        del args[1]

        try:
            sys.exit(
                subprocess.call(args)
            )
        except KeyboardInterrupt:
            # There was a more relevant stack trace already, so abort this
            # right here, pylint: disable=W0212
            os._exit(2)


def encodeNonAscii(var_name):
    """ Encode variable name that is potentially not ASCII to ASCII only.

        For Python3, unicode identifiers can be used, but these are not
        possible in C++03, so we need to replace them.
    """
    if python_version < 300:
        return var_name
    else:
        # Using a escaping here, because that makes it safe in terms of not
        # to occur in the encoding escape sequence for unicode use.
        var_name = var_name.replace("$$", "$_$")

        var_name = var_name.encode("ascii", "xmlcharrefreplace")
        var_name = var_name.decode("ascii")

        return var_name.replace("&#", "$$").replace(';', "")


def isExecutableCommand(command):
    path = os.environ["PATH"]

    suffixes = (".exe",) if getOS() == "Windows" else ("",)
    path_sep = ';' if getOS() == "Windows" else ':'

    for part in path.split(path_sep):
        if not part:
            continue

        for suffix in suffixes:
            if isFile(joinpath(part, command + suffix)):
                return True

    return False


def getOwnProcessMemoryUsage():
    """ Memory usage of own process in bytes.

    """

    if getOS() == "Windows":
        # adapted from http://code.activestate.com/recipes/578513
        import ctypes
        from ctypes import wintypes

        # Lets allow this to match Windows API it reflects,
        # pylint: disable=C0103
        class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]

        GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
        GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
            wintypes.DWORD,
        ]
        GetProcessMemoryInfo.restype = wintypes.BOOL

        counters = PROCESS_MEMORY_COUNTERS_EX()
        rv = GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(),
            ctypes.byref(counters),
            ctypes.sizeof(counters)
        )

        if not rv:
            raise ctypes.WinError()

        return counters.PrivateUsage
    else:
        # Posix only code, pylint: disable=F0401,I0021
        import resource

        # The value is from "getrusage", which has OS dependent scaling, at least
        # MacOS and Linux different
        if getOS() == "Darwin":
            factor = 1
        else:
            factor = 1024

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * factor


def getHumanReadableProcessMemoryUsage(value = None):
    if value is None:
        value = getOwnProcessMemoryUsage()

    if abs(value) < 1024*1014:
        return "%.2f KB (%d bytes)" % (
            value / 1024.0,
            value
        )
    elif abs(value) < 1024*1014*1024:
        return "%.2f MB (%d bytes)" % (
            value / (1024*1024.0),
            value
        )
    elif abs(value) < 1024*1014*1024*1024:
        return "%.2f GB (%d bytes)" % (
            value / (1024*1024*1024.0),
            value
        )
    else:
        return "%d bytes" % value


class MemoryWatch:
    def __init__(self):
        self.start = getOwnProcessMemoryUsage()
        self.stop = None

    def finish(self):
        self.stop = getOwnProcessMemoryUsage()

    def asStr(self):
        return getHumanReadableProcessMemoryUsage(self.stop - self.start)
