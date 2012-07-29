#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
""" Nodes for classes and their creations.

The classes are are at the core of the language and have their complexities.

"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from .FunctionNodes import CPythonExpressionFunctionCall

class CPythonExpressionClassDefinition( CPythonExpressionFunctionCall ):
    kind = "EXPRESSION_CLASS_DEFINITION"

    named_children = CPythonExpressionFunctionCall.named_children + \
                     ( "metaclass", "bases" )

    def __init__( self, class_definition, metaclass, bases, source_ref ):
        CPythonExpressionFunctionCall.__init__(
            self,
            function_body  = class_definition,
            values         = (),
            source_ref     = source_ref
        )

        self.setMetaclass( metaclass )
        self.setBases( bases )

    getBases = CPythonExpressionChildrenHavingBase.childGetter( "bases" )
    setBases = CPythonExpressionChildrenHavingBase.childSetter( "bases" )
    getMetaclass = CPythonExpressionChildrenHavingBase.childGetter( "metaclass" )
    setMetaclass = CPythonExpressionChildrenHavingBase.childSetter( "metaclass" )


class CPythonExpressionClassCreation( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_CLASS_CREATION"

    named_children = ( "class_dict", )

    def __init__( self, class_name, class_dict, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "class_dict" : class_dict
            },
            source_ref = source_ref
        )

        self.class_name = class_name

    def getDetails( self ):
        return {
            "class_name" : self.class_name
        }

    getClassDict = CPythonExpressionChildrenHavingBase.childGetter( "class_dict" )

    def getClassName( self ):
        return self.class_name

    def computeNode( self, constraint_collection ):
        # Class body is quite irreplacable. TODO: Not really, could be predictable as
        # a whole.
        return self, None, None


class CPythonExpressionBuiltinType3( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_TYPE3"

    named_children = ( "type_name", "bases", "dict" )

    def __init__( self, type_name, bases, type_dict, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "type_name" : type_name,
                "bases"     : bases,
                "dict"      : type_dict
            },
            source_ref = source_ref
        )

    getTypeName = CPythonExpressionChildrenHavingBase.childGetter( "type_name" )
    getBases = CPythonExpressionChildrenHavingBase.childGetter( "bases" )
    getDict = CPythonExpressionChildrenHavingBase.childGetter( "dict" )

    def computeNode( self, constraint_collection ):
        # TODO: Should be compile time computable if bases and dict are.

        return self, None, None
