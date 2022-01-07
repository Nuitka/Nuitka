#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

The represent special values of the modules. The "__name__", "__package__",
"__file__", and "__spec__" values can all be highly dynamic and version
dependent

These nodes are intended to allow for as much compile time optimization as
possible, despite this difficulty. In some modes these node become constants
quickly, in others they will present boundaries for optimization.

"""

from nuitka import Options

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionBase, ExpressionNoSideEffectsMixin


class ExpressionModuleAttributeBase(ExpressionBase):
    """Expression base class for module attributes.

    This
    """

    # Base classes can be abstract, pylint: disable=abstract-method

    __slots__ = ("variable",)

    def __init__(self, variable, source_ref):
        ExpressionBase.__init__(self, source_ref=source_ref)

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
        # These attributes can be expected to be present.

        return False


class ExpressionModuleAttributeFileRef(ExpressionModuleAttributeBase):
    """Expression that represents accesses to __file__ of module.

    The __file__ is a static or dynamic value depending on the
    file reference mode. If it requests runtime, i.e. looks at
    where it is loaded from, then there is not a lot to be said
    about its value, otherwise it becomes a constant value
    quickly.
    """

    kind = "EXPRESSION_MODULE_ATTRIBUTE_FILE_REF"

    def computeExpressionRaw(self, trace_collection):
        # There is not a whole lot to do here, the path will change at run
        # time, but options may disable that and make it predictable.
        if Options.getFileReferenceMode() != "runtime":
            result = makeConstantRefNode(
                constant=self.variable.getModule().getRunTimeFilename(),
                source_ref=self.source_ref,
            )

            return result, "new_expression", "Using original '__file__' value."

        return self, None, None


class ExpressionModuleAttributeNameRef(ExpressionModuleAttributeBase):
    """Expression that represents accesses to __name__ of module.

    For binaries this can be relatively well known, but modules
    living in a package, go by what loads them to ultimately
    determine their name.
    """

    kind = "EXPRESSION_MODULE_ATTRIBUTE_NAME_REF"

    def computeExpressionRaw(self, trace_collection):
        # For binaries, we can know it definite, but not for modules.

        if not Options.shallMakeModule():
            result = makeConstantRefNode(
                constant=self.variable.getModule().getRuntimeNameValue(),
                source_ref=self.source_ref,
            )

            return result, "new_expression", "Using constant '__name__' value."

        return self, None, None


class ExpressionModuleAttributePackageRef(ExpressionModuleAttributeBase):
    """Expression that represents accesses to __package__ of module.

    For binaries this can be relatively well known, but modules
    living in a package, go by what loads them to ultimately
    determine their parent package.
    """

    kind = "EXPRESSION_MODULE_ATTRIBUTE_PACKAGE_REF"

    def computeExpressionRaw(self, trace_collection):
        # For binaries, we can know it definite, but not for modules.

        if not Options.shallMakeModule():
            provider = self.variable.getModule()
            value = provider.getRuntimePackageValue()

            result = makeConstantRefNode(constant=value, source_ref=self.source_ref)

            return result, "new_expression", "Using constant '__package__' value."

        return self, None, None


class ExpressionModuleAttributeLoaderRef(ExpressionModuleAttributeBase):
    """Expression that represents accesses to __loader__ of module.

    The loader of Nuitka is going to load the module, and there
    is not a whole lot to be said about it here, it is assumed
    to be largely ignored in user code.
    """

    kind = "EXPRESSION_MODULE_ATTRIBUTE_LOADER_REF"

    def computeExpressionRaw(self, trace_collection):
        return self, None, None


class ExpressionModuleAttributeSpecRef(ExpressionModuleAttributeBase):
    """Expression that represents accesses to __spec__ of module.

    The __spec__ is used by the loader mechanism and sometimes
    by code checking e.g. if something is a package. It exists
    only for modern Python. For the main program module, it's
    always None (it is also not really loaded in the same way
    as other code).
    """

    kind = "EXPRESSION_MODULE_ATTRIBUTE_SPEC_REF"

    def computeExpressionRaw(self, trace_collection):
        if self.variable.getModule().isMainModule():
            result = makeConstantRefNode(constant=None, source_ref=self.source_ref)

            return (
                result,
                "new_expression",
                "Using constant '__spec__' value for main module.",
            )

        return self, None, None


class ExpressionNuitkaLoaderCreation(ExpressionNoSideEffectsMixin, ExpressionBase):
    __slots__ = ("provider",)

    kind = "EXPRESSION_NUITKA_LOADER_CREATION"

    def __init__(self, provider, source_ref):
        ExpressionBase.__init__(self, source_ref=source_ref)

        self.provider = provider

    def finalize(self):
        del self.parent
        del self.provider

    def computeExpressionRaw(self, trace_collection):
        # Nothing can be done here.
        return self, None, None
