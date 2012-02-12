#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
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

    # TODO: visitForest should see the module if any.
    def getVisitableNodes( self ):
        return ()

    def hasAttemptedRecurse( self ):
        return self.attempted_recurse

    def setAttemptedRecurse( self ):
        self.attempted_recurse = True

    getModule = CPythonExpressionChildrenHavingBase.childGetter( "module" )
    setModule = CPythonExpressionChildrenHavingBase.childSetter( "module" )

    def computeNode( self ):
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

    def computeNode( self ):
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

    def computeNode( self ):
        # TODO: May return a module or module variable reference of some sort in the
        # future with embedded modules.
        return self, None, None
