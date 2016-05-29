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
""" Tools for tracing memory usage at compiled time.

"""

from .Utils import getOS


def getOwnProcessMemoryUsage():
    """ Memory usage of own process in bytes.

    """

    if getOS() == "Windows":
        # adapted from http://code.activestate.com/recipes/578513
        import ctypes
        import ctypes.wintypes

        # Lets allow this to match Windows API it reflects,
        # pylint: disable=C0103
        class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.wintypes.DWORD),
                ("PageFaultCount", ctypes.wintypes.DWORD),
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
            ctypes.wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
            ctypes.wintypes.DWORD,
        ]
        GetProcessMemoryInfo.restype = ctypes.wintypes.BOOL

        counters = PROCESS_MEMORY_COUNTERS_EX()
        rv = GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(),  # @UndefinedVariable
            ctypes.byref(counters),
            ctypes.sizeof(counters)
        )

        if not rv:
            raise ctypes.WinError()

        return counters.PrivateUsage
    else:
        # Posix only code, pylint: disable=F0401,I0021
        import resource  # @UnresolvedImport

        # The value is from "getrusage", which has OS dependent scaling, at least
        # MacOS and Linux are different. Others maybe too.
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
