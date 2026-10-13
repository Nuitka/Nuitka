#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Python installation prefix specifics.

This abstracts the Python installation layout, e.g. breaking out of virtual
environments, and finding the system prefix, executable, and include path to
use for building against that Python.

Note: This is separate from "PythonVersions", which is about version behavior
only, and from "PythonFlavors", which is about the different flavors of Python,
while this is about the layout of their installations.

"""

import os
import sys

from nuitka.PythonVersions import (
    getPythonABI,
    python_version,
    python_version_str,
)
from nuitka.utils.FileOperations import (
    areSamePaths,
    getDirectoryRealPath,
    getFileContents,
    getFilenameRealPath,
    getLinkTarget,
    getNormalizedPathJoin,
)
from nuitka.utils.Utils import (
    getLaunchingNuitkaProcessEnvironmentValue,
    isWin32Windows,
)

_target_python_include_path = {}

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
            candidate = getNormalizedPathJoin(sys_prefix, candidate)
            if os.path.exists(candidate):
                sys_prefix = getFileContents(candidate)

                # Trailing spaces in the python prefix, please not.
                assert sys_prefix == sys_prefix.strip()

        # This is another for of virtualenv references:
        if not isWin32Windows():
            is_link, link_target = getLinkTarget(
                getNormalizedPathJoin(sys_prefix, ".Python")
            )

            if is_link:
                sys_prefix = getNormalizedPathJoin(link_target, "..")

        # Some virtualenv created by "venv" seem to have a different structure, where
        # library and include files are outside of it.
        if (
            not isWin32Windows()
            and python_version >= 0x330
            and os.path.exists(getNormalizedPathJoin(sys_prefix, "bin", "activate"))
        ):
            python_binary = getNormalizedPathJoin(sys_prefix, "bin", "python")
            python_binary = getFilenameRealPath(python_binary)

            sys_prefix = getNormalizedPathJoin(python_binary, "..", "..")

        # Resolve symlinks on Windows manually.
        if isWin32Windows():
            sys_prefix = getDirectoryRealPath(sys_prefix)

        # Self-compiled Python version in source tree
        real_executable = getFilenameRealPath(sys.executable)

        if os.path.isdir(getNormalizedPathJoin(real_executable, "..", "PCbuild")):
            sys_prefix = getNormalizedPathJoin(real_executable, "..")

        _the_sys_prefix = sys_prefix

    return _the_sys_prefix


def getSystemPrefixExecutable():
    """Return the sys.executable of the system prefix, i.e. breaking out of virtualenv.

    See getSystemPrefixPath() for details.

    Returns:
        str - path to system executable
    """
    # Yes, we want and need it here, pylint: disable=protected-access
    if hasattr(sys, "_base_executable"):
        return sys._base_executable

    sys_prefix = getSystemPrefixPath()
    if sys_prefix == sys.prefix:
        return sys.executable

    if areSamePaths(sys_prefix, sys.prefix):
        return sys.executable

    # The "sys.executable" is a good guess for the name, but we might have to
    # look for "python" effectively.
    candidate_names = (
        os.path.basename(sys.executable),
        "python.exe" if isWin32Windows() else "python",
        "python%s" % python_version_str,
    )

    for candidate_name in candidate_names:
        if isWin32Windows():
            candidate = getNormalizedPathJoin(sys_prefix, candidate_name)
        else:
            candidate = getNormalizedPathJoin(sys_prefix, "bin", candidate_name)

        if os.path.exists(candidate):
            return candidate

    # Fallback to sys.executable, which is not correct if we are in a virtualenv
    # but the best we can do if we didn't find the system prefix one.
    return sys.executable


def getLaunchingSystemPrefixPath():
    return getLaunchingNuitkaProcessEnvironmentValue("NUITKA_SYS_PREFIX")


def getTargetPythonIncludePath(
    logger,
    python_debug,
    self_compiled_python_uninstalled,
):
    python_abi_version = python_version_str + getPythonABI(python_debug=python_debug)
    python_prefix_external = getSystemPrefixPath()

    key = (
        python_debug,
        self_compiled_python_uninstalled,
        python_abi_version,
        python_prefix_external,
    )

    if key not in _target_python_include_path:
        _target_python_include_path[key] = _getTargetPythonIncludePath(
            logger=logger,
            python_debug=python_debug,
            python_abi_version=python_abi_version,
            python_prefix_external=python_prefix_external,
            self_compiled_python_uninstalled=self_compiled_python_uninstalled,
        )

    return _target_python_include_path[key]


def _getTargetPythonIncludePath(
    logger,
    python_debug,
    python_abi_version,
    python_prefix_external,
    self_compiled_python_uninstalled,
):

    if isWin32Windows():
        candidates = [
            # On Windows, the CPython official installation layout is relatively fixed,
            getNormalizedPathJoin(python_prefix_external, "include"),
            # On MSYS2 with MinGW64 Python, it is also the other form.
            getNormalizedPathJoin(
                python_prefix_external, "include", "python" + python_abi_version
            ),
            # For Anaconda and conda-forge Python, since Python 3.15.
            getNormalizedPathJoin(python_prefix_external, "include", "python"),
            # For self-built Python on Windows, need to also add the "PC" directory,
            # that a normal install won't have.
            getNormalizedPathJoin(python_prefix_external, "PC"),
        ]
    else:
        # The python header path is a combination of python version and debug
        # indication, we make sure the headers are found by adding it to the C
        # include path.

        candidates = [
            getNormalizedPathJoin(
                python_prefix_external, "include", "python" + python_abi_version
            ),
            # CPython source code checkout
            getNormalizedPathJoin(python_prefix_external, "Include"),
            # Haiku specific paths:
            getNormalizedPathJoin(
                python_prefix_external,
                "develop/headers",
                "python" + python_abi_version,
            ),
        ]

        # Not all Python versions, have the ABI version to use for the debug version.
        if python_debug and "d" in python_abi_version:
            candidates.append(
                getNormalizedPathJoin(
                    python_prefix_external,
                    "include",
                    "python" + python_abi_version.replace("d", ""),
                )
            )

    search = ["Python.h"]
    if self_compiled_python_uninstalled:
        search.append("pyconfig.h")  # spell-checker: ignore pyconfig

    for candidate in candidates:
        for s in tuple(search):
            found = False
            if os.path.exists(getNormalizedPathJoin(candidate, s)):
                search.remove(s)
                found = True

            if found:
                return candidate

        if not search:
            break
    else:
        if isWin32Windows():
            return logger.sysexit("""\
Error, you seem to be using the unsupported embeddable CPython distribution \
use a full Python instead.""")
        else:
            return logger.sysexit(
                """\
Error, no 'Python.h' %s headers can be found at '%s', dependency \
not satisfied!"""
                % (
                    "debug" if python_debug else "development",
                    candidates,
                )
            )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
