#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Target specification for 32-bit Windows."""

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
