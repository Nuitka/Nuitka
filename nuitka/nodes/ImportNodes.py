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
""" Nodes related to importing modules or names.

Normally imports are mostly relatively static, but Nuitka also attempts to
cover the uses of "__import__" built-in and other import techniques, that
allow dynamic values.

If other optimizations make it possible to predict these, the compiler can go
deeper that what it normally could. The import expression node can recurse.
"""

import os
from logging import warning

from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
    long,
    unicode
)
from nuitka.Builtins import calledWithBuiltinArgumentNamesDecorator
from nuitka.importing.Importing import (
    findModule,
    getModuleNameAndKindFromFilename
)
from nuitka.importing.Recursion import decideRecursion, recurseTo
from nuitka.importing.Whitelisting import getModuleWhiteList
from nuitka.utils.FileOperations import relpath

from .ExpressionBases import (
    ExpressionBase,
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase
)
from .NodeBases import StatementChildHavingBase
from .shapes.BuiltinTypeShapes import ShapeTypeBuiltinModule, ShapeTypeModule


class ExpressionImportModuleHard(ExpressionBase):
    """ Hard coded import names, e.g. of "__future__"

        These are directly created for some Python mechanics, but also due to
        compile time optimization for imports of statically known modules.
    """

    kind = "EXPRESSION_IMPORT_MODULE_HARD"

    __slots__ = ("module_name",)

    def __init__(self, module_name, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

        self.module_name = module_name

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {
            "module_name" : self.module_name
        }

    def getModuleName(self):
        return self.module_name

    def computeExpressionRaw(self, trace_collection):
        return self, None, None

    def mayHaveSideEffects(self):
        if self.module_name == "sys":
            return False
        elif self.module_name == "__future__":
            return False
        else:
            return True

    def mayRaiseException(self, exception_type):
        return self.mayHaveSideEffects()


class ExpressionImportModuleNameHard(ExpressionBase):
    """ Hard coded import names, e.g. of "os.path.dirname"

        These are directly created for some Python mechanics.
    """

    kind = "EXPRESSION_IMPORT_MODULE_NAME_HARD"

    __slots__ = "module_name", "import_name"

    def __init__(self, module_name, import_name, source_ref):
        ExpressionBase.__init__(
            self,
            source_ref = source_ref
        )

        self.module_name = module_name
        self.import_name = import_name

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {
            "module_name" : self.module_name,
            "import_name" : self.import_name
        }

    def getModuleName(self):
        return self.module_name

    def getImportName(self):
        return self.import_name

    def computeExpressionRaw(self, trace_collection):
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
                "name"     : name,
                "globals"  : globals_arg,
                "locals"   : locals_arg,
                "fromlist" : fromlist,
                "level"    : level
            },
            source_ref = source_ref
        )

        self.recurse_attempted = False

        # The module actually referenced in that import.
        self.imported_module = None

        # The fromlist imported modules if any.
        self.import_list_modules = []

        # For "package.sub_package.module" we also need to import the package,
        # because the imported_module not be found, as it's not a module, e.g.
        # in the case of "os.path" or "six.moves".
        self.package_modules = None

        self.finding = None

        self.type_shape = ShapeTypeModule

        self.builtin_module = None

    getImportName = ExpressionChildrenHavingBase.childGetter("name")
    getFromList = ExpressionChildrenHavingBase.childGetter("fromlist")
    getGlobals = ExpressionChildrenHavingBase.childGetter("globals")
    getLocals = ExpressionChildrenHavingBase.childGetter("locals")
    getLevel = ExpressionChildrenHavingBase.childGetter("level")

    def _consider(self, trace_collection, module_filename, module_package):
        assert module_package is None or \
              (type(module_package) is str and module_package != ""), repr(module_package)

        module_filename = os.path.normpath(module_filename)

        module_name, module_kind = getModuleNameAndKindFromFilename(module_filename)

        if module_kind is not None:
            decision, reason = decideRecursion(
                module_filename = module_filename,
                module_name     = module_name,
                module_package  = module_package,
                module_kind     = module_kind
            )

            if decision:
                module_relpath = relpath(module_filename)

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
--nofollow-imports (do not warn), \
--follow-imports (recurse to all), \
--nofollow-import-to=%(full_path)s (ignore it), \
--follow-import-to=%(full_path)s (recurse to it) to change.""" % {
                            "full_path" : module_fullpath,
                            "filename"  : module_filename
                        }
                    )

    def _attemptRecursion(self, trace_collection, module_name):
        # Complex stuff, pylint: disable=too-many-branches

        parent_module = self.getParentModule()

        if parent_module.isCompiledPythonPackage():
            parent_package = parent_module.getFullName()
        else:
            parent_package = self.getParentModule().getPackage()

        level = self.getLevel()

        if level is None:
            level = 0 if parent_module.getFutureSpec().isAbsoluteImport() else -1
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
        else:
            while '.' in module_name:
                module_name = '.'.join(module_name.split('.')[:-1])

                module_package, module_filename, _finding = findModule(
                    importing      = self,
                    module_name    = module_name,
                    parent_package = parent_package,
                    level          = level,
                    warn           = True
                )

                if module_filename is not None:
                    package_module = self._consider(
                        trace_collection = trace_collection,
                        module_filename  = module_filename,
                        module_package   = module_package
                    )

                    if package_module is not None:
                        if self.package_modules is None:
                            self.package_modules = []

                        self.package_modules.append(package_module)


    def _addUsedModules(self, trace_collection):
        if self.finding != "not-found":
            if self.imported_module is not None:
                trace_collection.onUsedModule(self.imported_module.getFullName())

            for import_list_module in self.import_list_modules:
                trace_collection.onUsedModule(import_list_module)

        # These are added in any case.
        if self.package_modules is not None:
            for package_module in self.package_modules:
                trace_collection.onUsedModule(package_module.getFullName())



    def computeExpression(self, trace_collection):
        # TODO: In fact, if the module is not a package, we don't have to insist
        # on the "fromlist" that much, but normally it's not used for anything
        # but packages, so it will be rare.
        self._addUsedModules(trace_collection)

        # Attempt to recurse if not already done.
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
                # TODO: This is not handling decoding errors all that well.
                if str is not unicode and type(imported_module_name) is unicode:
                    imported_module_name = str(imported_module_name)


                self._attemptRecursion(
                    trace_collection = trace_collection,
                    module_name      = imported_module_name
                )

                self.recurse_attempted = True

                if self.finding == "built-in":
                    self.type_shape = ShapeTypeBuiltinModule
                    self.builtin_module = __import__(imported_module_name)

                self._addUsedModules(trace_collection)
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

        # Importing may raise an exception obviously, unless we know it will
        # not.
        if self.finding != "built-in":
            trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: May return a module or module variable reference of some sort in
        # the future with embedded modules.
        return self, None, None

    # TODO: Add computeExpressionImportName

    def mayRaiseException(self, exception_type):
        return self.finding != "built-in"

    def mayRaiseExceptionImportName(self, exception_type, import_name):
        if self.finding == "built-in":
            return not hasattr(self.builtin_module, import_name)
        else:
            return True

    def getTypeShape(self):
        return self.type_shape


class StatementImportStar(StatementChildHavingBase):
    kind = "STATEMENT_IMPORT_STAR"

    named_child = "module"

    __slots__ = ("locals_scope",)

    def __init__(self, locals_scope, module_import, source_ref):
        StatementChildHavingBase.__init__(
            self,
            value      = module_import,
            source_ref = source_ref
        )

        self.locals_scope = locals_scope

    getSourceModule = StatementChildHavingBase.childGetter("module")

    def getLocalsDictScope(self):
        return self.locals_scope

    def computeStatement(self, trace_collection):
        trace_collection.onExpression(self.getSourceModule())

        trace_collection.onLocalsDictEscaped(self.locals_scope)

        # Need to invalidate everything, and everything could be assigned to
        # something else now.
        trace_collection.removeAllKnowledge()

        # We could always encounter that __all__ is a strange beast and causes
        # the exception.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def mayRaiseException(self, exception_type):
        # Not done. TODO: Later we can try and check for "__all__" if it
        # really can be that way.
        return True

    def getStatementNiceName(self):
        return "star import statement"


class ExpressionImportName(ExpressionChildHavingBase):
    kind = "EXPRESSION_IMPORT_NAME"

    named_child = "module"

    __slots__ = ("import_name", "level")

    def __init__(self, module, import_name, level, source_ref):
        ExpressionChildHavingBase.__init__(
            self,
            value      = module,
            source_ref = source_ref
        )

        self.import_name = import_name
        self.level = level

        assert module is not None

    def getImportName(self):
        return self.import_name

    def getImportLevel(self):
        return self.level

    def getDetails(self):
        return {
            "import_name" : self.getImportName(),
            "level"       : self.level
        }

    def getDetail(self):
        return "import %s from %s" % (
            self.getImportName(),
            self.getModule().getModuleName()
        )

    getModule = ExpressionChildrenHavingBase.childGetter("module")

    def computeExpression(self, trace_collection):
        return self.getModule().computeExpressionImportName(
            import_node      = self,
            import_name      = self.import_name,
            trace_collection = trace_collection
        )

    def mayRaiseException(self, exception_type):
        return self.getModule().mayRaiseExceptionImportName(
            exception_type = exception_type,
            import_name    = self.import_name
        )
