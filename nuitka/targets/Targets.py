#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Target ABI specifications for cross compilation."""

_target_specification = None


class TargetCompileTimeEvaluationNotAvailable(Exception):
    """The target cannot evaluate compile-time expressions yet."""


class TargetBase(object):
    """Base class for target ABI specifications.

    Notes:
        The target is selected once during option parsing. This class and its
        subclasses only describe the selected target; they do not parse options.
    """

    # The target specification is going to gain more attributes over time.
    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        name,
        c_long_size,
        c_longlong_size,
        c_pointer_size,
        target_os,
        target_arch,
        binary_format,
        rpath_using,
        python_digit_bits,
    ):
        self.name = name
        self.target_os = target_os
        self.target_arch = target_arch
        self.binary_format = binary_format
        self.rpath_using = rpath_using

        self.c_long_size = c_long_size
        self.c_longlong_size = c_longlong_size
        self.c_pointer_size = c_pointer_size

        digit_boundary = 2**python_digit_bits - 1

        self.c_long_min = -(2 ** (c_long_size * 7))
        self.c_long_max = 2 ** (c_long_size * 7) - 1
        self.c_longlong_min = -(2 ** (c_longlong_size * 8 - 1))
        self.c_longlong_max = 2 ** (c_longlong_size * 8 - 1) - 1
        self.digit_min = -digit_boundary
        self.digit_max = digit_boundary

    def getDescription(self):
        """Return the target description."""
        return self.name

    def getTargetArch(self):
        """Return the target architecture."""
        return self.target_arch

    def getTargetOS(self):
        """Return the target operating system."""
        return self.target_os

    def getCLongSize(self):
        """Return the size of C 'long' for this target."""
        return self.c_long_size

    def getCLongLongSize(self):
        """Return the size of C 'long long' for this target."""
        return self.c_longlong_size

    def getCPointerSize(self):
        """Return the size of a C pointer for this target."""
        return self.c_pointer_size

    def getBinaryFormat(self):
        """Return the target binary format, e.g. 'elf', 'coff', or 'wasm'."""
        return self.binary_format

    def isWasiTarget(self):
        """Return whether this target uses the WASI ABI."""
        return self.target_os == "WASI"

    def isWin32Target(self):
        """Return whether this target uses the Windows ABI."""
        return self.target_os == "Windows"

    def isElfTarget(self):
        """Return whether this target uses the ELF file format."""
        return self.binary_format == "elf"

    def isRPathUsingTarget(self):
        """Return whether this target uses RPATH or an equivalent."""
        return self.rpath_using

    def hasTargetSupportForDLLs(self):
        """Return whether the target can use detected DLL dependencies."""
        return not self.isWasiTarget()

    def getPythonVersionInfo(self):  # pylint: disable=no-self-use
        """Return the target Python's version information, or None if unknown."""
        return None

    def getModuleSubPackages(self, module_name):  # pylint: disable=no-self-use
        """Return the importable subpackages of a module on the target.

        Args:
            module_name: str of the module to inspect.

        Raises:
            TargetCompileTimeEvaluationNotAvailable: when no target Python is
                available for this target yet.
        """
        raise TargetCompileTimeEvaluationNotAvailable

    def canImportModule(self, module_name):  # pylint: disable=no-self-use
        """Return whether a module is importable on the target.

        Args:
            module_name: str of the module to check.

        Raises:
            TargetCompileTimeEvaluationNotAvailable: when no target Python is
                available for this target yet.
        """
        raise TargetCompileTimeEvaluationNotAvailable

    def evaluateCompileTimeExpression(  # pylint: disable=no-self-use
        self, expression, setup_code
    ):
        """Evaluate an expression with the target Python semantics.

        Args:
            expression: str containing the expression to evaluate.
            setup_code: str containing statements to execute before evaluating
                the expression, e.g. imports.

        Raises:
            TargetCompileTimeEvaluationNotAvailable: when no target Python is
                available for this target yet.
        """
        raise TargetCompileTimeEvaluationNotAvailable

    def isValidCLongValue(self, value):
        """Return whether a Python value fits the target C 'long'."""
        return self.c_long_min <= value <= self.c_long_max

    def isValidCLongLongValue(self, value):
        """Return whether a Python value fits the target C 'long long'."""
        return self.c_longlong_min <= value <= self.c_longlong_max

    def isValidDigitValue(self, value):
        """Return whether a Python value fits into a target float digit.

        Notes:
            Digits in long objects do not use 2-complement, but a boolean sign.
        """
        return self.digit_min <= value <= self.digit_max


def setTargetSpecification(target_name):
    """Select and install the target specification.

    Args:
        target_name: Canonical target name, one of 'native', 'wasm32-wasi',
            or 'i686-w64-mingw32'.
    """
    global _target_specification  # singleton, pylint: disable=global-statement

    assert _target_specification is None, "target specification already set"

    if target_name == "native":
        from .TargetNative import TargetNative

        _target_specification = TargetNative()
    elif target_name == "wasm32-wasi":
        from .TargetWASI import TargetWASI

        _target_specification = TargetWASI()
    elif target_name == "i686-w64-mingw32":
        from .TargetWin32 import TargetWin32

        _target_specification = TargetWin32()
    else:
        raise ValueError("Unsupported target %r" % target_name)


def getTargetSpecification():
    """Return the installed target specification."""
    return _target_specification


def isWasiTarget():
    """Return whether the installed target uses the WASI ABI."""
    return _target_specification.isWasiTarget()


def isNativeTarget():
    """Return whether the installed target is the native target."""
    return _target_specification.name == "native"


def isWin32Target():
    """Return whether the installed target uses the Windows ABI."""
    return _target_specification.isWin32Target()


def isElfTarget():
    """Return whether the installed target uses the ELF file format."""
    return _target_specification.isElfTarget()


def isWin32OrPosixWindowsTarget():
    """Return whether the installed target is Windows-like."""
    return _target_specification.isWin32Target()


def isRPathUsingTarget():
    """Return whether the installed target uses RPATH or an equivalent."""
    return _target_specification.isRPathUsingTarget()


_onefile_supported_target_os = (
    "Linux",
    "Windows",
    "Darwin",
    "FreeBSD",
    "OpenBSD",
    "AIX",
)

# WASI supports standalone builds, but not onefile.
_standalone_supported_target_os = _onefile_supported_target_os + ("WASI",)


def isStandaloneSupportedTarget():
    """Return whether standalone mode is supported for the installed target."""
    return _target_specification.getTargetOS() in _standalone_supported_target_os


def isOnefileSupportedTarget():
    """Return whether onefile mode is supported for the installed target."""
    return _target_specification.getTargetOS() in _onefile_supported_target_os


def getTargetCLongSize():
    """Return the installed target's C 'long' size."""
    return _target_specification.getCLongSize()


def isTargetValidCLongValue(value):
    """Return whether a Python value fits the installed target's C 'long'."""
    return _target_specification.isValidCLongValue(value)


def isTargetValidCLongLongValue(value):
    """Return whether a Python value fits the installed target's C 'long long'."""
    return _target_specification.isValidCLongLongValue(value)


def isTargetValidDigitValue(value):
    """Return whether a Python value fits into an installed target float digit."""
    return _target_specification.isValidDigitValue(value)


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
