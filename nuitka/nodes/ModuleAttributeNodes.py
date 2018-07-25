#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" Module/Package attribute nodes

The represent special values of the modules. The __name__, __package__ and
__file__ values can all be highly dynamic and version dependent. These nodes
are intended to allow for as much compile time optimization as possible,
despite this difficulty.

"""
from nuitka import Options

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionBase


class ExpressionModuleAttributeBase(ExpressionBase):
    # Base classes can be abstract, pylint: disable=abstract-method

    __slots__ = ("module",)

    def __init__(self, module, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

        self.module = module

    def finalize(self):
        del self.parent
        del self.module

    def getDetails(self):
        return {
            "module" : self.module
        }


    def mayRaiseException(self, exception_type):
        return False


class ExpressionModuleAttributeFileRef(ExpressionModuleAttributeBase):
    kind = "EXPRESSION_MODULE_ATTRIBUTE_FILE_REF"


    def computeExpressionRaw(self, trace_collection):
        # There is not a whole lot to do here, the path will change at run
        # time, but options may disable that and make it predictable.
        if Options.getFileReferenceMode() != "runtime":
            result = makeConstantRefNode(
                constant   = self.module.getRunTimeFilename(),
                source_ref = self.module.getSourceReference()
            )

            return result, "new_expression", "Using original '__file__' value."

        return self, None, None


class ExpressionModuleAttributeNameRef(ExpressionModuleAttributeBase):
    kind = "EXPRESSION_MODULE_ATTRIBUTE_NAME_REF"

    def computeExpressionRaw(self, trace_collection):
        # For binaries, we can know it definite, but not for modules.

        if not Options.shallMakeModule():
            result = makeConstantRefNode(
                constant   = self.module.getFullName(),
                source_ref = self.getSourceReference()
            )

            return result, "new_expression", "Using constant '__name__' value."

        return self, None, None


class ExpressionModuleAttributePackageRef(ExpressionModuleAttributeBase):
    kind = "EXPRESSION_MODULE_ATTRIBUTE_PACKAGE_REF"

    def computeExpressionRaw(self, trace_collection):
        # For binaries, we can know it definite, but not for modules.

        if not Options.shallMakeModule():
            provider = self.module

            if provider.isCompiledPythonPackage():
                value = provider.getFullName()
            else:
                value = provider.getPackage()

            result = makeConstantRefNode(
                constant   = value,
                source_ref = self.source_ref
            )

            return result, "new_expression", "Using constant '__package__' value."

        return self, None, None


class ExpressionModuleAttributeLoaderRef(ExpressionModuleAttributeBase):
    kind = "EXPRESSION_MODULE_ATTRIBUTE_LOADER_REF"

    def computeExpressionRaw(self, trace_collection):
        return self, None, None


class ExpressionModuleAttributeSpecRef(ExpressionModuleAttributeBase):
    kind = "EXPRESSION_MODULE_ATTRIBUTE_SPEC_REF"

    def computeExpressionRaw(self, trace_collection):
        if self.module.isMainModule():
            result = makeConstantRefNode(
                constant   = None,
                source_ref = self.source_ref
            )

            return result, "new_expression", "Using constant '__spec__' value for main module."

        return self, None, None
