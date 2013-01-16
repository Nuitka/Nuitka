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
""" These are just helpers to create nodes, often to replace existing nodes

These are for use in optimizations and computations, and therefore cover mostly exceptions
and constants. Otherwise the thread of cyclic dependency kicks in.
"""

from .ConstantRefNode import CPythonExpressionConstantRef

from nuitka.Constants import isConstant
from nuitka.Builtins import builtin_names

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
from .CallNode import (
    CPythonExpressionCallComplex,
    CPythonExpressionCallRaw
)
from .ContainerMakingNodes import (
    CPythonExpressionMakeTuple,
    CPythonExpressionMakeDict
)
from .SideEffectNode import CPythonExpressionSideEffects



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

def makeCompileTimeConstantReplacementNode( value, node ):
    if isConstant( value ):
        return makeConstantReplacementNode(
            constant = value,
            node     = node
        )
    elif type( value ) is type:
        if value.__name__ in builtin_names:
            return CPythonExpressionBuiltinRef(
                builtin_name = value.__name__,
                source_ref    = node.getSourceReference()
            )
        else:
            return node
    else:
        return node

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
        new_node = makeCompileTimeConstantReplacementNode(
            value = result,
            node  = node
        )

        if new_node is not node:
            change_tags = "new_constant"
            change_desc = description + " was predicted to constant result."
        else:
            change_tags = None
            change_desc = None

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

def wrapExpressionWithSideEffects( side_effects, old_node, new_node ):
    assert new_node.isExpression()

    if side_effects:
        new_node = CPythonExpressionSideEffects(
            expression   = new_node,
            side_effects = side_effects,
            source_ref   = old_node.getSourceReference()
        )

    return new_node

def wrapExpressionWithNodeSideEffects( new_node, old_node ):
    return wrapExpressionWithSideEffects(
        side_effects = old_node.extractSideEffects(),
        old_node     = old_node,
        new_node     = new_node
    )

def wrapStatementWithSideEffects( new_node, old_node, allow_none = False ):
    assert new_node is not None or allow_none

    side_effects = old_node.extractSideEffects()

    if side_effects:
        side_effects = tuple(
            CPythonStatementExpressionOnly(
                expression = side_effect,
                source_ref = side_effect.getSourceReference()
            )
            for side_effect in side_effects
        )

        if new_node is not None:
            new_node = makeStatementsSequenceReplacementNode(
                statements = side_effects + ( new_node, ),
                node       = old_node
            )
        else:
            new_node = makeStatementsSequenceReplacementNode(
                statements = side_effects,
                node       = old_node
            )

    return new_node


def makeCallNode( called, positional_args, pairs, list_star_arg, dict_star_arg, source_ref ):
    if list_star_arg is None and dict_star_arg is None:
        return CPythonExpressionCallRaw(
            called  = called,
            args    = CPythonExpressionMakeTuple(
                elements   = positional_args,
                source_ref = source_ref
            ),
            kw      = CPythonExpressionMakeDict(
                pairs      = pairs,
                source_ref = source_ref
            ),
            source_ref      = source_ref,
        )
    else:
        return CPythonExpressionCallComplex(
            called          = called,
            positional_args = positional_args,
            pairs           = pairs,
            list_star_arg   = list_star_arg,
            dict_star_arg   = dict_star_arg,
            source_ref      = source_ref,
        )
