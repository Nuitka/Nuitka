#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" These are just helpers to create nodes, often to replace existing nodes

These are for use in optimizations and computations, and therefore cover
mostly exceptions and constants.

Often cyclic dependencies kicks in, which is why this module is mostly only
imported locally. Note: It's intended to be reversed, this module will make
the local imports instead, as these local imports look ugly everywhere else,
making it more difficult to use.
"""

from nuitka import Options
from nuitka.__past__ import GenericAlias, UnionType
from nuitka.Builtins import builtin_names
from nuitka.Constants import isConstant
from nuitka.PythonVersions import python_version
from nuitka.Tracing import my_print, unusual_logger


def makeConstantReplacementNode(constant, node, user_provided):
    from .ConstantRefNodes import makeConstantRefNode

    return makeConstantRefNode(
        constant=constant, source_ref=node.source_ref, user_provided=user_provided
    )


def makeRaiseExceptionReplacementExpression(
    expression, exception_type, exception_value, no_warning=False
):
    from .ExceptionNodes import (
        ExpressionRaiseException,
        makeBuiltinMakeExceptionNode,
    )

    source_ref = expression.source_ref

    assert type(exception_type) is str

    if not no_warning and Options.shallWarnImplicitRaises():
        unusual_logger.warning(
            '%s: Will always raise exception: "%s(%s)"'
            % (
                source_ref.getAsString(),
                exception_type,
                exception_value,
            )
        )

    if type(exception_value) is not tuple:
        exception_value = (exception_value,)

    args = tuple(
        makeConstantReplacementNode(
            constant=element, node=expression, user_provided=False
        )
        for element in exception_value
    )

    result = ExpressionRaiseException(
        exception_type=makeBuiltinMakeExceptionNode(
            exception_name=exception_type,
            args=args,
            for_raise=False,
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )

    return result


def makeRaiseExceptionReplacementStatement(
    statement, exception_type, exception_value, no_warning=False
):
    from .ExceptionNodes import (
        StatementRaiseException,
        makeBuiltinMakeExceptionNode,
    )

    source_ref = statement.getSourceReference()

    assert type(exception_type) is str

    if not no_warning and Options.shallWarnImplicitRaises():
        unusual_logger.warning(
            '%s: Will always raise exception: "%s(%s)"'
            % (
                source_ref.getAsString(),
                exception_type,
                exception_value,
            )
        )

    result = StatementRaiseException(
        exception_type=makeBuiltinMakeExceptionNode(
            exception_name=exception_type,
            args=(
                makeConstantReplacementNode(
                    constant=exception_value, node=statement, user_provided=False
                ),
            ),
            for_raise=False,
            source_ref=source_ref,
        ),
        exception_value=None,
        exception_cause=None,
        exception_trace=None,
        source_ref=source_ref,
    )

    return result


def makeRaiseExceptionReplacementExpressionFromInstance(expression, exception):
    assert isinstance(exception, Exception)

    return makeRaiseExceptionReplacementExpression(
        expression=expression,
        exception_type=exception.__class__.__name__,
        exception_value=exception.args,
    )


def makeRaiseExceptionStatementFromInstance(exception, source_ref):
    assert isinstance(exception, Exception)

    from .ConstantRefNodes import makeConstantRefNode
    from .ExceptionNodes import (
        StatementRaiseException,
        makeBuiltinMakeExceptionNode,
    )

    args_value = tuple(
        makeConstantRefNode(constant=arg, source_ref=source_ref, user_provided=False)
        for arg in exception.args
    )

    return StatementRaiseException(
        exception_type=makeBuiltinMakeExceptionNode(
            exception_name=exception.__class__.__name__,
            args=args_value,
            for_raise=False,
            source_ref=source_ref,
        ),
        exception_value=None,
        exception_cause=None,
        exception_trace=None,
        source_ref=source_ref,
    )


def makeRaiseExceptionExpressionFromTemplate(
    exception_type, template, template_args, source_ref
):
    from .ConstantRefNodes import makeConstantRefNode
    from .ContainerMakingNodes import makeExpressionMakeTupleOrConstant
    from .ExceptionNodes import (
        ExpressionRaiseException,
        makeBuiltinMakeExceptionNode,
    )
    from .OperatorNodes import makeBinaryOperationNode

    if type(template_args) is tuple:
        template_args = makeExpressionMakeTupleOrConstant(
            elements=template_args, user_provided=False, source_ref=source_ref
        )

    return ExpressionRaiseException(
        exception_type=makeBuiltinMakeExceptionNode(
            exception_name=exception_type,
            args=(
                makeBinaryOperationNode(
                    operator="Mod",
                    left=makeConstantRefNode(
                        constant=template, source_ref=source_ref, user_provided=True
                    ),
                    right=template_args,
                    source_ref=source_ref,
                ),
            ),
            for_raise=False,
            source_ref=source_ref,
        ),
        source_ref=source_ref,
    )


def makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
    template, operation, original_node, value_node
):
    shape = value_node.getTypeShape()

    type_name = shape.getTypeName()

    if type_name is not None:
        result = makeRaiseExceptionReplacementExpressionFromInstance(
            expression=original_node,
            exception=TypeError(template % type_name if "%" in template else template),
        )

        result = wrapExpressionWithNodeSideEffects(new_node=result, old_node=value_node)
    else:
        from .AttributeNodes import makeExpressionAttributeLookup
        from .TypeNodes import ExpressionBuiltinType1

        source_ref = original_node.getSourceReference()

        result = makeRaiseExceptionExpressionFromTemplate(
            exception_type="TypeError",
            template=template,
            template_args=makeExpressionAttributeLookup(
                expression=ExpressionBuiltinType1(
                    value=value_node.makeClone(), source_ref=source_ref
                ),
                attribute_name="__name__",
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        )

        type_name = shape.__name__

    return (
        result,
        "new_raise",
        "Raising for use of '%s' on %s '%s'."
        % (operation, "type" if type_name is not None else "shape", type_name),
    )


def makeCompileTimeConstantReplacementNode(value, node, user_provided):
    # This needs to match code in isCompileTimeConstantValue
    if isConstant(value):
        return makeConstantReplacementNode(
            constant=value, node=node, user_provided=user_provided
        )
    elif type(value) is type:
        if value.__name__ in builtin_names:
            from .BuiltinRefNodes import makeExpressionBuiltinRef

            # Need not provide locals_scope, not used for these kinds of built-in refs that
            # refer to types.
            return makeExpressionBuiltinRef(
                builtin_name=value.__name__,
                locals_scope=None,
                source_ref=node.getSourceReference(),
            )
        else:
            return node
    elif GenericAlias is not None and isinstance(value, GenericAlias):
        from .BuiltinTypeNodes import ExpressionConstantGenericAlias

        return ExpressionConstantGenericAlias(
            generic_alias=value,
            source_ref=node.getSourceReference(),
        )
    elif UnionType is not None and isinstance(value, UnionType):
        from .BuiltinTypeNodes import ExpressionConstantUnionType

        return ExpressionConstantUnionType(
            union_type=value,
            source_ref=node.getSourceReference(),
        )
    else:
        return node


def getComputationResult(node, computation, description, user_provided):
    """With a computation function, execute it and return constant result or
    exception node.

    """

    # Try and turn raised exceptions into static raises. pylint: disable=broad-except
    try:
        result = computation()
    except Exception as e:
        new_node = makeRaiseExceptionReplacementExpressionFromInstance(
            expression=node, exception=e
        )

        change_tags = "new_raise"
        change_desc = description + " Predicted to raise an exception."
    else:
        new_node = makeCompileTimeConstantReplacementNode(
            value=result, node=node, user_provided=user_provided
        )

        if Options.is_debug:
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
        expression=expression, source_ref=node.getSourceReference()
    )


def mergeStatements(statements, allow_none=False):
    """Helper function that merges nested statement sequences."""
    merged_statements = []

    for statement in statements:
        if statement is None and allow_none:
            pass
        elif type(statement) in (tuple, list):
            merged_statements += mergeStatements(statement, allow_none)
        elif statement.isStatementsFrame():
            merged_statements.append(statement)
        elif statement.isStatementsSequence():
            merged_statements.extend(mergeStatements(statement.subnode_statements))
        else:
            merged_statements.append(statement)

    return tuple(merged_statements)


def makeStatementsSequenceReplacementNode(statements, node):
    from .StatementNodes import StatementsSequence

    return StatementsSequence(
        statements=mergeStatements(statements), source_ref=node.getSourceReference()
    )


def wrapExpressionWithSideEffects(side_effects, old_node, new_node):
    from .SideEffectNodes import ExpressionSideEffects

    if side_effects:
        try:
            side_effects = sum(
                (
                    side_effect.extractSideEffects()
                    for side_effect in side_effects
                    if side_effect.mayHaveSideEffects()
                ),
                (),
            )
        except AttributeError:
            my_print("Problem with side effects:", side_effects)
            raise

        if side_effects:
            new_node = ExpressionSideEffects(
                expression=new_node,
                side_effects=side_effects,
                source_ref=old_node.getSourceReference(),
            )

    return new_node


def wrapExpressionWithNodeSideEffects(new_node, old_node):
    return wrapExpressionWithSideEffects(
        side_effects=old_node.extractSideEffects(), old_node=old_node, new_node=new_node
    )


def wrapStatementWithSideEffects(new_node, old_node, allow_none=False):
    assert new_node is not None or allow_none

    side_effects = old_node.extractSideEffects()

    if side_effects:
        from .StatementNodes import StatementExpressionOnly

        side_effects = tuple(
            StatementExpressionOnly(
                expression=side_effect, source_ref=side_effect.getSourceReference()
            )
            for side_effect in side_effects
        )

        if new_node is not None:
            new_node = makeStatementsSequenceReplacementNode(
                statements=side_effects + (new_node,), node=old_node
            )
        else:
            new_node = makeStatementsSequenceReplacementNode(
                statements=side_effects, node=old_node
            )

    return new_node


def makeStatementOnlyNodesFromExpressions(expressions):
    from .StatementNodes import StatementExpressionOnly, StatementsSequence

    statements = tuple(
        StatementExpressionOnly(
            expression=expression, source_ref=expression.getSourceReference()
        )
        for expression in expressions
    )

    if not statements:
        return None
    elif len(statements) == 1:
        return statements[0]
    else:
        return StatementsSequence(
            statements=statements, source_ref=statements[0].getSourceReference()
        )


def makeVariableRefNode(variable, source_ref):
    if variable.isTempVariable():
        from .VariableRefNodes import ExpressionTempVariableRef

        return ExpressionTempVariableRef(variable=variable, source_ref=source_ref)
    else:
        from .VariableRefNodes import ExpressionVariableRef

        return ExpressionVariableRef(variable=variable, source_ref=source_ref)


def makeExpressionBuiltinLocals(locals_scope, source_ref):
    if locals_scope.isModuleScope():
        from .GlobalsLocalsNodes import ExpressionBuiltinGlobals

        return ExpressionBuiltinGlobals(source_ref=source_ref)
    else:
        from .GlobalsLocalsNodes import (
            ExpressionBuiltinLocalsCopy,
            ExpressionBuiltinLocalsRef,
            ExpressionBuiltinLocalsUpdated,
        )

        if locals_scope.isClassScope():
            return ExpressionBuiltinLocalsRef(
                locals_scope=locals_scope, source_ref=source_ref
            )
        elif python_version >= 0x300 or locals_scope.isUnoptimizedFunctionScope():
            assert locals_scope.isFunctionScope(), locals_scope

            return ExpressionBuiltinLocalsUpdated(
                locals_scope=locals_scope, source_ref=source_ref
            )
        else:
            return ExpressionBuiltinLocalsCopy(
                locals_scope=locals_scope, source_ref=source_ref
            )


def makeRaiseImportErrorReplacementExpression(expression, module_name):
    return makeRaiseExceptionReplacementExpression(
        expression=expression,
        exception_type="ImportError",
        exception_value=module_name.asString(),
    )


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
