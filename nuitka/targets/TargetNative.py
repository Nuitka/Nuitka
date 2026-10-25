#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Target specification for the local Python ABI."""

import ctypes
import sys

from nuitka.PythonVersions import getImportlibSubPackages
from nuitka.utils.Utils import (
    getArchitecture,
    getOS,
    isAIX,
    isMacOS,
    isRPathUsingPlatform,
    isWin32OrPosixWindows,
)

from .Targets import TargetBase


def _getBinaryFormat():
    if isWin32OrPosixWindows():
        return "coff"

    if isMacOS():
        return "macho"

    if isAIX():
        return "xcoff"

    return "elf"


def _getPythonDigitBits():
    if sys.version_info < (2, 7):
        return 15
    elif sys.version_info < (3, 0):
        return sys.long_info.bits_per_digit
    else:
        return sys.int_info.bits_per_digit


class TargetNative(TargetBase):
    """Target specification derived from the running Python."""

    def __init__(self):
        TargetBase.__init__(
            self,
            name="native",
            c_long_size=ctypes.sizeof(ctypes.c_long),
            c_longlong_size=ctypes.sizeof(ctypes.c_longlong),
            c_pointer_size=ctypes.sizeof(ctypes.c_void_p),
            target_os=getOS(),
            target_arch=getArchitecture(),
            binary_format=_getBinaryFormat(),
            rpath_using=isRPathUsingPlatform(),
            python_digit_bits=_getPythonDigitBits(),
        )

    def evaluateCompileTimeExpression(self, expression, setup_code):
        """Evaluate an expression with the running Python."""
        # The code is generated internally from hard module names.
        namespace = {"__builtins__": __builtins__}
        if setup_code:
            exec(setup_code, namespace)  # pylint: disable=exec-used
        return eval(expression, namespace, {})  # pylint: disable=eval-used

    def getPythonVersionInfo(self):
        """Return the target Python's version information."""
        return sys.version_info

    def getModuleSubPackages(self, module_name):
        """Return importable subpackages for a module on the target."""
        assert module_name == "importlib", module_name
        return getImportlibSubPackages()

    def canImportModule(self, module_name):
        """Return whether a module is importable on the target."""
        try:
            from importlib.util import find_spec
        except ImportError:
            from pkgutil import get_loader

            return get_loader(module_name) is not None

        try:
            return find_spec(module_name) is not None
        except ImportError:
            return False

    @staticmethod
    def isHardModuleSupported(module_name):
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
