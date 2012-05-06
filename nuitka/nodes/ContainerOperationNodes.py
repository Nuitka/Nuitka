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
""" Operations on Containers.

"""

from .NodeBases import CPythonExpressionChildrenHavingBase


class CPythonExpressionListOperationAppend( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_LIST_OPERATION_APPEND"

    named_children = ( "list", "value" )

    def __init__( self, liste, value, source_ref ):
        assert liste is not None
        assert value is not None

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "list"  : liste,
                "value" : value
            },
            source_ref = source_ref
        )

    getList = CPythonExpressionChildrenHavingBase.childGetter( "list" )
    getValue = CPythonExpressionChildrenHavingBase.childGetter( "value" )

    def computeNode( self, constraint_collection ):
        constraint_collection.removeKnowledge( self.getList() )

        return self, None, None


class CPythonExpressionSetOperationAdd( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_SET_OPERATION_ADD"

    named_children = ( "set", "value" )

    def __init__( self, sete, value, source_ref ):
        assert sete is not None
        assert value is not None

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "set"  : sete,
                "value" : value
            },
            source_ref = source_ref
        )

    getSet = CPythonExpressionChildrenHavingBase.childGetter( "set" )
    getValue = CPythonExpressionChildrenHavingBase.childGetter( "value" )

    def computeNode( self, constraint_collection ):
        constraint_collection.removeKnowledge( self.getSet() )

        return self, None, None


class CPythonExpressionDictOperationSet( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_DICT_OPERATION_SET"

    named_children = ( "dict", "key", "value" )

    def __init__( self, dicte, key, value, source_ref ):
        assert dicte is not None
        assert key is not None
        assert value is not None

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "dict"  : dicte,
                "key"   : key,
                "value" : value
            },
            source_ref = source_ref
        )

    getDict = CPythonExpressionChildrenHavingBase.childGetter( "dict" )
    getKey = CPythonExpressionChildrenHavingBase.childGetter( "key" )
    getValue = CPythonExpressionChildrenHavingBase.childGetter( "value" )

    def computeNode( self, constraint_collection ):
        constraint_collection.removeKnowledge( self.getDict() )

        return self, None, None
