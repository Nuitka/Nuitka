#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
    return ("2.6", "2.7", "3.3", "3.4", "3.5", "3.6", "3.7")


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
    if version < 280 <= python_version < 300:
        return True

    if version // 10 != python_version // 10:
        return False

    return python_version >= version


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
            # pylint: disable=  not-an-iterable,not-callable
            f = None
            f(*None)
        except TypeError as e:
            result = e.args[0].replace("NoneType object", "%s").replace("NoneType", "%s")
            getComplexCallSequenceErrorTemplate.result = result
        else:
            sys.exit("Error, cannot detect expected error message.")

    return getComplexCallSequenceErrorTemplate.result


def needsSetLiteralReverseInsertion():
    try:
        value = eval("{1,1.0}.pop()") # pylint: disable=eval-used
    except SyntaxError:
        return False
    else:
        return type(value) is float


def needsDuplicateArgumentColOffset():
    if python_version < 353:
        return False
    else:
        return True


def isUninstalledPython():
    if os.name == "nt":
        import ctypes.wintypes

        GetSystemDirectory  = ctypes.windll.kernel32.GetSystemDirectoryW   # @UndefinedVariable
        GetSystemDirectory.argtypes = (
            ctypes.wintypes.LPWSTR,
            ctypes.wintypes.DWORD
        )
        GetSystemDirectory.restype = ctypes.wintypes.DWORD

        MAX_PATH = 4096
        buf = ctypes.create_unicode_buffer(MAX_PATH)

        res = GetSystemDirectory(buf, MAX_PATH)
        assert res != 0

        system_path = os.path.normcase(buf.value)
        return not getRunningPythonDLLPath().startswith(system_path)

    return "Anaconda" in sys.version or "WinPython" in sys.version


def getRunningPythonDLLPath():
    import ctypes.wintypes

    MAX_PATH = 4096
    buf = ctypes.create_unicode_buffer(MAX_PATH)

    GetModuleFileName = ctypes.windll.kernel32.GetModuleFileNameW  # @UndefinedVariable
    GetModuleFileName.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD
    )
    GetModuleFileName.restype = ctypes.wintypes.DWORD

    # We trust ctypes internals here, pylint: disable=protected-access
    res = GetModuleFileName(ctypes.pythonapi._handle, buf, MAX_PATH)
    if res == 0:
        # Windows only code, pylint: disable=I0021,undefined-variable
        raise WindowsError(ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError())) # @UndefinedVariable

    dll_path = os.path.normcase(buf.value)
    assert os.path.exists(dll_path), dll_path

    return dll_path


def getTargetPythonDLLPath():
    dll_path = getRunningPythonDLLPath()

    from nuitka.Options import isPythonDebug

    if dll_path.endswith("_d.dll"):
        if not isPythonDebug():
            dll_path = dll_path[:-6] + ".dll"

        if not os.path.exists(dll_path):
            sys.exit("Error, cannot switch to non-debug Python, not installed.")

    else:
        if isPythonDebug():
            dll_path = dll_path[:-4] + "_d.dll"

        if not os.path.exists(dll_path):
            sys.exit("Error, cannot switch to debug Python, not installed.")

    return dll_path


def isStaticallyLinkedPython():
    try:
        import sysconfig
    except ImportError:
        # Cannot detect this properly for Python 2.6, but we don't care much
        # about that anyway.
        return False

    result = sysconfig.get_config_var("Py_ENABLE_SHARED") == 0

    if result:
        from nuitka.utils.Execution import check_output

        with open(os.devnull, 'w') as devnull:
            output = check_output(
                (
                    os.path.realpath(sys.executable) + "-config",
                    "--ldflags"
                ),
                stderr = devnull
            )

        if str is not bytes:
            output = output.decode("utf8")

        import shlex
        output = shlex.split(output)

        python_abi_version = python_version_str + getPythonABI()

        result = ("-lpython" + python_abi_version) not in output

    return result


def getPythonABI():
    if hasattr(sys, "abiflags"):
        abiflags = sys.abiflags

        # Cyclic dependency here.
        from nuitka.Options import isPythonDebug
        if isPythonDebug() or hasattr(sys, "getobjects"):
            if not abiflags.startswith('d'):
                abiflags = 'd' + abiflags
    else:
        abiflags = ""

    return abiflags
