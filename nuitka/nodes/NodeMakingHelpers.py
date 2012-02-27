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
""" These are just helpers to create nodes, often to replace existing nodes

These are for use in optimizations and computations, and therefore cover mostly exceptions
and constants. Otherwise the thread of cyclic dependency kicks in.
"""

from .ConstantRefNode import CPythonExpressionConstantRef

from .BuiltinReferenceNodes import (
    CPythonExpressionBuiltinExceptionRef,
    CPythonExpressionBuiltinRef
)

from .ExceptionNodes import (
    CPythonExpressionRaiseException,
    CPythonStatementRaiseException
)

from .StatementNodes import (
    CPythonStatementExpressionOnly,
    CPythonStatementsSequence
)

def makeConstantReplacementNode( constant, node ):
    return CPythonExpressionConstantRef(
        constant   = constant,
        source_ref = node.getSourceReference()
    )

def makeBuiltinExceptionRefReplacementNode( exception_name, node ):
    return CPythonExpressionBuiltinExceptionRef(
        exception_name = exception_name,
        source_ref     = node.getSourceReference()
    )

def makeBuiltinRefReplacementNode( builtin_name, node ):
    return CPythonExpressionBuiltinRef(
        builtin_name = builtin_name,
        source_ref   = node.getSourceReference()
    )

def makeRaiseExceptionReplacementExpression( expression, exception_type, exception_value ):
    source_ref = expression.getSourceReference()

    assert type( exception_type ) is str

    result = CPythonExpressionRaiseException(
        exception_type  = CPythonExpressionBuiltinExceptionRef(
            exception_name = exception_type,
            source_ref     = source_ref
        ),
        exception_value = makeConstantReplacementNode(
            constant = exception_value,
            node     = expression
        ),
        side_effects    = (),
        source_ref      = source_ref
    )

    return result

def makeRaiseExceptionReplacementExpressionFromInstance( expression, exception ):
    assert isinstance( exception, Exception )

    args = exception.args
    assert type( args ) is tuple and len( args ) == 1, args

    return makeRaiseExceptionReplacementExpression(
        expression      = expression,
        exception_type  = exception.__class__.__name__,
        exception_value = args[0]
    )

def getComputationResult( node, computation, description ):
    """ With a computation function, execute it and return the constant result or
        exception node.

    """

    # Try and turn raised exceptions into static raises. pylint: disable=W0703
    try:
        result = computation()
    except Exception as e:
        new_node = makeRaiseExceptionReplacementExpressionFromInstance(
            expression = node,
            exception  = e
        )

        change_tags = "new_raise"
        change_desc = description + " was predicted to raise an exception."
    else:
        new_node = makeConstantReplacementNode(
            constant = result,
            node     = node
        )

        change_tags = "new_constant"
        change_desc = description + " was predicted to constant result."

    return new_node, change_tags, change_desc

def makeRaiseExceptionReplacementStatement( statement, exception_type, exception_value ):
    source_ref = statement.getSourceReference()

    assert type( exception_type ) is str

    result = CPythonStatementRaiseException(
        exception_type  = makeBuiltinExceptionRefReplacementNode(
            exception_name = exception_type,
            node           = statement
        ),
        exception_value = makeConstantReplacementNode(
            constant = exception_value,
            node     = statement
        ),
        exception_trace = None,
        source_ref = source_ref
    )

    return result

def convertRaiseExceptionExpressionRaiseExceptionStatement( node ):
    assert node.isExpressionRaiseException()

    side_effects = node.getSideEffects()

    raise_node = CPythonStatementRaiseException(
        exception_type  = node.getExceptionType(),
        exception_value = node.getExceptionValue(),
        exception_trace = None,
        source_ref      = node.getSourceReference()
    )

    if side_effects:
        side_effects = tuple(
            CPythonStatementExpressionOnly(
                expression = side_effect,
                source_ref = side_effect.getSourceReference()
            )
            for side_effect in side_effects
        )

        return makeStatementsSequenceReplacementNode(
            statements = side_effects + ( raise_node, ),
            node       = node
        )
    else:
        return raise_node

def makeStatementExpressionOnlyReplacementNode( expression, node ):
    return CPythonStatementExpressionOnly(
        expression = expression,
        source_ref = node.getSourceReference()
    )

def makeStatementsSequenceReplacementNode( statements, node ):
    return CPythonStatementsSequence(
        statements = statements,
        source_ref = node.getSourceReference()
    )

def convertNoneConstantToNone( node ):
    if node is None:
        return None
    elif node.isExpressionConstantRef() and node.getConstant() is None:
        return None
    else:
        return node
