#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Module and package attribute nodes ('__name__', '__package__', '__file__', '__spec__', '__loader__', '__compiled__')."""

import os

from nuitka.options.Options import (
    getFileReferenceMode,
    getModuleForceNamespace,
    getModuleNameMode,
)

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionBase
from .RuntimePathNodes import ExpressionRuntimePath


class ExpressionModuleAttributeBase(ExpressionBase):
    # pylint: disable=abstract-method

    __slots__ = ("variable",)

    def __init__(self, variable, source_ref):
        ExpressionBase.__init__(self, source_ref)

        self.variable = variable

    def finalize(self):
        del self.parent
        del self.variable

    def getDetails(self):
        return {"variable": self.variable}

    def getVariable(self):
        return self.variable

    @staticmethod
    def mayRaiseException(exception_type):
        return False


class ExpressionModuleAttributeDunderCompiledRef(ExpressionModuleAttributeBase):
    """Module '__compiled__' attribute filled by Nuitka without module dict lookup."""

    kind = "EXPRESSION_MODULE_ATTRIBUTE_DUNDER_COMPILED_REF"

    def computeExpressionRaw(self, trace_collection):
        return self, None, None


class ExpressionModuleAttributeFileRef(ExpressionModuleAttributeBase):
    kind = "EXPRESSION_MODULE_ATTRIBUTE_FILE_REF"

    def computeExpressionRaw(self, trace_collection):
        run_time_filename = self.variable.getModule().getRunTimeFilename()

        if getFileReferenceMode() != "runtime" or os.path.isabs(run_time_filename):
            result = makeConstantRefNode(
                constant=run_time_filename,
                source_ref=self.source_ref,
            )

            return result, "new_expression", "Using original '__file__' value."

        return (
            ExpressionRuntimePath(
                relative_path=run_time_filename,
                source_ref=self.source_ref,
            ),
            "new_expression",
            "Using runtime relative '__file__' value.",
        )


class ExpressionModuleAttributeNameRef(ExpressionModuleAttributeBase):
    kind = "EXPRESSION_MODULE_ATTRIBUTE_NAME_REF"

    def computeExpressionRaw(self, trace_collection):
        return self, None, None


def makeExpressionModuleAttributeNameRef(variable, source_ref):
    """Create a constant or runtime node for a module '__name__' reference."""
    if getModuleNameMode() != "runtime" or getModuleForceNamespace() is not None:
        return makeConstantRefNode(
            constant=variable.getModule().getRuntimeNameValue(),
            source_ref=source_ref,
        )

    return ExpressionModuleAttributeNameRef(variable=variable, source_ref=source_ref)


class ExpressionModuleAttributePackageRef(ExpressionModuleAttributeBase):
    kind = "EXPRESSION_MODULE_ATTRIBUTE_PACKAGE_REF"

    def computeExpressionRaw(self, trace_collection):
        return self, None, None


def makeExpressionModuleAttributePackageRef(variable, source_ref):
    """Create a constant or runtime node for a module '__package__' reference."""
    if getModuleNameMode() != "runtime" or getModuleForceNamespace() is not None:
        return makeConstantRefNode(
            constant=variable.getModule().getRuntimePackageValue(),
            source_ref=source_ref,
        )

    return ExpressionModuleAttributePackageRef(variable=variable, source_ref=source_ref)


class ExpressionModuleAttributeLoaderRef(ExpressionModuleAttributeBase):
    kind = "EXPRESSION_MODULE_ATTRIBUTE_LOADER_REF"

    def computeExpressionRaw(self, trace_collection):
        return self, None, None


class ExpressionModuleAttributeSpecRef(ExpressionModuleAttributeBase):
    """Module '__spec__' reference; always 'None' for a non-package '__main__' module."""

    kind = "EXPRESSION_MODULE_ATTRIBUTE_SPEC_REF"

    def computeExpressionRaw(self, trace_collection):
        if self.variable.getModule().isMainModule():
            if not self.variable.getModule().getRuntimePackageValue():
                result = makeConstantRefNode(constant=None, source_ref=self.source_ref)

                return (
                    result,
                    "new_expression",
                    "Using constant '__spec__' value for main module.",
                )

        return self, None, None


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
