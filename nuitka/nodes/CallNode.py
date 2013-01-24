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
""" Call node

Function calls and generally calling expressions are the same thing. This is very
important, because it allows to predict most things, and avoid expensive operations like
parameter parsing at run time.

There will be a method "computeNodeCall" to aid predicting them.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase

from .ConstantRefNode import CPythonExpressionConstantRef


class CPythonExpressionCall( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_CALL"

    named_children = ( "called", "args", "kw" )

    def __init__( self, called, args, kw, source_ref ):
        assert called.isExpression()
        assert args.isExpression()
        assert kw.isExpression()

        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "called" : called,
                "args"   : args,
                "kw"     : kw,
            },
            source_ref = source_ref
        )

    getCalled = CPythonExpressionChildrenHavingBase.childGetter( "called" )
    getCallArgs = CPythonExpressionChildrenHavingBase.childGetter( "args" )
    getCallKw = CPythonExpressionChildrenHavingBase.childGetter( "kw" )

    def isExpressionCall( self ):
        return True

    def computeNode( self, constraint_collection ):
        return self.getCalled().computeNodeCall(
            call_node             = self,
            constraint_collection = constraint_collection
        )

    def extractPreCallSideEffects( self ):
        args = self.getCallArgs()
        kw = self.getCallKw()

        return args.extractSideEffects() + kw.extractSideEffects()


class CPythonExpressionCallNoKeywords( CPythonExpressionCall ):
    kind = "EXPRESSION_CALL_NO_KEYWORDS"

    named_children = ( "called", "args", "kw" )

    def __init__( self, called, args, source_ref ):
        assert called.isExpression()

        CPythonExpressionCall.__init__(
            self,
            called = called,
            args   = args,
            kw     = CPythonExpressionConstantRef(
                constant   = {},
                source_ref = source_ref,
            ),
            source_ref = source_ref
        )

class CPythonExpressionCallKeywordsOnly( CPythonExpressionCall ):
    kind = "EXPRESSION_CALL_KEYWORDS_ONLY"

    named_children = ( "called", "args", "kw" )

    def __init__( self, called, kw, source_ref ):
        assert called.isExpression()

        CPythonExpressionCall.__init__(
            self,
            called = called,
            args   = CPythonExpressionConstantRef(
                constant   = (),
                source_ref = source_ref,
            ),
            kw     = kw,
            source_ref = source_ref
        )


class CPythonExpressionCallEmpty( CPythonExpressionCall ):
    kind = "EXPRESSION_CALL_EMPTY"

    named_children = ( "called", "args", "kw" )

    def __init__( self, called, source_ref ):
        assert called.isExpression()

        CPythonExpressionCall.__init__(
            self,
            called = called,
            args   = CPythonExpressionConstantRef(
                constant   = (),
                source_ref = source_ref
            ),
            kw     = CPythonExpressionConstantRef(
                constant   = {},
                source_ref = source_ref,
            ),
            source_ref = source_ref
        )
