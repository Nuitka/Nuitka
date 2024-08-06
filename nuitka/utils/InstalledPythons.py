#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Provide installed Pythons with module availability checks. """

import os
import sys

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonFlavors import isAnacondaPython, isMSYS2MingwPython
from nuitka.PythonVersions import (
    getInstalledPythonRegistryPaths,
    python_version_str,
)

from .Execution import (
    NuitkaCalledProcessError,
    check_output,
    getExecutablePath,
)
from .FileOperations import getDirectoryRealPath
from .Utils import isWin32Windows


class InstalledPython(object):
    def __init__(self, python_exe, python_version):
        self.python_exe = python_exe
        self.python_version = python_version

    def __repr__(self):
        return "<InstalledPython '%s' version '%s'>" % (
            self.python_exe,
            self.python_version,
        )

    def getPythonExe(self):
        return self.python_exe

    def getPythonVersion(self):
        return self.python_version

    def getHexVersion(self):
        major, minor = self.python_version.split(".")
        return int(major) * 256 + int(minor) * 16

    def isAnacondaPython(self):
        if self.python_exe == sys.executable:
            return isAnacondaPython()

        # TODO: May not yet work really.
        return os.path.exists(
            os.path.join(os.path.dirname(self.python_exe), "..", "conda-meta")
        )

    def isMSYS2MingwPython(self):
        if self.python_exe == sys.executable:
            return isMSYS2MingwPython()

        # TODO: May not yet work really.
        return (
            os.path.exists(
                os.path.join(os.path.dirname(self.python_exe), "..", "..", "msys2.ini")
            )
            and os.path.basename(os.path.dirname(self.python_exe)) == "mingw64"
        )

    def getPreferredPackageType(self):
        if self.isAnacondaPython():
            return "conda"
        elif self.isMSYS2MingwPython():
            return "pacman"
        else:
            return "pip"

    # Necessary for Python 2.7, otherwise SyntaxError is given on exec.
    @staticmethod
    def _exec(code, context):
        # We can trust our own code there, pylint: disable=exec-used
        exec(code.replace("print", "catch_print"), context)

    def checkUsability(self, module_name, module_version):
        # very many cases and return driven
        # pylint: disable=too-many-branches,too-many-return-statements

        if module_name is None:
            return True

        test_code = "import %s" % module_name

        if module_version is not None:
            test_code += ";print(%s.__version__)" % module_name

        test_code += ";print('OK')"

        if self.python_exe != sys.executable:
            try:
                output = check_output([self.python_exe, "-c", test_code])
            except NuitkaCalledProcessError:
                return False
            except OSError:
                return False

            output = output.splitlines()
        else:
            output = []

            def catch_print(value):
                output.append(value)

            try:
                self._exec(code=test_code, context={"catch_print": catch_print})
            except ImportError:
                return False

            if str is not bytes:
                output = [line.encode("utf8") for line in output]

        if output[-1] != b"OK":
            return False

        if module_version is not None:
            detected_version = output[-2].split(b".")

            if str is not bytes:
                module_version = module_version.encode("utf8")

            for detected_part, wanted_part in zip(
                detected_version, module_version.split(b".")
            ):
                if int(detected_part) < int(wanted_part):
                    return False

        return True


_installed_pythons = {}


def _getPythonInstallPathsWindows(python_version):
    """Find Python installation on Windows.

    Find a Python installation, first try a few
    guesses for their paths, then look into registry for user or system wide
    installations.
    """
    seen = set()

    # Shortcuts for the default installation directories, to avoid going to
    # registry at all unless necessary. Any Python2 will do for Scons, so it
    # might be avoided entirely.

    candidate = r"c:\python%s\python.exe" % python_version.replace(".", "")

    if os.path.isfile(candidate):
        candidate = os.path.join(
            getDirectoryRealPath(os.path.dirname(candidate)),
            os.path.basename(candidate),
        )

        yield candidate

        seen.add(candidate)

    for candidate in getInstalledPythonRegistryPaths(python_version):
        if candidate not in seen:
            seen.add(candidate)
            yield candidate


def findPythons(python_version, module_name=None, module_version=None):
    """Find all Python installations for a specific version."""

    if python_version not in _installed_pythons:
        result = OrderedSet()

        if python_version == python_version_str:
            result.add(
                InstalledPython(
                    python_exe=sys.executable, python_version=python_version
                )
            )

        if isWin32Windows():
            result.update(
                InstalledPython(python_exe=python_exe, python_version=python_version)
                for python_exe in _getPythonInstallPathsWindows(python_version)
            )

        candidate = getExecutablePath("python" + python_version)
        if candidate is not None:
            result.add(
                InstalledPython(python_exe=candidate, python_version=python_version)
            )

        _installed_pythons[python_version] = result

    return tuple(
        sorted(
            (
                candidate
                for candidate in _installed_pythons[python_version]
                if candidate.checkUsability(
                    module_name=module_name, module_version=module_version
                )
            ),
            key=lambda c: c.getPythonExe(),
        )
    )


def findInstalledPython(python_versions, module_name, module_version):
    python_versions = list(python_versions)
    python_versions.sort(
        key=lambda python_version: python_version != python_version_str
    )

    # Make sure the current Python version is scanned for if acceptable.
    if python_version_str in python_versions:
        findPythons(python_version_str)

    # Attempt to prefer scanned versions.
    for python_version in python_versions:
        for candidate in _installed_pythons.get(python_version, ()):
            if module_name is None or candidate.checkUsability(
                module_name=module_name, module_version=module_version
            ):
                return candidate

    # Attempt to find so far not scanned versions.
    for python_version in python_versions:
        if python_version not in _installed_pythons:
            for candidate in findPythons(python_version):
                if module_name is None or candidate.checkUsability(
                    module_name=module_name, module_version=module_version
                ):
                    return candidate

    return None


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
