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
""" Python version specifics.

This abstracts the Python version decisions. This makes decisions based on
the numbers, and attempts to give them meaningful names. Where possible it
should attempt to make run time detections.

"""

import os
import re
import sys


def getSupportedPythonVersions():
    return ("2.6", "2.7", "3.2", "3.3", "3.4", "3.5")


def getSupportedPythonVersionStr():
    supported_python_versions = getSupportedPythonVersions()

    supported_python_versions_str = repr(supported_python_versions)[1:-1]
    supported_python_versions_str = re.sub(
        r"(.*),(.*)$",
        r"\1, or\2",
        supported_python_versions_str
    )

    return supported_python_versions_str


def _getPythonVersion():
    big, major, minor = sys.version_info[0:3]

    return big * 100 + major * 10 + minor

python_version = _getPythonVersion()

python_version_full_str = '.'.join(str(s) for s in sys.version_info[0:3])
python_version_str = '.'.join(str(s) for s in sys.version_info[0:2])

def isAtLeastSubVersion(version):
    if version < 280 and \
       python_version >= 280 and \
       python_version < 300:
        return True

    if version // 10 != python_version // 10:
        return False

    return python_version >= version


def doShowUnknownEncodingName():
    # Python 3.3.3 or higher does it, 3.4 always did.
    if python_version >= 333:
        return True

    # Python2.7 after 2.7.6 does it.
    if isAtLeastSubVersion(276):
        return True

    # Debian back ports do it.
    if  "2.7.5+" in sys.version or "3.3.2+" in sys.version:
        return True

    return False


def getErrorMessageExecWithNestedFunction():
    """ Error message of the concrete Python in case an exec occurs in a
        function that takes a closure variable.
    """

    assert python_version < 300

    # Need to use "exec" to detect the syntax error, pylint: disable=W0122

    try:
        exec("""
def f():
   exec ""
   def nested():
      return closure""")
    except SyntaxError as e:
        return e.message.replace("'f'", "'%s'")


def getComplexCallSequenceErrorTemplate():
    if not hasattr(getComplexCallSequenceErrorTemplate, "result"):
        try:
            # We are doing this on purpose, to get the exception.
            # pylint: disable=E1133,E1102
            f = None
            f(*None)
        except TypeError as e:
            result = e.args[0].replace("NoneType object", "%s").replace("NoneType", "%s")
            getComplexCallSequenceErrorTemplate.result = result
        else:
            sys.exit("Error, cannot detect expected error message.")

    return getComplexCallSequenceErrorTemplate.result


def isUninstalledPython():
    return "Anaconda" in sys.version or \
           "WinPython" in sys.version or \
           (os.name == "nt" and python_version >= 350)


def getRunningPythonDLLPath():
    import ctypes.wintypes

    GetModuleHandle = ctypes.windll.kernel32.GetModuleHandleW  # @UndefinedVariable
    GetModuleHandle.argtypes = (
        ctypes.wintypes.LPWSTR,
    )
    GetModuleHandle.restype = ctypes.wintypes.DWORD

    big, major = sys.version_info[0:2]

    dll_module_name = "python%d%d" % (big, major)
    module_handle = GetModuleHandle(dll_module_name)

    if module_handle == 0:
        dll_module_name += "_d"
        module_handle = GetModuleHandle(dll_module_name)

    assert module_handle, (sys.executable, dll_module_name, sys.flags.debug)

    MAX_PATH = 4096
    buf = ctypes.create_unicode_buffer(MAX_PATH)

    GetModuleFileName = ctypes.windll.kernel32.GetModuleFileNameW  # @UndefinedVariable
    GetModuleFileName.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD
    )
    GetModuleFileName.restype = ctypes.wintypes.DWORD

    res = GetModuleFileName(module_handle, buf, MAX_PATH)
    assert res != 0

    dll_path = os.path.normcase(buf.value)
    assert os.path.exists(dll_path), dll_path

    return dll_path


def getTargetPythonDLLPath():
    dll_path = getRunningPythonDLLPath()

    from nuitka.Options import isPythonDebug

    if dll_path.endswith("_d.dll"):
        if not isPythonDebug():
            dll_path = dll_path[:-5] + ".dll"

        if not os.path.exists(dll_path):
            sys.exit("Error, cannot switch to non-debug Python, not installed.")

    else:
        if isPythonDebug():
            dll_path = dll_path[:-4] + "_d.dll"

        if not os.path.exists(dll_path):
            sys.exit("Error, cannot switch to debug Python, not installed.")

    return dll_path
