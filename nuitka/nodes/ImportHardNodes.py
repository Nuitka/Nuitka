#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes representing more trusted imports. """

from nuitka.importing.Importing import locateModule
from nuitka.utils.ModuleNames import ModuleName

from .ExpressionBases import ExpressionBase


class ExpressionImportHardBase(ExpressionBase):
    # Base classes can be abstract, pylint: disable=abstract-method
    #
    __slots__ = ("module_name", "finding", "module_filename")

    def __init__(self, module_name, source_ref):
        ExpressionBase.__init__(self, source_ref=source_ref)

        self.module_name = ModuleName(module_name)

        self.finding = None
        self.module_filename = None

        _module_name, self.module_filename, self.finding = locateModule(
            module_name=self.module_name,
            parent_package=None,
            level=0,
        )

        # Expect to find them and to match the name of course.
        assert self.finding != "not-found", self.module_name
        assert _module_name == self.module_name, _module_name

    def getUsedModule(self):
        return self.module_name, self.module_filename, self.finding


class ExpressionImportModuleNameHardBase(ExpressionImportHardBase):
    """Hard import names base class."""

    # Base classes can be abstract, pylint: disable=I0021,abstract-method

    __slots__ = ("import_name", "finding", "module_filename", "module_guaranteed")

    def __init__(self, module_name, import_name, module_guaranteed, source_ref):
        ExpressionImportHardBase.__init__(
            self, module_name=module_name, source_ref=source_ref
        )

        self.import_name = import_name

        self.module_guaranteed = module_guaranteed

    def getDetails(self):
        return {
            "module_name": self.module_name,
            "import_name": self.import_name,
            "module_guaranteed": self.module_guaranteed,
        }

    # Derived ones have the same interface.
    @staticmethod
    def isExpressionImportModuleNameHard():
        return True

    @staticmethod
    def hasVeryTrustedValue():
        return True

    def finalize(self):
        del self.parent

    def getModuleName(self):
        return self.module_name

    def getImportName(self):
        return self.import_name


class ExpressionImportModuleNameHardMaybeExists(ExpressionImportModuleNameHardBase):
    """Hard coded import names, e.g. of "site.something"

    These are created for attributes of hard imported modules that are not know if
    they exist or not.
    """

    kind = "EXPRESSION_IMPORT_MODULE_NAME_HARD_MAYBE_EXISTS"

    def computeExpressionRaw(self, trace_collection):
        trace_collection.onExceptionRaiseExit(AttributeError)

        return self, None, None

    @staticmethod
    def mayHaveSideEffects():
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        return True


class ExpressionImportModuleNameHardExists(ExpressionImportModuleNameHardBase):
    """Hard coded import names, e.g. of "sys.stdout"

    These are directly created for some Python mechanics.
    """

    kind = "EXPRESSION_IMPORT_MODULE_NAME_HARD_EXISTS"

    def computeExpressionRaw(self, trace_collection):
        if not self.module_guaranteed:
            trace_collection.onExceptionRaiseExit(ImportError)

        # As good as it gets.
        return self, None, None

    def mayHaveSideEffects(self):
        return not self.module_guaranteed

    def mayRaiseException(self, exception_type):
        return not self.module_guaranteed

    def computeExpressionCallViaVariable(
        self, call_node, variable_ref_node, call_args, call_kw, trace_collection
    ):
        # Hard imports being called, generally have no problem with forward propagation.
        return self.computeExpressionCall(
            call_node=call_node,
            call_args=call_args,
            call_kw=call_kw,
            trace_collection=trace_collection,
        )


class ExpressionImportModuleNameHardExistsSpecificBase(
    ExpressionImportModuleNameHardExists
):
    """Base class for nodes that hard coded import names, e.g. of "importlib.import_module" name."""

    @staticmethod
    def getDetails():
        return {}
