#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Numba plugin.

When the Numba JIT is enabled, it compiles functions from their Python
bytecode, which compiled functions do not have. Therefore the modules of the
'numba' package are compiled to bytecode, and functions in other modules using
the common Numba decorators are left uncompiled, so that the JIT can find the
bytecode of the functions it is given.
"""

from nuitka.options.Options import isStandaloneMode
from nuitka.plugins.PluginBase import (
    NuitkaNamespaceDetectorPluginBase,
    NuitkaPluginBase,
)


class NuitkaPluginNumba(NuitkaPluginBase):
    """Support for Numba JIT compiled functions."""

    plugin_name = "numba"
    plugin_desc = "Required for 'numba' JIT compilation of functions."
    plugin_category = "package-support"

    def __init__(self, enable_jit):
        if enable_jit is None:
            enable_jit = "no" if isStandaloneMode() else "yes"

        self.enable_jit = enable_jit

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--numba-enable-jit",
            action="store",
            dest="enable_jit",
            choices=("yes", "no"),
            default=None,
            help="""\
Whether to enable the JIT of 'numba'. Defaults to 'no' in standalone mode
and 'yes' otherwise.""",
        )

    def _isNumbaJitEnabled(self):
        return self.enable_jit == "yes"

    def createPreModuleLoadCode(self, module):
        if not self._isNumbaJitEnabled() and module.getFullName() == "numba":
            yield (
                "import os\nos.environ['NUMBA_DISABLE_JIT'] = '1'",
                "According to '--numba-enable-jit' option.",
            )

    def decideCompilation(self, module_name):
        # Numba compiles functions of its own package too, e.g. for the
        # "vectorize" and "stencil" decorators, even when the JIT is disabled,
        # so all of its modules need real bytecode.
        if module_name.hasNamespace("numba"):
            return "bytecode"

        return None

    def getUncompiledDecoratorNames(self):
        # The stencil decorator always compiles its function, even when the
        # JIT is disabled, so those functions always need real bytecode.
        yield "stencil"

        if self._isNumbaJitEnabled():
            for decorator_name in (
                "njit",
                "jit",
                "generated_jit",
                "vectorize",
                "guvectorize",
                "cfunc",
            ):
                yield decorator_name


class NuitkaPluginDetectorNumba(NuitkaNamespaceDetectorPluginBase):
    """Used only if plugin is not activated.

    Notes:
        We are given the chance to issue a warning if we think we may be
        required.
    """

    detector_for = NuitkaPluginNumba
    detector_namespaces = ("numba",)


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
