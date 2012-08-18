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
""" Globals/locals/dir0 nodes

These nodes give access to variables, highly problematic, because using them, the code may
change or access anything about them, so nothing can be trusted anymore, if we start to
not know where their value goes.

"""


from .NodeBases import (
    CPythonNodeBase,
    CPythonExpressionMixin,
    CPythonExpressionBuiltinSingleArgBase
)


class CPythonExpressionBuiltinGlobals( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_BUILTIN_GLOBALS"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def computeNode( self, constraint_collection ):
        return self, None, None


class CPythonExpressionBuiltinLocals( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_BUILTIN_LOCALS"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def computeNode( self, constraint_collection ):
        return self, None, None

    def needsLocalsDict( self ):
        return self.getParentVariableProvider().isEarlyClosure()


class CPythonExpressionBuiltinDir0( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_BUILTIN_DIR0"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def computeNode( self, constraint_collection ):
        return self, None, None


class CPythonExpressionBuiltinDir1( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_DIR1"

    def computeNode( self, constraint_collection ):
        # TODO: Quite some cases should be possible to predict.
        return self, None, None
