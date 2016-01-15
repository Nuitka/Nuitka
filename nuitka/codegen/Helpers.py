#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Helpers for code generation.

This dispatch building of expressions and statements, as well as providing
typical support functions to building parts.

"""

from nuitka.Tracing import printError

expression_dispatch_dict = {}

def setExpressionDispatchDict(dispatch_dict):
    # Using global here, as this is really a singleton, in the form of a module,
    # and this is to break the cyclic dependency it has, pylint: disable=W0603

    # Please call us only once.
    global expression_dispatch_dict

    assert not expression_dispatch_dict
    expression_dispatch_dict = dispatch_dict


def generateExpressionCode(to_name, expression, emit, context,
                            allow_none = False):
    try:
        _generateExpressionCode(
            to_name    = to_name,
            expression = expression,
            emit       = emit,
            context    = context,
            allow_none = allow_none
        )
    except Exception:
        printError(
            "Problem with %r at %s" % (
                expression,
                ""
                  if expression is None else
                expression.getSourceReference().getAsString()
            )
        )
        raise


def _generateExpressionCode(to_name, expression, emit, context, allow_none = False):
    # This is a dispatching function for every expression.

    if expression is None and allow_none:
        return None

    # Make sure we don't generate code twice for any node, this uncovers bugs
    # where nodes are shared in the tree, which is not allowed.
    assert not hasattr(expression, "code_generated"), expression
    expression.code_generated = True

    old_source_ref = context.setCurrentSourceCodeReference(expression.getSourceReference())

    if not expression.isExpression():
        printError("No expression %r" % expression)

        expression.dump()
        assert False, expression

    expression_dispatch_dict[expression.kind](
        to_name    = to_name,
        expression = expression,
        emit       = emit,
        context    = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateExpressionsCode(names, expressions, emit, context):
    assert len(names) == len(expressions)

    result = []
    for name, expression in zip(names, expressions):
        if expression is not None:
            to_name = context.allocateTempName(name)

            generateExpressionCode(
                to_name    = to_name,
                expression = expression,
                emit       = emit,
                context    = context
            )
        else:
            to_name = None

        result.append(to_name)

    return result


def generateChildExpressionsCode(expression, emit, context):
    value_names = []

    for child_name in expression.named_children:
        child_value = expression.getChild(child_name)

        # Allocate anyway, so names are aligned.
        value_name = context.allocateTempName(child_name + "_name")

        if child_value is not None:
            generateExpressionCode(
                to_name    = value_name,
                expression = child_value,
                emit       = emit,
                context    = context
            )

            value_names.append(value_name)
        else:
            context.forgetTempName(value_name)

            value_names.append(None)


    return value_names


def generateChildExpressionCode(expression, emit, context, child_name = None):
    assert expression is not None

    if child_name is None:
        child_name = expression.getChildName()

    # Allocate anyway, so names are aligned.
    value_name = context.allocateTempName(child_name + "_name")

    generateExpressionCode(
        to_name    = value_name,
        expression = expression,
        emit       = emit,
        context    = context
    )

    return value_name


statement_dispatch_dict = {}

def setStatementDispatchDict(dispatch_dict):
    # Using global here, as this is really a singleton, in the form of a module,
    # and this is to break the cyclic dependency it has, pylint: disable=W0603

    # Please call us only once.
    global statement_dispatch_dict

    assert not statement_dispatch_dict
    statement_dispatch_dict = dispatch_dict


def generateStatementCode(statement, emit, context):
    try:
        statement_dispatch_dict[statement.kind](
            statement = statement,
            emit      = emit,
            context   = context
        )

        # Complain if any temporary was not dealt with yet.
        assert not context.getCleanupTempnames(), \
          context.getCleanupTempnames()
    except Exception:
        printError(
            "Problem with %r at %s" % (
                statement,
                statement.getSourceReference().getAsString()
            )
        )
        raise
