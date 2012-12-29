#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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

"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from .ConstantRefNode import CPythonExpressionConstantRef

class CPythonExpressionImportModule( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_IMPORT_MODULE"

    named_children = ( "module", )

    def __init__( self, module_name, import_list, level, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
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
            return 0 if self.source_ref.getFutureSpec().isAbsoluteImport() else -1
        else:
            return self.level

    # Prevent normal recursion from entering the module.
    def getVisitableNodes( self ):
        return ()

    def hasAttemptedRecurse( self ):
        return self.attempted_recurse

    def setAttemptedRecurse( self ):
        self.attempted_recurse = True

    getModule = CPythonExpressionChildrenHavingBase.childGetter( "module" )
    _setModule = CPythonExpressionChildrenHavingBase.childSetter( "module" )

    def setModule( self, module ):
        # Modules have no parent.
        assert module.parent is None
        self._setModule( module )
        module.parent = None

    def computeNode( self, constraint_collection ):
        # TODO: May return a module reference of some sort in the future with embedded
        # modules.
        return self, None, None


class CPythonExpressionBuiltinImport( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_IMPORT"

    named_children = ( "import_name", "globals", "locals", "fromlist", "level" )

    def __init__( self, name, import_globals, import_locals, fromlist, level, source_ref ):
        if fromlist is None:
            fromlist = CPythonExpressionConstantRef(
                constant   = [],
                source_ref = source_ref
            )

        if level is None:
            level = CPythonExpressionConstantRef(
                constant   = 0 if source_ref.getFutureSpec().isAbsoluteImport() else -1,
                source_ref = source_ref
            )

        CPythonExpressionChildrenHavingBase.__init__(
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

    getImportName = CPythonExpressionChildrenHavingBase.childGetter( "import_name" )
    getFromList = CPythonExpressionChildrenHavingBase.childGetter( "fromlist" )
    getGlobals = CPythonExpressionChildrenHavingBase.childGetter( "globals" )
    getLocals = CPythonExpressionChildrenHavingBase.childGetter( "locals" )
    getLevel = CPythonExpressionChildrenHavingBase.childGetter( "level" )

    def computeNode( self, constraint_collection ):
        module_name = self.getImportName()
        fromlist = self.getFromList()
        level = self.getLevel()

        # TODO: In fact, if the module is not a package, we don't have to insist on the
        # fromlist that much, but normally it's not used for anything but packages, so
        # it will be rare.

        if module_name.isExpressionConstantRef() and fromlist.isExpressionConstantRef() \
             and level.isExpressionConstantRef():
            new_node = CPythonExpressionImportModule(
                module_name = module_name.getConstant(),
                import_list = fromlist.getConstant(),
                level       = level.getConstant(),
                source_ref  = self.getSourceReference()
            )

            return new_node, "new_import", "Replaced __import__ call with module import expression."

        # TODO: May return a module or module variable reference of some sort in the
        # future with embedded modules.
        return self, None, None


class CPythonStatementImportStar( CPythonExpressionChildrenHavingBase ):
    kind = "STATEMENT_IMPORT_STAR"

    named_children = ( "module", )

    def __init__( self, module_import, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "module" : module_import
            },
            source_ref = source_ref
        )

    getModule = CPythonExpressionChildrenHavingBase.childGetter( "module" )


class CPythonExpressionImportName( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_IMPORT_NAME"

    named_children = ( "module", )

    def __init__( self, module, import_name, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
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

    getModule = CPythonExpressionChildrenHavingBase.childGetter( "module" )

    def computeNode( self, constraint_collection ):
        # TODO: May return a module or module variable reference of some sort in the
        # future with embedded modules.
        return self, None, None
