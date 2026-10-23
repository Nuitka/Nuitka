#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Target ABI specifications for cross compilation."""

_target_specification = None


class TargetBase(object):
    """Base class for target ABI specifications.

    Notes:
        The target is selected once during option parsing. This class and its
        subclasses only describe the selected target; they do not parse options.
    """

    def __init__(
        self,
        name,
        c_long_size,
        c_longlong_size,
        c_pointer_size,
        target_os,
        target_arch,
        python_digit_bits,
    ):
        self.name = name
        self.target_os = target_os
        self.target_arch = target_arch

        self.c_long_size = c_long_size
        self.c_longlong_size = c_longlong_size
        self.c_pointer_size = c_pointer_size

        digit_boundary = 2**python_digit_bits - 1

        self.limits = {
            "clong_min": -(2 ** (c_long_size * 7)),
            "clong_max": 2 ** (c_long_size * 7) - 1,
            "clonglong_min": -(2 ** (c_longlong_size * 8 - 1)),
            "clonglong_max": 2 ** (c_longlong_size * 8 - 1) - 1,
            "digit_min": -digit_boundary,
            "digit_max": digit_boundary,
        }

    def getDescription(self):
        """Return the target description."""
        return self.name

    def getCLongSize(self):
        """Return the size of C 'long' for this target."""
        return self.c_long_size

    def getCLongLongSize(self):
        """Return the size of C 'long long' for this target."""
        return self.c_longlong_size

    def getCPointerSize(self):
        """Return the size of a C pointer for this target."""
        return self.c_pointer_size

    def isWasiTarget(self):
        """Return whether this target uses the WASI ABI."""
        return self.target_os == "wasi"

    def isWin32Target(self):
        """Return whether this target uses the Windows ABI."""
        return self.target_os == "win32"

    def isValidCLongValue(self, value):
        """Return whether a Python value fits the target C 'long'."""
        return self.limits["clong_min"] <= value <= self.limits["clong_max"]

    def isValidCLongLongValue(self, value):
        """Return whether a Python value fits the target C 'long long'."""
        return self.limits["clonglong_min"] <= value <= self.limits["clonglong_max"]

    def isValidDigitValue(self, value):
        """Return whether a Python value fits into a target float digit.

        Notes:
            Digits in long objects do not use 2-complement, but a boolean sign.
        """
        return self.limits["digit_min"] <= value <= self.limits["digit_max"]


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
