#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" This module deals with finding and information about static libraries.

"""

import os

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonFlavors import (
    isAnacondaPython,
    isDebianPackagePython,
    isNuitkaPython,
)
from nuitka.PythonVersions import (
    getPythonABI,
    getSystemPrefixPath,
    python_version,
    python_version_str,
)
from nuitka.Tracing import general

from .FileOperations import getFileContentByLine, getFileList
from .Utils import getLinuxDistribution, isDebianBasedLinux, isWin32Windows

_ldconf_paths = None

_static_lib_cache = {}


def locateStaticLinkLibrary(dll_name):
    if dll_name not in _static_lib_cache:
        _static_lib_cache[dll_name] = _locateStaticLinkLibrary(dll_name)

    return _static_lib_cache[dll_name]


def _locateStaticLinkLibrary(dll_name):
    # singleton, pylint: disable=global-statement
    #
    global _ldconf_paths

    if _ldconf_paths is None:
        _ldconf_paths = OrderedSet()

        for conf_filemame in getFileList("/etc/ld.so.conf.d", only_suffixes=".conf"):
            for conf_line in getFileContentByLine(conf_filemame):
                conf_line = conf_line.split("#", 1)[0]
                conf_line = conf_line.strip()

                if os.path.exists(conf_line):
                    _ldconf_paths.add(conf_line)

    for ld_config_path in _ldconf_paths:
        candidate = os.path.join(ld_config_path, "lib%s.a" % dll_name)

        if os.path.exists(candidate):
            return candidate

    return None


_static_lib_python_path = False


def isDebianSuitableForStaticLinking():
    dist_name, _base, dist_version = getLinuxDistribution()

    if dist_name == "Debian":
        if dist_version is None:
            return True

        try:
            dist_version = tuple(int(x) for x in dist_version.split("."))
        except ValueError:
            # dist_version contains a non-numeric string such as "sid".
            return True

        return dist_version >= (10,)
    else:
        # TODO: Needs implementing potentially, Mint etc. are based
        # on something that should be considered.
        return True


def _getSystemStaticLibPythonPath():
    # Return driven function with many cases, pylint: disable=too-many-branches,too-many-return-statements

    sys_prefix = getSystemPrefixPath()
    python_abi_version = python_version_str + getPythonABI()

    if isNuitkaPython():
        # Nuitka Python has this.
        if isWin32Windows():
            return os.path.join(
                sys_prefix,
                "libs",
                "python" + python_abi_version.replace(".", "") + ".lib",
            )
        else:
            return os.path.join(
                sys_prefix,
                "lib",
                "libpython" + python_abi_version + ".a",
            )

    if isWin32Windows():
        # The gcc used on Windows for Anaconda is far too old for winlibs gcc
        # to use its library.
        if isAnacondaPython():
            return None

        candidates = [
            # Anaconda has this.
            os.path.join(
                sys_prefix,
                "libs",
                "libpython" + python_abi_version.replace(".", "") + ".dll.a",
            ),
            # MSYS2 mingw64 Python has this.
            os.path.join(
                sys_prefix,
                "lib",
                "libpython" + python_abi_version + ".dll.a",
            ),
        ]

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
    else:
        candidate = os.path.join(
            sys_prefix, "lib", "libpython" + python_abi_version + ".a"
        )

        if os.path.exists(candidate):
            return candidate

        # For Python2 this works. TODO: Figure out Debian and Python3.
        if (
            python_version < 0x300
            and isDebianPackagePython()
            and isDebianSuitableForStaticLinking()
        ):
            candidate = locateStaticLinkLibrary("python" + python_abi_version)
        else:
            candidate = None

        if candidate is not None and os.path.exists(candidate):
            # Also check libz, can be missing
            if not locateStaticLinkLibrary("z"):
                general.warning(
                    "Error, missing 'libz-dev' installation needed for static lib-python."
                )

            return candidate

        # This is not necessarily only for Python3 on Debian, but maybe others as well,
        # but that's what's been tested.
        if python_version >= 0x300 and isDebianPackagePython() and isDebianBasedLinux():
            try:
                import sysconfig

                candidate = os.path.join(
                    sysconfig.get_config_var("LIBPL"),
                    "libpython" + python_abi_version + "-pic.a",
                )

                if os.path.exists(candidate):
                    return candidate

            except ImportError:
                # Cannot detect this properly for Python 2.6, but we don't care much
                # about that anyway.
                pass

    return None


def getSystemStaticLibPythonPath():
    global _static_lib_python_path  # singleton, pylint: disable=global-statement

    if _static_lib_python_path is False:
        _static_lib_python_path = _getSystemStaticLibPythonPath()

    return _static_lib_python_path
