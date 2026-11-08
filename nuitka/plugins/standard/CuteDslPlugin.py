#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""CuTe DSL plugin.

The CuTe DSL rewrites the '__code__' attribute of functions decorated with
'@cute.jit' or '@cute.kernel' during JIT preparation. Compiled functions do
not allow that, so these functions are included as bytecode instead. The rest
of their module stays compiled.
"""

from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginCuteDsl(NuitkaPluginBase):
    """Support for functions compiled by the CuTe DSL."""

    plugin_name = "cute-dsl"
    plugin_desc = "Required for CuTe DSL functions that rewrite their '__code__'."
    plugin_category = "package-support"

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def getUncompiledDecoratorNames():
        yield "cutlass.cute.jit"
        yield "cutlass.cute.kernel"


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
