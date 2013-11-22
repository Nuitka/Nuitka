#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
cover the uses of "__import__" builtin and other import techniques, that
allow dynamic values.

If other optimizations make it possible to predict these, the compiler can go
deeper that what it normally could. The import expression node can recurse. An
"__import__" builtin may be converted to it, once the module name becomes a
compile time constant.
"""

from .NodeBases import ExpressionChildrenHavingBase, StatementChildrenHavingBase

from .ConstantRefNodes import ExpressionConstantRef

from nuitka import Importing, Utils, Options

from logging import warning

class ExpressionImportModule( ExpressionChildrenHavingBase ):
    kind = "EXPRESSION_IMPORT_MODULE"

    named_children = ( "module", )

    # Set of modules, that we failed to import, and gave warning to the user
    # about it.
    _warned_about = set()

    def __init__( self, module_name, import_list, level, source_ref ):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "module" : None
            },
            source_ref = source_ref
        )

        self.module_name = module_name
        self.import_list = import_list
        self.level = level

        self.attempted_recurse = False
        self.found_modules = ()

    def getDetails( self ):
        return {
            "module_name" : self.module_name,
            "level"       : self.level
        }

    def getModuleName( self ):
        return self.module_name

    def getImportList( self ):
        return self.import_list

    def getLevel( self ):
        if self.level == 0:
            if self.source_ref.getFutureSpec().isAbsoluteImport():
                return 0
            else:
                return -1
        else:
            return self.level

    # Prevent normal recursion from entering the module. TODO: Why have the
    # class when not really using it.
    def getVisitableNodes( self ):
        return ()

    # TODO: No need for these accessor functions anymore.
    def hasAttemptedRecurse( self ):
        return self.attempted_recurse

    def setAttemptedRecurse( self ):
        self.attempted_recurse = True

    getModule = ExpressionChildrenHavingBase.childGetter( "module" )
    _setModule = ExpressionChildrenHavingBase.childSetter( "module" )

    def setModule( self, module ):
        # Modules have no parent.
        assert module.parent is None
        self._setModule( module )
        module.parent = None

    @staticmethod
    def _decide( module_filename, module_name, module_package ):
        # Many branches, which make decisions immediately, pylint: disable=R0911

        no_case_modules = Options.getShallFollowInNoCase()

        if module_package is None:
            full_name = module_name
        else:
            full_name = module_package + "." + module_name

        for no_case_module in no_case_modules:
            if full_name == no_case_module:
                return (
                    False,
                    "Module listed explicitely to not recurse to."
                )

            if full_name.startswith( no_case_module + "." ):
                return (
                    False,
                    "Module in package listed explicitely to not recurse to."
                )

        any_case_modules = Options.getShallFollowModules()

        for any_case_module in any_case_modules:
            if full_name == any_case_module:
                return (
                    True,
                    "Module listed explicitely to recurse to."
                )

            if full_name.startswith( any_case_module + "." ):
                return (
                    True,
                    "Module in package listed explicitely to recurse to."
                )

        if Options.shallFollowNoImports():
            return (
                False,
                "Requested to not recurse at all."
            )

        if Importing.isStandardLibraryPath( module_filename ):
            return (
                Options.shallFollowStandardLibrary(),
                "Requested to %srecurse to standard library." % (
                    "" if Options.shallFollowStandardLibrary() else "not "
                )
            )

        if Options.shallFollowAllImports():
            return (
                True,
                "Requested to recurse to all non-standard library modules."
            )

        # Means, we were not given instructions how to handle things.
        return (
            None,
            "Default behaviour, not recursing without request."
        )

    def _consider( self, constraint_collection, module_filename,
                   module_package ):
        assert module_package is None or \
              ( type( module_package ) is str and module_package != "" )

        module_filename = Utils.normpath( module_filename )

        if Utils.isDir( module_filename ):
            module_name = Utils.basename( module_filename )
        elif module_filename.endswith( ".py" ):
            module_name = Utils.basename( module_filename )[:-3]
        elif module_filename.endswith( ".so" ) or \
             module_filename.endswith( ".pyd" ):
            # Remember the list of used shared library modules separately, and
            # then act as if they were not found, because there is not much we
            # can say about them. TODO: We might one day have module-alike
            # objects that can provide information about some of them, once we
            # have that for Python modules.

            from nuitka.ModuleRegistry import addSharedLibrary
            addSharedLibrary( module_filename )

            module_name = None
        else:
            module_name = None

        if module_name is not None:
            decision, reason = self._decide(
                module_filename = module_filename,
                module_name     = module_name,
                module_package  = module_package
            )

            if decision:
                module_relpath = Utils.relpath( module_filename )

                from nuitka.tree import Recursion

                imported_module, added_flag = Recursion.recurseTo(
                    module_package  = module_package,
                    module_filename = module_filename,
                    module_relpath  = module_relpath,
                    reason          = reason
                )

                if added_flag:
                    constraint_collection.signalChange(
                        "new_code",
                        imported_module.getSourceReference(),
                        "Recursed to module."
                    )
            elif decision is None:
                if module_package is None:
                    module_fullpath = module_name
                else:
                    module_fullpath = module_package + "." + module_name

                if module_filename not in self._warned_about:
                    self._warned_about.add( module_filename )

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

    def _attemptRecursion( self, constraint_collection ):
        assert self.getModule() is None

        parent_module = self.getParentModule()

        if parent_module.isPythonPackage():
            parent_package = parent_module.getFullName()
        else:
            parent_package = self.getParentModule().getPackage()

        module_package, _module_name, module_filename = Importing.findModule(
            source_ref     = self.source_ref,
            module_name    = self.getModuleName(),
            parent_package = parent_package,
            level          = self.getLevel(),
            warn           = True
        )

        # That would be an illegal package name, catch it.
        assert module_package != ""

        if module_filename is not None:
            imported_module = self._consider(
                constraint_collection = constraint_collection,
                module_filename       = module_filename,
                module_package        = module_package
            )

            if imported_module is not None:
                self.setModule( imported_module )
                self.found_modules = []

                import_list = self.getImportList()

                if import_list and imported_module.isPythonPackage():
                    for import_item in import_list:

                        module_package, _module_name, module_filename = \
                          Importing.findModule(
                            source_ref     = self.source_ref,
                            module_name    = import_item,
                            parent_package = imported_module.getFullName(),
                            level          = -1,
                            warn           = False
                        )

                        if module_filename is not None:
                            sub_imported_module = self._consider(
                                constraint_collection = constraint_collection,
                                module_filename       = module_filename,
                                module_package        = module_package
                            )

                            if sub_imported_module is not None:
                                self.found_modules.append( sub_imported_module )


    def computeExpression( self, constraint_collection ):
        # Attempt to recurse if not already done.
        if not self.hasAttemptedRecurse():
            self._attemptRecursion(
                constraint_collection = constraint_collection
            )

            self.setAttemptedRecurse()

        if self.getModule() is not None:
            from nuitka.ModuleRegistry import addUsedModule
            addUsedModule( self.getModule() )

            for found_module in self.found_modules:
                addUsedModule( found_module )

        # TODO: May return a module reference of some sort in the future with
        # embedded modules.
        return self, None, None


class ExpressionBuiltinImport( ExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_IMPORT"

    named_children = ( "import_name", "globals", "locals", "fromlist", "level" )

    def __init__( self, name, import_globals, import_locals, fromlist, level,
                  source_ref ):
        if fromlist is None:
            fromlist = ExpressionConstantRef(
                constant   = [],
                source_ref = source_ref
            )

        if level is None:
            level = 0 if source_ref.getFutureSpec().isAbsoluteImport() else -1

            level = ExpressionConstantRef(
                constant   = level,
                source_ref = source_ref
            )

        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "import_name" : name,
                "globals"     : import_globals,
                "locals"      : import_locals,
                "fromlist"    : fromlist,
                "level"       : level
            },
            source_ref = source_ref
        )

    getImportName = ExpressionChildrenHavingBase.childGetter( "import_name" )
    getFromList = ExpressionChildrenHavingBase.childGetter( "fromlist" )
    getGlobals = ExpressionChildrenHavingBase.childGetter( "globals" )
    getLocals = ExpressionChildrenHavingBase.childGetter( "locals" )
    getLevel = ExpressionChildrenHavingBase.childGetter( "level" )

    def computeExpression( self, constraint_collection ):
        module_name = self.getImportName()
        fromlist = self.getFromList()
        level = self.getLevel()

        # TODO: In fact, if the module is not a package, we don't have to insist
        # on the fromlist that much, but normally it's not used for anything but
        # packages, so it will be rare.

        if module_name.isExpressionConstantRef() and \
           fromlist.isExpressionConstantRef() and \
           level.isExpressionConstantRef():
            new_node = ExpressionImportModule(
                module_name = module_name.getConstant(),
                import_list = fromlist.getConstant(),
                level       = level.getConstant(),
                source_ref  = self.getSourceReference()
            )

            return (
                new_node,
                "new_import",
                "Replaced __import__ call with module import expression."
            )

        # TODO: May return a module or module variable reference of some sort in
        # the future with embedded modules.
        return self, None, None


class StatementImportStar( StatementChildrenHavingBase ):
    kind = "STATEMENT_IMPORT_STAR"

    named_children = ( "module", )

    def __init__( self, module_import, source_ref ):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "module" : module_import
            },
            source_ref = source_ref
        )

    getModule = StatementChildrenHavingBase.childGetter( "module" )

    def computeStatement( self, constraint_collection ):
        constraint_collection.onExpression( self.getModule() )

        # Need to invalidate everything, and everything could be assigned to
        # something else now.
        constraint_collection.removeAllKnowledge()

        return self, None, None


class ExpressionImportName( ExpressionChildrenHavingBase ):
    kind = "EXPRESSION_IMPORT_NAME"

    named_children = ( "module", )

    def __init__( self, module, import_name, source_ref ):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "module" : module
            },
            source_ref = source_ref
        )

        self.import_name = import_name

    def getImportName( self ):
        return self.import_name

    def getDetails( self ):
        return { "import_name" : self.getImportName() }

    def getDetail( self ):
        return "import %s from %s" % ( self.getImportName(), self.getModule() )

    getModule = ExpressionChildrenHavingBase.childGetter( "module" )

    def computeExpression( self, constraint_collection ):
        # TODO: May return a module or module variable reference of some sort in
        # the future with embedded modules.
        return self, None, None
