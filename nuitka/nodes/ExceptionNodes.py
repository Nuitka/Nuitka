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
""" Nodes related to raising and making exceptions.

"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonExpressionMixin,
    CPythonChildrenHaving,
    CPythonNodeBase
)

class CPythonStatementRaiseException( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_RAISE_EXCEPTION"

    named_children = ( "exception_type", "exception_value", "exception_trace" )

    def __init__( self, exception_type, exception_value, exception_trace, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        if exception_type is None:
            assert exception_value is None

        if exception_value is None:
            assert exception_trace is None

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "exception_type"  : exception_type,
                "exception_value" : exception_value,
                "exception_trace" : exception_trace,
            }
        )

        self.reraise_local = False

    getExceptionType = CPythonChildrenHaving.childGetter( "exception_type" )
    getExceptionValue = CPythonChildrenHaving.childGetter( "exception_value" )
    getExceptionTrace = CPythonChildrenHaving.childGetter( "exception_trace" )

    def isReraiseException( self ):
        return self.getExceptionType() is None

    def isReraiseExceptionLocal( self ):
        assert self.isReraiseException()

        return self.reraise_local

    def markAsReraiseLocal( self ):
        self.reraise_local = True

    def isStatementAbortative( self ):
        return True

    def needsLineNumber( self ):
        return not self.isReraiseException()


class CPythonExpressionRaiseException( CPythonExpressionChildrenHavingBase ):
    """ This node type is only produced via optimization.

    CPython only knows exception raising as a statement, but often the raising
    of exceptions can be predicted to occur as part of an expression, which it
    replaces then.

    The side_effects is there, to represent that an exception is to be raised
    after doing certain things first.
    """

    kind = "EXPRESSION_RAISE_EXCEPTION"

    named_children = ( "exception_type", "exception_value" )

    def __init__( self, exception_type, exception_value, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "exception_type"  : exception_type,
                "exception_value" : exception_value
            },
            source_ref = source_ref
        )

    getExceptionType = CPythonExpressionChildrenHavingBase.childGetter( "exception_type" )
    getExceptionValue = CPythonExpressionChildrenHavingBase.childGetter( "exception_value" )
    def computeNode( self, constraint_collection ):
        return self, None, None


class CPythonExpressionBuiltinMakeException( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_MAKE_EXCEPTION"

    named_children = ( "args", )

    def __init__( self, exception_name, args, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "args" : tuple( args ),
            },
            source_ref = source_ref
        )

        self.exception_name = exception_name

    def getDetails( self ):
        return { "exception_name" : self.exception_name }

    def getExceptionName( self ):
        return self.exception_name

    getArgs = CPythonExpressionChildrenHavingBase.childGetter( "args" )

    def computeNode( self, constraint_collection ):
        return self, None, None


class CPythonExpressionCaughtExceptionTypeRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_TYPE_REF"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def computeNode( self, constraint_collection ):
        # TODO: Might be predictable based on the exception handler this is in.
        return self, None, None

    def mayHaveSideEffects( self, constraint_collection ):
        # Referencing the expression type has no side effect
        return False


class CPythonExpressionCaughtExceptionValueRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_VALUE_REF"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def computeNode( self, constraint_collection ):
        # TODO: Might be predictable based on the exception handler this is in.
        return self, None, None

    def mayHaveSideEffects( self, constraint_collection ):
        # Referencing the expression type has no side effect
        return False

    def makeCloneAt( self, source_ref ):
        return CPythonExpressionCaughtExceptionValueRef(
            source_ref = source_ref
        )


class CPythonExpressionCaughtExceptionTracebackRef( CPythonNodeBase, CPythonExpressionMixin ):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_TRACEBACK_REF"

    def __init__( self, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

    def computeNode( self, constraint_collection ):
        return self, None, None

    def mayHaveSideEffects( self, constraint_collection ):
        # Referencing the expression type has no side effect
        return False
