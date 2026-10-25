#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Target specification for WASI on wasm32."""

from nuitka.options.Options import (
    assumeYesForDownloads,
    shallDisableCacheUsage,
)
from nuitka.utils.WasiPython import getWasiPythonPrefix

from .TargetPython import TargetPython
from .Targets import TargetBase


class TargetWASI(TargetBase):
    """Target specification for the wasm32-wasi ABI."""

    def __init__(self):
        TargetBase.__init__(
            self,
            name="wasm32-wasi",
            c_long_size=4,
            c_longlong_size=8,
            c_pointer_size=4,
            target_os="WASI",
            target_arch="wasm32",
            binary_format="wasm",
            rpath_using=False,
            python_digit_bits=15,
        )

        assume_yes_for_downloads = assumeYesForDownloads()

        self._target_python = TargetPython(
            target_spec=self,
            python_prefix=getWasiPythonPrefix(
                assume_yes_for_downloads=assume_yes_for_downloads
            ),
            assume_yes_for_downloads=assume_yes_for_downloads,
            use_cache=not shallDisableCacheUsage("all"),
        )

    def evaluateCompileTimeExpression(self, expression, setup_code):
        """Evaluate an expression with the WASI target Python."""
        return self._target_python.evaluate(expression, setup_code)

    def getPythonVersionInfo(self):
        """Return the target Python's version information."""
        return self._target_python.getPythonVersionInfo()

    def getModuleSubPackages(self, module_name):
        """Return importable subpackages for a module on WASI."""
        return self._target_python.getModuleSubPackages(module_name)

    def canImportModule(self, module_name):
        """Return whether a module is importable on WASI."""
        return self._target_python.canImportModule(module_name)

    @staticmethod
    def isHardModuleSupported(module_name):
        """Return whether a hard module is available for WASI."""
        return module_name != "ctypes"


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
