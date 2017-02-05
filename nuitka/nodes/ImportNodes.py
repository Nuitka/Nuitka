#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nodes related to importing modules or names.

Normally imports are mostly relatively static, but Nuitka also attempts to
cover the uses of "__import__" built-in and other import techniques, that
allow dynamic values.

If other optimizations make it possible to predict these, the compiler can go
deeper that what it normally could. The import expression node can recurse. An
"__import__" built-in may be converted to it, once the module name becomes a
compile time constant.
"""

from logging import warning

from nuitka.__past__ import long, unicode  # pylint: disable=W0622
from nuitka.Builtins import calledWithBuiltinArgumentNamesDecorator
from nuitka.importing.Importing import (
    findModule,
    getModuleNameAndKindFromFilename
)
from nuitka.importing.Recursion import decideRecursion, recurseTo
from nuitka.importing.Whitelisting import getModuleWhiteList
from nuitka.utils import Utils

from .ExpressionBases import ExpressionChildrenHavingBase, ExpressionMixin
from .NodeBases import NodeBase, StatementChildrenHavingBase


class ExpressionImportModuleHard(NodeBase, ExpressionMixin):
    """ Hard code import, e.g. of "sys" module as done in Python mechanics.

    """
    kind = "EXPRESSION_IMPORT_MODULE_HARD"
    def __init__(self, module_name, import_name, source_ref):
        NodeBase.__init__(
            self,
            source_ref = source_ref
        )

        self.module_name = module_name
        self.import_name = import_name

    def getDetails(self):
        return {
            "module_name" : self.module_name,
            "import_name" : self.import_name
        }

    def getModuleName(self):
        return self.module_name

    def getImportName(self):
        return self.import_name

    def computeExpression(self, trace_collection):
        # TODO: May return a module reference of some sort in the future with
        # embedded modules.
        return self, None, None

    def mayHaveSideEffects(self):
        if self.module_name == "sys" and self.import_name == "stdout":
            return False
        elif self.module_name == "__future__":
            return False
        else:
            return True

    def mayRaiseException(self, exception_type):
        return self.mayHaveSideEffects()


class ExpressionBuiltinImport(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_BUILTIN_IMPORT"

    named_children = (
        "name", "globals", "locals", "fromlist", "level"
    )

    _warned_about = set()

    @calledWithBuiltinArgumentNamesDecorator
    def __init__(self, name, globals_arg, locals_arg, fromlist, level,
                source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "name"        : name,
                "globals"     : globals_arg,
                "locals"      : locals_arg,
                "fromlist"    : fromlist,
                "level"       : level
            },
            source_ref = source_ref
        )

        self.recurse_attempted = False
        self.imported_module = None
        self.import_list_modules = []
        self.finding = None

    getImportName = ExpressionChildrenHavingBase.childGetter("name")
    getFromList = ExpressionChildrenHavingBase.childGetter("fromlist")
    getGlobals = ExpressionChildrenHavingBase.childGetter("globals")
    getLocals = ExpressionChildrenHavingBase.childGetter("locals")
    getLevel = ExpressionChildrenHavingBase.childGetter("level")

    def _consider(self, trace_collection, module_filename, module_package):
        assert module_package is None or \
              (type(module_package) is str and module_package != "")

        module_filename = Utils.normpath(module_filename)

        module_name, module_kind = getModuleNameAndKindFromFilename(module_filename)

        if module_kind is not None:
            decision, reason = decideRecursion(
                module_filename = module_filename,
                module_name     = module_name,
                module_package  = module_package,
                module_kind     = module_kind
            )

            if decision:
                module_relpath = Utils.relpath(module_filename)

                imported_module, added_flag = recurseTo(
                    module_package  = module_package,
                    module_filename = module_filename,
                    module_relpath  = module_relpath,
                    module_kind     = module_kind,
                    reason          = reason
                )

                if added_flag:
                    trace_collection.signalChange(
                        "new_code",
                        imported_module.getSourceReference(),
                        "Recursed to module."
                    )

                return imported_module
            elif decision is None and module_kind == "py":
                if module_package is None:
                    module_fullpath = module_name
                else:
                    module_fullpath = module_package + '.' + module_name

                if module_filename not in self._warned_about and \
                   module_fullpath not in getModuleWhiteList():
                    self._warned_about.add(module_filename)

                    warning(
                        """\
