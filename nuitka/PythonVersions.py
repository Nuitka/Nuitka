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
""" Python version specifics.

This abstracts the Python version decisions. This makes decisions based on
the numbers, and attempts to give them meaningful names. Where possible it
should attempt to make run time detections.

"""

import __future__

import os
import re
import sys

from nuitka.__past__ import WindowsError  # pylint: disable=I0021,redefined-builtin


def getSupportedPythonVersions():
    """Officially supported Python versions for Nuitka."""

    return ("2.6", "2.7", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "3.10")


def getPartiallySupportedPythonVersions():
    """Partially supported Python versions for Nuitka."""

    return ()


def getSupportedPythonVersionStr():
    supported_python_versions = getSupportedPythonVersions()

    supported_python_versions_str = repr(supported_python_versions)[1:-1]
    supported_python_versions_str = re.sub(
        r"(.*),(.*)$", r"\1, or\2", supported_python_versions_str
    )

    return supported_python_versions_str


def _getPythonVersion():
    big, major, minor = sys.version_info[0:3]

    return big * 256 + major * 16 + min(15, minor)


python_version = _getPythonVersion()

python_version_full_str = ".".join(str(s) for s in sys.version_info[0:3])
python_version_str = ".".join(str(s) for s in sys.version_info[0:2])


def getErrorMessageExecWithNestedFunction():
    """Error message of the concrete Python in case an exec occurs in a
    function that takes a closure variable.
    """

    assert python_version < 0x300

    # Need to use "exec" to detect the syntax error, pylint: disable=W0122

    try:
        exec(
            """
def f():
   exec ""
   def nested():
      return closure"""
        )
    except SyntaxError as e:
        return e.message.replace("'f'", "'%s'")


def getComplexCallSequenceErrorTemplate():
    if not hasattr(getComplexCallSequenceErrorTemplate, "result"):
        try:
            # We are doing this on purpose, to get the exception.
            # pylint: disable=not-an-iterable,not-callable
            f = None
            f(*None)
        except TypeError as e:
            result = (
                e.args[0]
                .replace("NoneType object", "%s")
                .replace("NoneType", "%s")
                .replace("None ", "%s ")
            )
            getComplexCallSequenceErrorTemplate.result = result
        else:
            sys.exit("Error, cannot detect expected error message.")

    return getComplexCallSequenceErrorTemplate.result


_needs_set_literal_reverse_insertion = None


def needsSetLiteralReverseInsertion():
    """For Python3, until Python3.5 ca. the order of set literals was reversed."""
    # Cached result, pylint: disable=global-statement
    global _needs_set_literal_reverse_insertion

    if _needs_set_literal_reverse_insertion is None:
        try:
            value = eval("{1,1.0}.pop()")  # pylint: disable=eval-used
        except SyntaxError:
            _needs_set_literal_reverse_insertion = False
        else:
            _needs_set_literal_reverse_insertion = type(value) is float

    return _needs_set_literal_reverse_insertion


def needsDuplicateArgumentColOffset():
    if python_version < 0x353:
        return False
    else:
        return True


def getRunningPythonDLLPath():
    import ctypes.wintypes

    MAX_PATH = 4096
    buf = ctypes.create_unicode_buffer(MAX_PATH)

    GetModuleFileName = ctypes.windll.kernel32.GetModuleFileNameW
    GetModuleFileName.argtypes = (
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD,
    )
    GetModuleFileName.restype = ctypes.wintypes.DWORD

    # We trust ctypes internals here, pylint: disable=protected-access
    res = GetModuleFileName(ctypes.pythonapi._handle, buf, MAX_PATH)
    if res == 0:
        # Windows only code, pylint: disable=I0021,undefined-variable
        raise WindowsError(
            ctypes.GetLastError(), ctypes.FormatError(ctypes.GetLastError())
        )

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
    # On Windows, there is no way to detect this from syconfig.
    if os.name == "nt":
        import ctypes

        return ctypes.pythonapi is None

    try:
        import sysconfig
    except ImportError:
        # Cannot detect this properly for Python 2.6, but we don't care much
        # about that anyway.
        return False

    result = sysconfig.get_config_var("Py_ENABLE_SHARED") == 0

    return result


def getPythonABI():
    if hasattr(sys, "abiflags"):
        abiflags = sys.abiflags

        # Cyclic dependency here.
        from nuitka.Options import isPythonDebug

        if isPythonDebug() or hasattr(sys, "getobjects"):
            if not abiflags.startswith("d"):
                abiflags = "d" + abiflags
    else:
        abiflags = ""

    return abiflags


_the_sys_prefix = None


def getSystemPrefixPath():
    """Return real sys.prefix as an absolute path breaking out of virtualenv.

    Note:

        For Nuitka, it often is OK to break out of the virtualenv, and use the
        original install. Mind you, this is not about executing anything, this is
        about building, and finding the headers to compile against that Python, we
        do not care about any site packages, and so on.

    Returns:
        str - path to system prefix
    """

    global _the_sys_prefix  # Cached result, pylint: disable=global-statement
    if _the_sys_prefix is None:

        sys_prefix = getattr(
            sys, "real_prefix", getattr(sys, "base_prefix", sys.prefix)
        )
        sys_prefix = os.path.abspath(sys_prefix)

        # Some virtualenv contain the "orig-prefix.txt" as a textual link to the
        # target, this is often on Windows with virtualenv. There are two places to
        # look for.
        for candidate in (
            "Lib/orig-prefix.txt",
            "lib/python%s/orig-prefix.txt" % python_version_str,
        ):
            candidate = os.path.join(sys_prefix, candidate)
            if os.path.exists(candidate):
                # Cannot use FileOperations.getFileContents() here, because of circular dependency.
                # pylint: disable=unspecified-encoding
                with open(candidate) as f:
                    sys_prefix = f.read()

                # Trailing spaces in the python prefix, please not.
                assert sys_prefix == sys_prefix.strip()

        # This is another for of virtualenv references:
        if os.name != "nt" and os.path.islink(os.path.join(sys_prefix, ".Python")):
            sys_prefix = os.path.normpath(
                os.path.join(os.readlink(os.path.join(sys_prefix, ".Python")), "..")
            )

        # Some virtualenv created by "venv" seem to have a different structure, where
        # library and include files are outside of it.
        if (
            os.name != "nt"
            and python_version >= 0x330
            and os.path.exists(os.path.join(sys_prefix, "bin/activate"))
        ):
            python_binary = os.path.join(sys_prefix, "bin", "python")
            python_binary = os.path.realpath(python_binary)

            sys_prefix = os.path.normpath(os.path.join(python_binary, "..", ".."))

        _the_sys_prefix = sys_prefix

    return _the_sys_prefix


def getFutureModuleKeys():
    result = [
        "unicode_literals",
        "absolute_import",
        "division",
        "print_function",
        "generator_stop",
        "nested_scopes",
        "generators",
        "with_statement",
    ]

    if hasattr(__future__, "barry_as_FLUFL"):
        result.append("barry_as_FLUFL")
    if hasattr(__future__, "annotations"):
        result.append("annotations")

    return result


def getImportlibSubPackages():
    result = []
    if python_version >= 0x270:
        import importlib
        import pkgutil

        for module_info in pkgutil.walk_packages(importlib.__path__):
            result.append(module_info[1])

    return result
