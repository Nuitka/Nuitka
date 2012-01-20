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

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase

class CPythonExpressionImportModule( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_IMPORT_MODULE"

    named_children = ( "module", )

    def __init__( self, module_name, import_list, level, source_ref ):
        CPythonChildrenHaving.__init__(
            self,
            values = {
                "module" : None
            }
        )

        CPythonNodeBase.__init__( self, source_ref = source_ref )

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

    getModule = CPythonChildrenHaving.childGetter( "module" )
    setModule = CPythonChildrenHaving.childSetter( "module" )


class CPythonStatementImportStar( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_IMPORT_STAR"

    named_children = ( "module", )

    def __init__( self, module_import, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "module" : module_import
            }
        )

    getModule = CPythonChildrenHaving.childGetter( "module" )


class CPythonExpressionImportName( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_IMPORT_NAME"

    named_children = ( "module", )

    def __init__( self, module, import_name, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "module" : module
            }
        )

        self.import_name = import_name

    def getImportName( self ):
        return self.import_name

    def getDetails( self ):
        return { "import_name" : self.getImportName() }

    def getDetail( self ):
        return "import %s from %s" % ( self.getImportName(), self.getModule() )

    getModule = CPythonChildrenHaving.childGetter( "module" )
