#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Python version specifics.

This abstracts the Python version decisions. This makes decisions based on
the numbers, and attempts to give them meaningful names. Where possible it
should attempt to make run time detections.

"""

import __future__

import ctypes
import os
import re
import sys


def getSupportedPythonVersions():
    """Officially supported Python versions for Nuitka."""

    return (
        "2.6",
        "2.7",
        "3.4",
        "3.5",
        "3.6",
        "3.7",
        "3.8",
        "3.9",
        "3.10",
        "3.11",
        "3.12",
        "3.13",
    )


def getNotYetSupportedPythonVersions():
    """Versions known to not work at all (yet)."""
    return ("3.14",)


def getPartiallySupportedPythonVersions():
    """Partially supported Python versions for Nuitka."""

    return ()


def getZstandardSupportingVersions():
    result = getSupportedPythonVersions() + getPartiallySupportedPythonVersions()

    # This will crash if we remove versions, but it is more likely to work
    # with newly supported versions, and to list the ones not supported by
    # zstandard.
    result = tuple(
        version for version in result if version not in ("2.6", "2.7", "3.3", "3.4")
    )

    return result


def getTestExecutionPythonVersions():
    return (
        getSupportedPythonVersions()
        + getPartiallySupportedPythonVersions()
        + getNotYetSupportedPythonVersions()
    )


# Make somewhat sure we keep these ones consistent
assert len(
    set(
        getPartiallySupportedPythonVersions()
        + getNotYetSupportedPythonVersions()
        + getSupportedPythonVersions()
    )
) == len(
    getPartiallySupportedPythonVersions()
    + getNotYetSupportedPythonVersions()
    + getSupportedPythonVersions()
)


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

python_release_level = sys.version_info[3]


# TODO: Move error construction helpers to separate node making helpers module.
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


def getUnboundLocalErrorErrorTemplate():
    if not hasattr(getUnboundLocalErrorErrorTemplate, "result"):
        try:
            # We are doing this on purpose, to get the exception.
            # pylint: disable=undefined-variable
            del _f
        except UnboundLocalError as e:
            result = e.args[0].replace("_f", "%s")
            getUnboundLocalErrorErrorTemplate.result = result
        else:
            sys.exit("Error, cannot detect expected error message.")

    return getUnboundLocalErrorErrorTemplate.result


def getDictFromkeysNoArgErrorMessage():
    try:
        dict.fromkeys()
    except TypeError as e:
        return e.args[0]


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


def getRunningPythonDllHandle():
    # We trust ctypes internals here, pylint: disable=protected-access
    # spell-checker: ignore pythonapi
    return ctypes.pythonapi._handle


def getRunningPythonDLLPath():
    from nuitka.utils.SharedLibraries import (
        getWindowsRunningProcessModuleFilename,
    )

    return getWindowsRunningProcessModuleFilename(getRunningPythonDllHandle())


def getTargetPythonDLLPath():
    dll_path = getRunningPythonDLLPath()

    from nuitka.Options import shallUsePythonDebug

    if dll_path.endswith("_d.dll"):
        if not shallUsePythonDebug():
            dll_path = dll_path[:-6] + ".dll"

        if not os.path.exists(dll_path):
            sys.exit("Error, cannot switch to non-debug Python, not installed.")

    else:
        if shallUsePythonDebug():
            dll_path = dll_path[:-4] + "_d.dll"

        if not os.path.exists(dll_path):
            sys.exit("Error, cannot switch to debug Python, not installed.")

    return dll_path


def isStaticallyLinkedPython():
    # On Windows, there is no way to detect this from sysconfig.
    if os.name == "nt":
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
        from nuitka.Options import shallUsePythonDebug

        # spell-checker: ignore getobjects
        if shallUsePythonDebug() or hasattr(sys, "getobjects"):
            if not abiflags.startswith("d"):
                abiflags = "d" + abiflags
    else:
        abiflags = ""

    return abiflags


def getLaunchingSystemPrefixPath():
    from nuitka.utils.Utils import getLaunchingNuitkaProcessEnvironmentValue

    return getLaunchingNuitkaProcessEnvironmentValue("NUITKA_SYS_PREFIX")


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

        # Resolve symlinks on Windows manually.
        if os.name == "nt":
            from nuitka.utils.FileOperations import getDirectoryRealPath

            sys_prefix = getDirectoryRealPath(sys_prefix)

        # Self-compiled Python version in source tree
        if os.path.isdir(
            os.path.join(os.path.dirname(os.path.realpath(sys.executable)), "PCbuild")
        ):
            sys_prefix = os.path.dirname(os.path.realpath(sys.executable))

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


def isDebugPython():
    """Is this a debug build of Python."""
    return hasattr(sys, "gettotalrefcount")


def _getFloatDigitBoundaryValue():
    if python_version < 0x270:
        bits_per_digit = 15
    elif python_version < 0x300:
        bits_per_digit = sys.long_info.bits_per_digit
    else:
        bits_per_digit = sys.int_info.bits_per_digit

    return (2**bits_per_digit) - 1


_float_digit_boundary = _getFloatDigitBoundaryValue()


def isPythonValidDigitValue(value):
    """Does the given value fit into a float digit.

    Note: Digits in long objects do not use 2-complement, but a boolean sign.
    """

    return -_float_digit_boundary <= value <= _float_digit_boundary


sizeof_clong = ctypes.sizeof(ctypes.c_long)

# TODO: We could be more aggressive here, there are issues with using full
# values, in some contexts, but that can probably be sorted out.
_max_signed_long = 2 ** (sizeof_clong * 7) - 1
_min_signed_long = -(2 ** (sizeof_clong * 7))

# Used by data composer to write Python long values.
sizeof_clonglong = ctypes.sizeof(ctypes.c_longlong)

_max_signed_longlong = 2 ** (sizeof_clonglong * 8 - 1) - 1
_min_signed_longlong = -(2 ** (sizeof_clonglong * 8 - 1))


def isPythonValidCLongValue(value):
    return _min_signed_long <= value <= _max_signed_long


def isPythonValidCLongLongValue(value):
    return _min_signed_longlong <= value <= _max_signed_longlong


def getInstalledPythonRegistryPaths(version):
    """Yield all Pythons as found in the Windows registry."""
    # Windows only code,
    # pylint: disable=I0021,import-error,redefined-builtin
    from nuitka.__past__ import WindowsError

    if str is bytes:
        import _winreg as winreg  # pylint: disable=I0021,import-error,no-name-in-module
    else:
        import winreg  # pylint: disable=I0021,import-error,no-name-in-module

    for hkey_branch in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for arch_key in (0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            for suffix in "", "-32", "-arm64":
                try:
                    key = winreg.OpenKey(
                        hkey_branch,
                        r"SOFTWARE\Python\PythonCore\%s%s\InstallPath"
                        % (version, suffix),
                        0,
                        winreg.KEY_READ | arch_key,
                    )

                    install_dir = os.path.normpath(winreg.QueryValue(key, ""))
                except WindowsError:
                    pass
                else:
                    candidate = os.path.normpath(
                        os.path.join(install_dir, "python.exe")
                    )

                    if os.path.exists(candidate):
                        yield candidate


def getTkInterVersion():
    """Get the tk-inter version or None if not installed."""
    try:
        if str is bytes:
            return str(__import__("TkInter").TkVersion)
        else:
            return str(__import__("tkinter").TkVersion)
    except ImportError:
        # This should lead to no action taken ideally.
        return None


def getModuleLinkerLibs():
    """Get static link libraries needed."""
    try:
        import sysconfig
    except ImportError:
        return []
    else:
        # static link libraries might be there, spell-checker: ignore modlibs
        result = sysconfig.get_config_var("MODLIBS") or ""
        result = [entry[2:] for entry in result.split() if entry.startswith("-l:")]

        return result


def isPythonWithGil():
    return python_version < 0x3D0 or sys.flags.gil


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
