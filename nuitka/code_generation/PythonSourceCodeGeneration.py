#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for Python source from Nuitka node tree.

Used for generating bytecode-backed functions, if so decided. The main
important use is "__annotate__" functions.
"""

from nuitka.Errors import NuitkaCodeDeficit

from .CodeHelpers import getExpressionDispatchDict, getStatementDispatchDict


def getFunctionEntryPointIdentifier(function_identifier):
    return "impl_" + function_identifier


def getFunctionMakerIdentifier(function_identifier):
    return "MAKE_FUNCTION_" + function_identifier


class PythonSourceGenerationError(Exception):
    """Raised when a Nuitka node cannot be converted to Python source."""


# ---------------------------------------------------------------------------
# Per-kind generators


def _generateConstantTypeRefSource(expression):
    return expression.getCompileTimeConstant().__name__


def _generateConstantStrRefSource(expression):
    return repr(expression.getCompileTimeConstant())


def _generateConstantIntRefSource(expression):
    return repr(expression.getCompileTimeConstant())


def _generateConstantBoolRefSource(expression):
    constant = expression.getCompileTimeConstant()
    assert constant is True or constant is False
    return "True" if constant is True else "False"


def _generateConstantNoneRefSource(_expression):
    return "None"


def _generateAttributeLookupSource(expression):
    left = generateExpressionSource(expression.subnode_expression)
    attr = expression.getAttributeName()
    return "%s.%s" % (left, attr)


def _generateSubscriptLookupSource(expression):
    looked_up = generateExpressionSource(expression.subnode_expression)
    subscript = generateExpressionSource(expression.subnode_subscript)
    return "%s[%s]" % (looked_up, subscript)


def _generateBinaryOpSource(expression):
    operator = expression.getOperator()

    if operator == "BitOr":
        left = _maybeParens(expression.subnode_left)
        right = _maybeParens(expression.subnode_right)
        return "%s | %s" % (left, right)

    raise PythonSourceGenerationError(
        "Unsupported binary operator for source generation: %s" % operator
    )


# Node kinds that bind tighter than binary operators and need no parens.
_atomic_kinds = frozenset(
    (
        "EXPRESSION_CONSTANT_TYPE_REF",
        "EXPRESSION_VARIABLE_REF",
        "EXPRESSION_CONSTANT_STR_REF",
        "EXPRESSION_CONSTANT_UNICODE_REF",
        "EXPRESSION_CONSTANT_INT_REF",
        "EXPRESSION_CONSTANT_LONG_REF",
        "EXPRESSION_CONSTANT_NONE_REF",
        "EXPRESSION_CONSTANT_TRUE_REF",
        "EXPRESSION_CONSTANT_FALSE_REF",
        "EXPRESSION_CONSTANT_ELLIPSIS_REF",
        "EXPRESSION_ATTRIBUTE_LOOKUP",
        "EXPRESSION_SUBSCRIPT_LOOKUP",
        "EXPRESSION_FUNCTION_CALL",
        "EXPRESSION_MAKE_TUPLE",
    )
)


def _maybeParens(expression):
    source = generateExpressionSource(expression)
    if expression.kind in _atomic_kinds:
        return source
    return "(%s)" % source


def _generateFunctionCallSource(expression):
    called_source = generateExpressionSource(expression.subnode_function)

    arg_sources = []
    for arg in expression.subnode_values:
        arg_sources.append(generateExpressionSource(arg))

    return "%s(%s)" % (called_source, ", ".join(arg_sources))


def _generateTupleSource(expression):
    elements = []
    for element in expression.subnode_elements:
        elements.append(generateExpressionSource(element))

    if len(elements) == 0:
        return "()"
    elif len(elements) == 1:
        return "(%s,)" % elements[0]
    else:
        return "(%s)" % ", ".join(elements)


def _generateDictSource(expression):
    items = []
    for pair in expression.subnode_pairs:
        key_source = repr(pair.getKeyCompileTimeConstant())
        value_source = generateExpressionSource(pair.getValueNode())
        items.append("%s: %s" % (key_source, value_source))

    return "{%s}" % ", ".join(items)


def _generateSliceSource(expression):
    lower = expression.subnode_lower
    upper = expression.subnode_upper
    step = expression.subnode_step

    if lower is None and upper is None and step is None:
        return ":"

    parts = []
    for part in (lower, upper, step):
        if part is not None:
            parts.append(generateExpressionSource(part))
        else:
            parts.append("")

    return "%s:%s:%s" % tuple(parts)


def _generateComparisonSource(expression):
    # Comparison nodes have a 'comparator' class attribute, e.g. "Gt", "GtE".
    comparator = type(expression).comparator

    operators = {
        "Lt": "<",
        "LtE": "<=",
        "Gt": ">",
        "GtE": ">=",
        "Eq": "==",
        "NotEq": "!=",
    }

    op = operators.get(comparator)
    if op is None:
        raise PythonSourceGenerationError("Unsupported comparison: %s" % comparator)

    left = generateExpressionSource(expression.subnode_left)
    right = generateExpressionSource(expression.subnode_right)
    return "%s %s %s" % (left, op, right)


# ---------------------------------------------------------------------------
# Statement-level source generation


def generateStatementSequenceSource(statement_seq, indent=""):
    """Generate Python source for a StatementsSequence."""
    lines = []

    for statement in statement_seq.subnode_statements:
        kind = statement.kind

        handler = _statement_source_dispatch.get(kind)
        if handler is None:
            raise PythonSourceGenerationError(
                "Unsupported statement kind for source generation: %s" % kind
            )

        lines.append(handler(statement, indent))

    return "\n".join(lines)


def _generateConditionalSource(statement, indent):
    condition = generateExpressionSource(statement.subnode_condition)
    yes_body = generateStatementSequenceSource(
        statement.subnode_yes_branch, indent=indent + "    "
    )
    no_body = generateStatementSequenceSource(
        statement.subnode_no_branch, indent=indent + "    "
    )

    if no_body == "pass":
        return "%sif %s:\n%s" % (indent, condition, yes_body)
    else:
        return "%sif %s:\n%s\n%selse:\n%s" % (
            indent,
            condition,
            yes_body,
            indent,
            no_body,
        )


def _generateRaiseExceptionSource(statement, indent):
    exception_type = generateExpressionSource(statement.subnode_exception_type)
    return "%sraise %s" % (indent, exception_type)


def _generateReturnSource(statement, indent):
    if statement.isStatementReturnConstant():
        constant = statement.getConstant()
        if isinstance(constant, dict):
            items = []
            for key, value in constant.items():
                items.append("%s: %s" % (repr(key), _constantToSource(value)))

            value = "{%s}" % ", ".join(items)
        else:
            value = _constantToSource(constant)

        return "%sreturn %s" % (indent, value)
    else:
        expression = statement.subnode_expression
        value = generateExpressionSource(expression)
        return "%sreturn %s" % (indent, value)


def _constantToSource(value):
    """Convert a compile-time constant to its Python source representation."""
    if isinstance(value, type):
        return value.__name__
    elif value is None:
        return "None"
    elif value is True:
        return "True"
    elif value is False:
        return "False"
    elif value is Ellipsis:
        return "..."
    else:
        return repr(value)


def generateFunctionSourceFromBody(function_body):
    """Generate a complete `def ...` Python source from a function body."""
    body_source = generateStatementSequenceSource(
        function_body.subnode_body, indent=" " * 4
    )

    return "def %s(%s):\n%s" % (
        function_body.getFunctionName(),
        ", ".join(function_body.getParameters().getParameterNames()),
        body_source,
    )


def _generateBuiltinNext1Source(expression):
    inner = generateExpressionSource(expression.subnode_value)
    return "next(iter(%s))" % inner


def _generateVariableRefSource(expression):
    return expression.variable.getName()


def _generateEllipsisSource(_expression):
    return "..."


def _generateBuiltinExceptionRefSource(expression):
    return expression.getBuiltinName()


# ---------------------------------------------------------------------------
# Dispatch table

_expression_source_dispatch = {
    "EXPRESSION_CONSTANT_TYPE_REF": _generateConstantTypeRefSource,
    "EXPRESSION_VARIABLE_REF": _generateVariableRefSource,
    "EXPRESSION_CONSTANT_STR_REF": _generateConstantStrRefSource,
    "EXPRESSION_CONSTANT_UNICODE_REF": _generateConstantStrRefSource,
    "EXPRESSION_CONSTANT_INT_REF": _generateConstantIntRefSource,
    "EXPRESSION_CONSTANT_LONG_REF": _generateConstantIntRefSource,
    "EXPRESSION_CONSTANT_NONE_REF": _generateConstantNoneRefSource,
    "EXPRESSION_CONSTANT_TRUE_REF": _generateConstantBoolRefSource,
    "EXPRESSION_CONSTANT_FALSE_REF": _generateConstantBoolRefSource,
    "EXPRESSION_CONSTANT_ELLIPSIS_REF": _generateEllipsisSource,
    "EXPRESSION_ATTRIBUTE_LOOKUP": _generateAttributeLookupSource,
    "EXPRESSION_SUBSCRIPT_LOOKUP": _generateSubscriptLookupSource,
    "EXPRESSION_OPERATION_BINARY_BIT_OR": _generateBinaryOpSource,
    "EXPRESSION_FUNCTION_CALL": _generateFunctionCallSource,
    "EXPRESSION_MAKE_TUPLE": _generateTupleSource,
    "EXPRESSION_MAKE_DICT": _generateDictSource,
    "EXPRESSION_BUILTIN_SLICE1": _generateSliceSource,
    "EXPRESSION_BUILTIN_SLICE2": _generateSliceSource,
    "EXPRESSION_BUILTIN_SLICE3": _generateSliceSource,
    "EXPRESSION_BUILTIN_NEXT1": _generateBuiltinNext1Source,
    "EXPRESSION_COMPARISON_GT": _generateComparisonSource,
    "EXPRESSION_COMPARISON_GTE": _generateComparisonSource,
    "EXPRESSION_COMPARISON_LT": _generateComparisonSource,
    "EXPRESSION_COMPARISON_LTE": _generateComparisonSource,
    "EXPRESSION_COMPARISON_EQ": _generateComparisonSource,
    "EXPRESSION_COMPARISON_NEQ": _generateComparisonSource,
    "EXPRESSION_BUILTIN_EXCEPTION_REF": _generateBuiltinExceptionRefSource,
}

_statement_source_dispatch = {
    "STATEMENT_CONDITIONAL": _generateConditionalSource,
    "STATEMENT_RAISE_EXCEPTION": _generateRaiseExceptionSource,
    "STATEMENT_RETURN": _generateReturnSource,
    "STATEMENT_RETURN_CONSTANT": _generateReturnSource,
}

_checked_dispatch_kinds = False


def _checkDispatchKinds():
    """Verify all source-generation kinds exist in C code generation."""
    # Singleton, pylint: disable=global-statement
    global _checked_dispatch_kinds

    if _checked_dispatch_kinds:
        return

    for kind in _expression_source_dispatch:
        if kind not in getExpressionDispatchDict():
            raise NuitkaCodeDeficit(
                "Source generation expression kind %r is not in C dispatch" % kind
            )

    for kind in _statement_source_dispatch:
        if kind not in getStatementDispatchDict():
            raise NuitkaCodeDeficit(
                "Source generation statement kind %r is not in C dispatch" % kind
            )

    _checked_dispatch_kinds = True


def generateExpressionSource(expression):
    """Generate Python source code for a Nuitka expression node.

    Returns a string of valid Python source.
    Raises PythonSourceGenerationError for unsupported node kinds.
    """
    _checkDispatchKinds()

    kind = expression.kind

    handler = _expression_source_dispatch.get(kind)
    if handler is None:
        raise PythonSourceGenerationError(
            "Unsupported expression kind for source generation: %s" % kind
        )

    return handler(expression)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
