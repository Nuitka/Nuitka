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
""" Operations on Containers.

"""

from .NodeBases import CPythonExpressionChildrenHavingBase, CPythonChildrenHaving, CPythonNodeBase


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


class CPythonStatementDictOperationRemove( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_DICT_OPERATION_REMOVE"

    named_children = ( "dict", "key" )

    def __init__( self, dicte, key, source_ref ):
        assert dicte is not None
        assert key is not None

        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values     = {
                "dict"    : dicte,
                "key"     : key,
            }
        )

    getDict = CPythonExpressionChildrenHavingBase.childGetter( "dict" )
    getKey = CPythonExpressionChildrenHavingBase.childGetter( "key" )


class CPythonExpressionDictOperationGet( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_DICT_OPERATION_GET"

    named_children = ( "dict", "key" )

    def __init__( self, dicte, key, source_ref ):
        assert dicte is not None
        assert key is not None

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "dict" : dicte,
                "key"  : key,
            },
            source_ref = source_ref
        )

    getDict = CPythonExpressionChildrenHavingBase.childGetter( "dict" )
    getKey = CPythonExpressionChildrenHavingBase.childGetter( "key" )

    def computeNode( self, constraint_collection ):
        return self, None, None
