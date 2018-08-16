#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

These are for use in optimizations and computations, and therefore cover
mostly exceptions and constants.

Often cyclic dependencies kicks in, which is why this module is mostly only
imported locally. Note: It's intended to be reversed, this module will make
the local imports instead, as these local imports look ugly everywhere else,
making it more difficult to use.
"""

from logging import warning

from nuitka.Builtins import builtin_names
from nuitka.Constants import isConstant
from nuitka.Options import isDebug, shallWarnImplicitRaises
from nuitka.PythonVersions import python_version


def makeConstantReplacementNode(constant, node):
    from .ConstantRefNodes import makeConstantRefNode

    return makeConstantRefNode(
        constant   = constant,
        source_ref = node.getSourceReference()
    )


def makeRaiseExceptionReplacementExpression(expression, exception_type,
                                            exception_value):
    from .ExceptionNodes import ExpressionRaiseException
    from .BuiltinRefNodes import ExpressionBuiltinExceptionRef

    source_ref = expression.getSourceReference()

    assert type(exception_type) is str

    if shallWarnImplicitRaises():
        warning(
            '%s: Will always raise exception: "%s(%s)"',
            source_ref.getAsString(),
            exception_type,
            exception_value
        )

    result = ExpressionRaiseException(
        exception_type  = ExpressionBuiltinExceptionRef(
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


def makeRaiseExceptionReplacementStatement(statement, exception_type,
                                           exception_value):
    from .ExceptionNodes import StatementRaiseExceptionImplicit
    from .BuiltinRefNodes import ExpressionBuiltinExceptionRef

    source_ref = statement.getSourceReference()

    assert type(exception_type) is str

    if shallWarnImplicitRaises():
        warning(
            '%s: Will always raise exception: "%s(%s)"',
            source_ref.getAsString(),
            exception_type,
            exception_value
        )

    result = StatementRaiseExceptionImplicit(
        exception_type  = ExpressionBuiltinExceptionRef(
            exception_name = exception_type,
            source_ref     = source_ref
        ),
        exception_value = makeConstantReplacementNode(
            constant = exception_value,
            node     = statement
        ),
        exception_cause = None,
        exception_trace = None,
        source_ref      = source_ref
    )

    return result


def makeRaiseExceptionReplacementExpressionFromInstance(expression, exception):
    assert isinstance(exception, Exception)

    args = exception.args
    if type(args) is tuple and len(args) == 1:
        value = args[0]
    else:
        assert type(args) is tuple
        value = args

    return makeRaiseExceptionReplacementExpression(
        expression      = expression,
        exception_type  = exception.__class__.__name__,
        exception_value = value
    )


def makeRaiseExceptionExpressionFromTemplate(exception_type, template,
                                             template_args, source_ref):
    from .ExceptionNodes import ExpressionRaiseException
    from .BuiltinRefNodes import ExpressionBuiltinExceptionRef
    from .OperatorNodes import makeBinaryOperationNode
    from .ConstantRefNodes import makeConstantRefNode
    from .ContainerMakingNodes import ExpressionMakeTuple

    if type(template_args) is tuple:
        template_args = ExpressionMakeTuple(
            elements   = template_args,
            source_ref = source_ref
        )

    return ExpressionRaiseException(
        exception_type  = ExpressionBuiltinExceptionRef(
            exception_name = exception_type,
            source_ref     = source_ref
        ),
        exception_value = makeBinaryOperationNode(
            operator   = "Mod",
            left       =  makeConstantRefNode(
                constant      = template,
                source_ref    = source_ref,
                user_provided = True
            ),
            right      = template_args,
            source_ref = source_ref
        ),
        source_ref      = source_ref
    )


def makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(template,
                                                               operation,
                                                               original_node,
                                                               value_node):
    shape = value_node.getTypeShape()

    type_name = shape.getTypeName()

    if type_name is not None:
        result = makeRaiseExceptionReplacementExpressionFromInstance(
            expression = original_node,
            exception  = TypeError(template % type_name if '%' in template else template)
        )

        result = wrapExpressionWithNodeSideEffects(
            new_node = result,
            old_node = value_node
        )

    else:
        from .AttributeNodes import ExpressionAttributeLookup
        from .TypeNodes import ExpressionBuiltinType1

        source_ref = original_node.getSourceReference()

        result = makeRaiseExceptionExpressionFromTemplate(
            exception_type = "TypeError",
            template       = "object of type '%s' has no len()",
            template_args  = ExpressionAttributeLookup(
                source         = ExpressionBuiltinType1(
                    value      = value_node.makeClone(),
                    source_ref = source_ref
                ),
                attribute_name = "__name__",
                source_ref     = source_ref
            ),
            source_ref     = source_ref
        )

        type_name = shape.__name__

    return result, "new_raise", "Raising for use of '%s' on %s '%s'." % (
        operation,
        "type" if type_name is not None else "shape",
        type_name
    )


def makeCompileTimeConstantReplacementNode(value, node):
    # This needs to match code in isCompileTimeConstantValue
    if isConstant(value):
        return makeConstantReplacementNode(
            constant = value,
            node     = node
        )
    elif type(value) is type:
        if value.__name__ in builtin_names:
            from .BuiltinRefNodes import makeExpressionBuiltinRef

            return makeExpressionBuiltinRef(
                builtin_name = value.__name__,
                source_ref   = node.getSourceReference()
            )
        else:
            return node
    else:
        return node


def getComputationResult(node, computation, description):
    """ With a computation function, execute it and return constant result or
        exception node.

    """

    # Try and turn raised exceptions into static raises. pylint: disable=broad-except
    try:
        result = computation()
    except Exception as e:
        new_node = makeRaiseExceptionReplacementExpressionFromInstance(
            expression = node,
            exception  = e
        )

        change_tags = "new_raise"
        change_desc = description + " Predicted to raise an exception."
    else:
        new_node = makeCompileTimeConstantReplacementNode(
            value = result,
            node  = node
        )

        if isDebug():
            assert new_node is not node, (node, result)

        if new_node is not node:
            change_tags = "new_constant"
            change_desc = description + " Predicted constant result."
        else:
            change_tags = None
            change_desc = None

    return new_node, change_tags, change_desc


def makeStatementExpressionOnlyReplacementNode(expression, node):
    from .StatementNodes import StatementExpressionOnly

    return StatementExpressionOnly(
        expression = expression,
        source_ref = node.getSourceReference()
    )


def mergeStatements(statements, allow_none = False):
    """ Helper function that merges nested statement sequences. """
    merged_statements = []

    for statement in statements:
        if statement is None and allow_none:
            pass
        elif type(statement) in (tuple, list):
            merged_statements += mergeStatements(statement, allow_none)
        elif statement.isStatement() or statement.isStatementsFrame():
            merged_statements.append(statement)
        elif statement.isStatementsSequence():
            merged_statements.extend(mergeStatements(statement.getStatements()))
        else:
            assert False, statement

    return merged_statements


def makeStatementsSequenceReplacementNode(statements, node):
    from .StatementNodes import StatementsSequence

    return StatementsSequence(
        statements = mergeStatements(statements),
        source_ref = node.getSourceReference()
    )


def convertNoneConstantToNone(node):
    if node is None:
        return None
    elif node.isExpressionConstantRef() and node.getConstant() is None:
        return None
    else:
        return node


def wrapExpressionWithSideEffects(side_effects, old_node, new_node):
    assert new_node.isExpression()

    from .SideEffectNodes import ExpressionSideEffects

    if side_effects:
        side_effects = sum(
            (
                side_effect.extractSideEffects()
                for side_effect in
                side_effects
                if side_effect.mayHaveSideEffects()
            ),
            ()
        )

        if side_effects:
            new_node = ExpressionSideEffects(
                expression   = new_node,
                side_effects = side_effects,
                source_ref   = old_node.getSourceReference()
            )

    return new_node

def wrapExpressionWithNodeSideEffects(new_node, old_node):
    return wrapExpressionWithSideEffects(
        side_effects = old_node.extractSideEffects(),
        old_node     = old_node,
        new_node     = new_node
    )

def wrapStatementWithSideEffects(new_node, old_node, allow_none = False):
    assert new_node is not None or allow_none

    side_effects = old_node.extractSideEffects()

    if side_effects:
        from .StatementNodes import StatementExpressionOnly

        side_effects = tuple(
            StatementExpressionOnly(
                expression = side_effect,
                source_ref = side_effect.getSourceReference()
            )
            for side_effect in side_effects
        )

        if new_node is not None:
            new_node = makeStatementsSequenceReplacementNode(
                statements = side_effects + (new_node,),
                node       = old_node
            )
        else:
            new_node = makeStatementsSequenceReplacementNode(
                statements = side_effects,
                node       = old_node
            )

    return new_node

def makeStatementOnlyNodesFromExpressions(expressions):
    from .StatementNodes import StatementExpressionOnly, StatementsSequence

    statements = tuple(
        StatementExpressionOnly(
            expression = expression,
            source_ref = expression.getSourceReference()
        )
        for expression in expressions
    )

    if not statements:
        return None
    elif len(statements) == 1:
        return statements[0]
    else:
        return StatementsSequence(
            statements = statements,
            source_ref = statements[0].getSourceReference()
        )


def makeComparisonNode(left, right, comparator, source_ref):
    from .ComparisonNodes import (
        ExpressionComparison,
        ExpressionComparisonIs,
        ExpressionComparisonIsNOT,
        ExpressionComparisonIn,
        ExpressionComparisonNOTIn
    )

    if comparator == "Is":
        result = ExpressionComparisonIs(
            left       = left,
            right      = right,
            source_ref = source_ref
        )
    elif comparator == "IsNot":
        result = ExpressionComparisonIsNOT(
            left       = left,
            right      = right,
            source_ref = source_ref
        )
    elif comparator == "In":
        result = ExpressionComparisonIn(
            left       = left,
            right      = right,
            source_ref = source_ref
        )
    elif comparator == "NotIn":
        result = ExpressionComparisonNOTIn(
            left       = left,
            right      = right,
            source_ref = source_ref
        )
    else:
        result = ExpressionComparison(
            left       = left,
            right      = right,
            comparator = comparator,
            source_ref = source_ref
        )

    result.setCompatibleSourceReference(
        source_ref = right.getCompatibleSourceReference()
    )

    return result


def makeVariableRefNode(variable, source_ref):
    if variable.isTempVariable():
        from .VariableRefNodes import ExpressionTempVariableRef

        return ExpressionTempVariableRef(
            variable   = variable,
            source_ref = source_ref
        )
    else:
        from .VariableRefNodes import ExpressionVariableRef

        return ExpressionVariableRef(
            variable   = variable,
            source_ref = source_ref
        )


def makeExpressionBuiltinLocals(provider, source_ref):
    while provider.isExpressionOutlineFunction():
        provider = provider.getParentVariableProvider()

    if provider.isCompiledPythonModule():
        from .GlobalsLocalsNodes import ExpressionBuiltinGlobals

        return ExpressionBuiltinGlobals(
            source_ref = source_ref
        )
    else:
        from .GlobalsLocalsNodes import (
            ExpressionBuiltinLocalsCopy,
            ExpressionBuiltinLocalsRef,
            ExpressionBuiltinLocalsUpdated
        )

        if provider.isExpressionClassBody():
            return ExpressionBuiltinLocalsRef(
                locals_scope = provider.getFunctionLocalsScope(),
                source_ref   = source_ref
            )
        elif python_version >= 300 or provider.isUnoptimized():
            assert provider.getFunctionLocalsScope(), provider

            return ExpressionBuiltinLocalsUpdated(
                locals_scope = provider.getFunctionLocalsScope(),
                source_ref   = source_ref
            )
        else:
            # TODO: Make this not true, there ought to be always a locals
            # scope.
            assert not provider.getFunctionLocalsScope(), provider

            return ExpressionBuiltinLocalsCopy(
                locals_scope = provider.getFunctionLocalsScope(),
                source_ref   = source_ref
            )
