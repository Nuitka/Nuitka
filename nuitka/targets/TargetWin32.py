#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Target specification for 32-bit Windows."""

import ntpath
import os

from nuitka.options.Options import (
    assumeYesForDownloads,
    getWin32PythonExePath,
    isZig,
    shallDisableCacheUsage,
)
from nuitka.PythonVersions import python_version_str
from nuitka.Tracing import general
from nuitka.utils.Execution import executeProcess, getExecutablePath
from nuitka.utils.FileOperations import (
    getNormalizedPath,
    getNormalizedPathJoin,
)
from nuitka.utils.Utils import (
    isLinuxWSL,
    isWin32OrPosixWindows,
    isWin32Windows,
)

from .TargetPython import TargetPython, TargetPythonError
from .Targets import TargetBase


class TargetWin32(TargetBase):
    """Target specification for the i686-w64-mingw32 ABI."""

    def __init__(self):
        TargetBase.__init__(
            self,
            name="i686-w64-mingw32",
            c_long_size=4,
            c_longlong_size=8,
            c_pointer_size=4,
            target_os="Windows",
            target_arch="x86",
            binary_format="coff",
            rpath_using=False,
            python_digit_bits=15,
        )

        self._python_executable = getWin32PythonExePath()
        self._target_python = None

    def _getTargetPython(self):
        if self._target_python is None:
            assume_yes_for_downloads = assumeYesForDownloads()

            self._target_python = TargetPython(
                target_spec=self,
                python_prefix=None,
                python_executable=self._python_executable,
                assume_yes_for_downloads=assume_yes_for_downloads,
                use_cache=not shallDisableCacheUsage("all"),
            )

        return self._target_python

    def getPythonPrefix(self):
        """Return the Windows Python prefix used by this target."""
        return self._getTargetPython().getTargetSystemPrefixPath()

    def getPythonDLLPath(self):
        """Return the Python DLL path used by this target."""
        return self._getTargetPython().getTargetPythonDLLPath()

    def getSystemStaticLibPythonPath(self, python_debug):
        """Return the Windows Python static library path, if available."""
        target_path = self._getTargetPython().evaluate(
            expression="""\
nuitka.utils.StaticLibraries.getSystemStaticLibPythonPath(
    python_debug=%r,
)""" % python_debug,
            setup_code="import nuitka.utils.StaticLibraries",
        )

        if target_path is None:
            return None

        return self.translateTargetPathToHost(target_path)

    def couldUseStaticLibPython(self, python_debug, dll_mode):
        """Return whether the Windows Python can use a static libpython."""
        return self._getTargetPython().evaluate(
            expression="""\
nuitka.utils.StaticLibraries.couldUseStaticLibPython(
    python_debug=%r,
    dll_mode=%r,
)""" % (python_debug, dll_mode),
            setup_code="import nuitka.utils.StaticLibraries",
        )

    def translateHostPathToTarget(self, host_path):
        """Translate a host path to a path usable by the target Python."""
        if isWin32Windows():
            return host_path

        for tool_name in ("wslpath", "winepath"):
            if tool_name == "wslpath" and not isLinuxWSL():
                continue

            tool_path = getExecutablePath(tool_name)

            if tool_path is None:
                continue

            process_result = executeProcess((tool_path, "-w", host_path))

            if process_result.exit_code != 0:
                continue

            output = process_result.stdout

            if str is not bytes and type(output) is bytes:
                output = output.decode("utf8")

            output = output.strip()

            if output:
                return output

        if self._python_executable is None:
            return host_path

        target_executable = self._getTargetPython().getTargetExecutablePath()

        if target_executable is None:
            return host_path

        target_dir = ntpath.dirname(target_executable)
        host_dir = os.path.dirname(os.path.abspath(self._python_executable))
        relative_path = os.path.relpath(host_path, host_dir)

        if relative_path == os.pardir or relative_path.startswith(os.pardir + os.sep):
            return host_path

        relative_path = relative_path.replace(os.sep, "\\")

        return ntpath.normpath(ntpath.join(target_dir, relative_path))

    def translateTargetPathToHost(self, target_path):
        """Translate a path reported by the target Python to a host path."""
        if isWin32Windows():
            return getNormalizedPath(target_path)

        if os.path.exists(target_path):
            return getNormalizedPath(target_path)

        if self._python_executable is None:
            raise TargetPythonError(
                "Cannot translate target path '%s' without a target executable."
                % target_path
            )

        target_python = self._getTargetPython()
        target_python.start()
        target_executable = target_python.getTargetExecutablePath()
        target_dir = ntpath.dirname(target_executable)
        host_dir = os.path.dirname(os.path.abspath(self._python_executable))

        try:
            relative_path = ntpath.relpath(target_path, target_dir)
        except ValueError:
            raise TargetPythonError(
                "Cannot translate target path '%s' relative to '%s'."
                % (target_path, target_executable)
            )

        relative_path = relative_path.replace("\\", os.sep)

        return getNormalizedPathJoin(host_dir, relative_path)

    def getTargetRunCommand(self, executable_path):
        """Return the command to run a Windows executable on this host."""
        if isWin32OrPosixWindows() or isLinuxWSL():
            return (executable_path,)

        wine_path = getExecutablePath("wine")

        if wine_path is None:
            return general.sysexit(
                "Error, running the Win32 target requires 'wine' on non-Windows platforms."
            )

        return (wine_path, executable_path)

    def getPythonSconsOptions(self):
        """Return the Windows Python paths for Scons."""
        target_python = self._getTargetPython()

        return {
            "python_prefix": target_python.getTargetSystemPrefixPath(),
            "python_include_path": target_python.getTargetPythonIncludePath(),
        }

    def checkPreconditions(self):
        """Check that the Windows Python executable is usable."""

        # Many error exits, pylint: disable=too-many-return-statements

        if not isWin32Windows() and not isZig():
            return general.sysexit(
                "Error, the Win32 cross target on non-Windows hosts requires '--zig'."
            )

        if self._python_executable is None:
            return general.sysexit("""\
Error, the Win32 target requires a Windows Python executable. Use \
'--win32-python-exe=PATH'.""")

        if not os.path.isfile(self._python_executable):
            return general.sysexit(
                "Error, the Win32 Python executable '%s' does not exist."
                % self._python_executable
            )

        target_python = self._getTargetPython()
        target_info = target_python.start()

        if target_info.get("platform") != "win32":
            return general.sysexit(
                "Error, '%s' is not a Windows Python executable."
                % self._python_executable
            )

        target_version = ".".join(
            str(part) for part in target_info["python_version"][:2]
        )

        if target_version != python_version_str:
            return general.sysexit(
                """\
Error, '%s' is a Python %s executable, but Nuitka is running with Python %s. \
The target Python version must match the running Python version."""
                % (
                    self._python_executable,
                    target_version,
                    python_version_str,
                )
            )

        python_prefix = target_python.getTargetSystemPrefixPath()

        if not os.path.isdir(python_prefix):
            return general.sysexit(
                "Error, cannot access the Win32 Python prefix '%s'." % python_prefix
            )

        python_dll_path = target_python.getTargetPythonDLLPath()

        if not os.path.isfile(python_dll_path):
            return general.sysexit(
                "Error, cannot access the Win32 Python DLL '%s'." % python_dll_path
            )

    def evaluateCompileTimeExpression(self, expression, setup_code):
        """Evaluate an expression with the Win32 target Python."""
        return self._getTargetPython().evaluate(
            expression=expression,
            setup_code=setup_code,
        )

    def getPythonVersionInfo(self):
        """Return the target Python's version information."""
        return self._getTargetPython().getPythonVersionInfo()

    def getModuleSubPackages(self, module_name):
        """Return importable subpackages for a module on Win32."""
        return self._getTargetPython().getModuleSubPackages(module_name)

    def canImportModule(self, module_name):
        """Return whether a module is importable on Win32."""
        return self._getTargetPython().canImportModule(module_name)

    def isHardModuleSupported(self, module_name):  # pylint: disable=no-self-use
        """Return whether a hard module is available for this target."""
        # pylint: disable=unused-argument
        return True


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