Not recursing to '%(full_path)s' (%(filename)s), please specify \
--recurse-none (do not warn), \
--recurse-all (recurse to all), \
--recurse-not-to=%(full_path)s (ignore it), \
--recurse-to=%(full_path)s (recurse to it) to change.""" % {
                            "full_path" : module_fullpath,
                            "filename"  : module_filename
                        }
                    )

    def _attemptRecursion(self, trace_collection, module_name):
        # Complex stuff, pylint: disable=R0912

        parent_module = self.getParentModule()

        if parent_module.isCompiledPythonPackage():
            parent_package = parent_module.getFullName()
        else:
            parent_package = self.getParentModule().getPackage()

        level = self.getLevel()
        if level is None:
            level = 0 if self.source_ref.getFutureSpec().isAbsoluteImport() else -1
        elif not level.isCompileTimeConstant():
            return
        else:
            level = level.getCompileTimeConstant()

        # TODO: Catch this as a static error maybe.
        if type(level) not in (int, long):
            return

        module_package, module_filename, self.finding = findModule(
            importing      = self,
            module_name    = module_name,
            parent_package = parent_package,
            level          = level,
            warn           = True
        )

        if module_filename is not None:
            self.imported_module = self._consider(
                trace_collection = trace_collection,
                module_filename  = module_filename,
                module_package   = module_package
            )

            if self.imported_module is not None:
                import_list = self.getFromList()

                if import_list is not None:
                    if import_list.isCompileTimeConstant():
                        import_list = import_list.getCompileTimeConstant()

                    if type(import_list) not in (tuple, list):
                        import_list = None

                if import_list and \
                   self.imported_module.isCompiledPythonPackage():
                    for import_item in import_list:
                        if import_item == '*':
                            continue

                        module_package, module_filename, _finding = findModule(
                            importing      = self,
                            module_name    = import_item,
                            parent_package = self.imported_module.getFullName(),
                            level          = -1, # Relative import, so child is used.
                            warn           = False
                        )

                        if module_filename is not None:
                            sub_imported_module = self._consider(
                                trace_collection = trace_collection,
                                module_filename  = module_filename,
                                module_package   = module_package
                            )

                            if sub_imported_module is not None:
                                self.import_list_modules.append(
                                    sub_imported_module.getFullName()
                                )


    def computeExpression(self, trace_collection):
        # TODO: In fact, if the module is not a package, we don't have to insist
        # on the "fromlist" that much, but normally it's not used for anything
        # but packages, so it will be rare.
        # Attempt to recurse if not already done.
        if self.finding != "not-found":
            if self.imported_module is not None:
                trace_collection.onUsedModule(self.imported_module.getFullName())

            for import_list_module in self.import_list_modules:
                trace_collection.onUsedModule(import_list_module)

        if self.recurse_attempted:
            if self.finding == "not-found":
                # Importing and not finding, may raise an exception obviously.
                trace_collection.onExceptionRaiseExit(BaseException)
            else:
                # If we know it exists, only RuntimeError shall occur.
                trace_collection.onExceptionRaiseExit(RuntimeError)

            # We stay here.
            return self, None, None

        module_name = self.getImportName()

        if module_name.isCompileTimeConstant():
            imported_module_name = module_name.getCompileTimeConstant()

            if type(imported_module_name) in (str, unicode):
                self._attemptRecursion(
                    trace_collection = trace_collection,
                    module_name      = imported_module_name
                )

                self.recurse_attempted = True
            else:
                # TODO: This doesn't preserve side effects.

                # Non-strings is going to raise an error.
                new_node, change_tags, message = trace_collection.getCompileTimeComputationResult(
                    node        = self,
                    computation = lambda : __import__(module_name.getConstant()),
                    description = "Replaced '__import__' call with non-string module name argument."
                )

                # Must fail, must not go on when it doesn't.
                assert change_tags == "new_raise", module_name

                return new_node, change_tags, message

        # Importing may raise an exception obviously.
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: May return a module or module variable reference of some sort in
        # the future with embedded modules.
        return self, None, None


class StatementImportStar(StatementChildrenHavingBase):
    kind = "STATEMENT_IMPORT_STAR"

    named_children = ("module",)

    def __init__(self, module_import, source_ref):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "module" : module_import
            },
            source_ref = source_ref
        )

    getSourceModule = StatementChildrenHavingBase.childGetter("module")

    def computeStatement(self, trace_collection):
        trace_collection.onExpression(self.getSourceModule())

        # Need to invalidate everything, and everything could be assigned to
        # something else now.
        trace_collection.removeAllKnowledge()

        return self, None, None


class ExpressionImportName(ExpressionChildrenHavingBase):
    kind = "EXPRESSION_IMPORT_NAME"

    named_children = (
        "module",
    )

    def __init__(self, module, import_name, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "module" : module
            },
            source_ref = source_ref
        )

        self.import_name = import_name

        assert module is not None

    def getImportName(self):
        return self.import_name

    def getDetails(self):
        return {
            "import_name" : self.getImportName()
        }

    def getDetail(self):
        return "import %s from %s" % (
            self.getImportName(),
            self.getModule().getModuleName()
        )

    getModule = ExpressionChildrenHavingBase.childGetter("module")

    def computeExpression(self, trace_collection):
        # TODO: May return a module or module variable reference of some sort in
        # the future with embedded modules.

        # Importing may raise an exception obviously.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
