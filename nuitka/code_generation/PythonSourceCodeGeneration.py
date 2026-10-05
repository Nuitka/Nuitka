#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for Python source from Nuitka node tree.

Used for generating bytecode-backed functions, if so decided. The main
important use is "__annotate__" functions.
"""

import re
import types

from nuitka.__past__ import GenericAlias, UnionType, frozendict, re_sub
from nuitka.Constants import EllipsisType, NoneType
from nuitka.Errors import NuitkaCodeDeficit
from nuitka.Tracing import code_generation_logger

from .CodeHelpers import getExpressionDispatchDict, getStatementDispatchDict


def getFunctionEntryPointIdentifier(function_identifier):
    return "impl_" + function_identifier


def getFunctionMakerIdentifier(function_identifier):
    return "MAKE_FUNCTION_" + function_identifier


class PythonSourceGenerationError(Exception):
    """Raised when a Nuitka node cannot be converted to Python source."""


# ---------------------------------------------------------------------------
# Per-kind generators


def _formatTypeSource(value, expression):
    """Return the source representation of a type constant.

    Only built-in types (int, str, list, dict, etc.) are available as bare
    names in module globals.  Types from imported modules (e.g. io.BytesIO)
    are emitted as `module_alias.TypeName` when an alias can be found, or
    via `__import__()` otherwise.

    Args:
        value: The type to format.
        expression: Nuitka expression node for alias resolution.

    Returns:
        The type name as a Python source string.
    """
    if value.__module__ in ("builtins", None):
        return value.__name__

    module = expression.getParentModule()
    alias = _findAliasForModule(module, value.__module__)

    if alias is not None:
        return "%s.%s" % (alias, value.__name__)

    return "__import__(%r).%s" % (value.__module__, value.__name__)


def _generateConstantTypeRefSource(expression):
    return _formatTypeSource(expression.getCompileTimeConstant(), expression)


def _formatConstantFloat(value, expression):
    # The expression argument is for the uniform dispatch only.
    # pylint: disable=unused-argument
    # "repr" gives bare "inf", "-inf" and "nan", which are names, not literals.
    result = repr(value)

    if result in ("inf", "-inf", "nan"):
        return 'float("%s")' % result

    return result


def _formatConstantComplex(value, expression):
    real, imag = value.real, value.imag

    # "repr" of complex numbers with nan/inf components yields bare
    # "nan"/"inf" tokens (e.g. "(nan+1j)"), which are names, not literals.
    # For such values fall back to "complex(real, imag)" so each component
    # is formatted via '_formatConstantFloat'.
    if repr(real) in ("inf", "-inf", "nan") or repr(imag) in ("inf", "-inf", "nan"):
        return "complex(%s, %s)" % (
            _formatConstantFloat(real, expression),
            _formatConstantFloat(imag, expression),
        )

    return repr(value)


def _formatConstantRepr(value, expression):
    # The expression argument is for the uniform dispatch only.
    # pylint: disable=unused-argument
    return repr(value)


def _formatConstantStr(value, expression):
    # The expression argument is for the uniform dispatch only.
    # pylint: disable=unused-argument
    return str(value)


def _formatEllipsisValue(value, expression):
    # We insist on this value that is not the repr, pylint: disable=unused-argument
    return "..."


def _formatFunctionValue(value, expression):
    # The expression argument is for the uniform dispatch only.
    # pylint: disable=unused-argument
    return value.__name__


def _formatConstantTuple(value, expression):
    if len(value) == 0:
        return "()"
    elif len(value) == 1:
        return "(%s,)" % _formatConstantElement(value[0], expression)
    else:
        return "(%s)" % ", ".join(_formatConstantElement(e, expression) for e in value)


def _formatConstantList(value, expression):
    return "[%s]" % ", ".join(_formatConstantElement(e, expression) for e in value)


def _formatConstantDict(value, expression):
    return "{%s}" % ", ".join(
        "%s: %s"
        % (
            _formatConstantElement(k, expression),
            _formatConstantElement(v, expression),
        )
        for k, v in value.items()
    )


def _formatConstantSet(value, expression):
    if not value:
        return "set()"

    return "{%s}" % ", ".join(_formatConstantElement(e, expression) for e in value)


def _formatConstantFrozenset(value, expression):
    if not value:
        return "frozenset()"

    return "frozenset({%s})" % ", ".join(
        _formatConstantElement(e, expression) for e in value
    )


def _formatConstantFrozendict(value, expression):
    if not value:
        return "frozendict()"

    return "frozendict(%s)" % _formatConstantDict(value, expression)


# Dispatch by exact constant type. The 'GenericAlias', 'UnionType' and
# 'frozendict' are 'None' before Python 3.9, 3.10 and 3.15 respectively, which
# no value can have as its type, so this is harmless.
_constant_formatters = {
    str: _formatConstantRepr,
    int: _formatConstantRepr,
    bool: _formatConstantRepr,
    bytes: _formatConstantRepr,
    bytearray: _formatConstantRepr,
    float: _formatConstantFloat,
    complex: _formatConstantComplex,
    NoneType: _formatConstantRepr,
    EllipsisType: _formatEllipsisValue,
    GenericAlias: _formatConstantStr,
    UnionType: _formatConstantStr,
    types.BuiltinFunctionType: _formatFunctionValue,
    types.FunctionType: _formatFunctionValue,
    tuple: _formatConstantTuple,
    list: _formatConstantList,
    dict: _formatConstantDict,
    set: _formatConstantSet,
    frozenset: _formatConstantFrozenset,
    frozendict: _formatConstantFrozendict,
}


def _formatConstantElement(value, expression):
    constant_type = type(value)

    formatter = _constant_formatters.get(constant_type)

    if formatter is not None:
        return formatter(value, expression)

    # Class objects are not covered by the exact type dispatch dictionary.
    if isinstance(value, type):
        return _formatTypeSource(value, expression)

    raise PythonSourceGenerationError(
        "Unsupported constant value for source generation: %s (%s)"
        % (constant_type.__name__, repr(value))
    )


def _generateListConstantSource(expression):
    return _formatConstantList(expression.getCompileTimeConstant(), expression)


def _generateSetConstantSource(expression):
    return _formatConstantSet(expression.getCompileTimeConstant(), expression)


def _generateFrozensetConstantSource(expression):
    return _formatConstantFrozenset(expression.getCompileTimeConstant(), expression)


def _generateDictConstantSource(expression):
    return _formatConstantDict(expression.getCompileTimeConstant(), expression)


def _generateFrozendictConstantSource(expression):
    constant_value = expression.getCompileTimeConstant()

    if not constant_value:
        return "frozendict()"

    return "frozendict(%s)" % _formatConstantDict(constant_value, expression)


def _findAliasForModule(module, target):
    """Find the module variable name for `target` via trace collection.

    Returns the variable name (the alias, or the module name itself when it
    was imported without a rename) if a module variable for `target` exists,
    else None.
    """
    trace_collection = module.getTraceCollection()

    for variable, traces in trace_collection.variable_traces.items():
        if not variable.isModuleVariable():
            continue

        for trace in traces.values():
            if trace.getAttributeNode() is None:
                continue

            node = trace.getAttributeNode()

            if node is None:
                continue

            if (
                node.isExpressionImportModuleHard()
                or node.isExpressionImportModuleFixed()
                or node.isExpressionImportModuleBuiltin()
            ):
                module_name = node.getModuleName()

                if module_name.asString() == target:
                    return variable.getName()
            elif node.isExpressionBuiltinImport():
                # General import `import mymod as mm` -> `__import__('mymod')`
                name_node = node.subnode_name

                if name_node is None or not name_node.isExpressionConstantRef():
                    continue

                module_name_str = name_node.getCompileTimeConstant()

                if module_name_str != target:
                    continue

                return variable.getName()

    return None


def _generateGenericAliasSource(expression):
    value = expression.getCompileTimeConstant()
    s = str(value)

    module = expression.getParentModule()

    # Cache alias lookups per module/target.
    alias_cache = {}

    def _replaceAlias(match):
        tgt = match.group(1)

        if tgt not in alias_cache:
            alias_cache[tgt] = _findAliasForModule(module, tgt)

        alias = alias_cache[tgt]

        if alias:
            return alias + "."

        return match.group(0)

    return re_sub(r"\b([^\W\d]\w*)\.", _replaceAlias, s, flags=re.UNICODE)


def _generateTupleConstantSource(expression):
    return _formatConstantTuple(expression.getCompileTimeConstant(), expression)


def _generateConstantStrRefSource(expression):
    return repr(expression.getCompileTimeConstant())


def _generateConstantBytesRefSource(expression):
    return repr(expression.getCompileTimeConstant())


def _generateConstantIntRefSource(expression):
    return repr(expression.getCompileTimeConstant())


def _generateConstantFloatRefSource(expression):
    return _formatConstantFloat(expression.getCompileTimeConstant(), expression)


def _generateConstantComplexRefSource(expression):
    return _formatConstantComplex(expression.getCompileTimeConstant(), expression)


def _generateConstantBytearrayRefSource(expression):
    return repr(expression.getCompileTimeConstant())


def _generateConstantSliceRefSource(expression):
    value = expression.getCompileTimeConstant()

    parts = [
        _formatConstantElement(value.start, expression),
        _formatConstantElement(value.stop, expression),
        _formatConstantElement(value.step, expression),
    ]

    # Omit trailing None components to match the canonical slice literal form
    # (e.g. `slice(None, 5)` rather than `slice(None, 5, None)`), since repr()
    # itself is not valid as a bare expression.
    while parts and parts[-1] == "None":
        parts.pop()

    return "slice(%s)" % ", ".join(parts)


def _generateConstantXrangeRefSource(expression):
    value = expression.getCompileTimeConstant()

    parts = [
        _formatConstantElement(value.start, expression),
        _formatConstantElement(value.stop, expression),
    ]

    step = _formatConstantElement(value.step, expression)
    if step != "1":
        parts.append(step)

    return "range(%s)" % ", ".join(parts)


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


_binary_operator_symbols = {
    "Add": "+",
    "Sub": "-",
    "Mult": "*",
    "MatMult": "@",
    "TrueDiv": "/",
    "FloorDiv": "//",
    "Mod": "%",
    "Pow": "**",
    "LShift": "<<",
    "RShift": ">>",
    "BitAnd": "&",
    "BitOr": "|",
    "BitXor": "^",
}


def _generateBinaryOpSource(expression):
    operator = expression.getOperator()

    symbol = _binary_operator_symbols.get(operator)

    if symbol is None:
        raise PythonSourceGenerationError(
            "Unsupported binary operator for source generation: %s" % operator
        )

    left = _maybeParens(expression.subnode_left)
    right = _maybeParens(expression.subnode_right)
    return "%s %s %s" % (left, symbol, right)


# Node kinds that bind tighter than binary operators and need no parens.
_atomic_kinds = frozenset(
    (
        "EXPRESSION_CONSTANT_TYPE_REF",
        "EXPRESSION_VARIABLE_REF",
        "EXPRESSION_CONSTANT_STR_REF",
        "EXPRESSION_CONSTANT_STR_EMPTY_REF",
        "EXPRESSION_CONSTANT_UNICODE_REF",
        "EXPRESSION_CONSTANT_UNICODE_EMPTY_REF",
        "EXPRESSION_CONSTANT_BYTES_REF",
        "EXPRESSION_CONSTANT_BYTES_EMPTY_REF",
        "EXPRESSION_CONSTANT_BYTEARRAY_REF",
        "EXPRESSION_CONSTANT_INT_REF",
        "EXPRESSION_CONSTANT_LONG_REF",
        "EXPRESSION_CONSTANT_FLOAT_REF",
        "EXPRESSION_CONSTANT_COMPLEX_REF",
        "EXPRESSION_CONSTANT_NONE_REF",
        "EXPRESSION_CONSTANT_TRUE_REF",
        "EXPRESSION_CONSTANT_FALSE_REF",
        "EXPRESSION_CONSTANT_ELLIPSIS_REF",
        "EXPRESSION_CONSTANT_SLICE_REF",
        "EXPRESSION_CONSTANT_XRANGE_REF",
        "EXPRESSION_ATTRIBUTE_LOOKUP",
        "EXPRESSION_SUBSCRIPT_LOOKUP",
        "EXPRESSION_FUNCTION_CALL",
        "EXPRESSION_MAKE_TUPLE",
        "EXPRESSION_MAKE_LIST",
        "EXPRESSION_MAKE_SET",
        "EXPRESSION_MAKE_SET_LITERAL",
        "EXPRESSION_TEMPLATE_STRING",
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


def _generateCallSource(expression):
    called_source = generateExpressionSource(expression.subnode_called)

    argument_sources = []

    args = expression.subnode_args
    if args is not None:
        if args.isExpressionMakeTuple():
            for element in args.subnode_elements:
                argument_sources.append(generateExpressionSource(element))
        else:
            for element in args.getCompileTimeConstant():
                argument_sources.append(_formatConstantElement(element, expression))

    kwargs = expression.subnode_kwargs
    if kwargs is not None:
        if kwargs.isExpressionMakeDict():
            for pair in kwargs.subnode_pairs:
                key = pair.getKeyCompileTimeConstant()
                value = generateExpressionSource(pair.getValueNode())
                argument_sources.append("%s=%s" % (key, value))
        else:
            for key, value in kwargs.getCompileTimeConstant().items():
                argument_sources.append(
                    "%s=%s" % (key, _formatConstantElement(value, expression))
                )

    return "%s(%s)" % (called_source, ", ".join(argument_sources))


def _generateListSource(expression):
    elements = []
    for element in expression.subnode_elements:
        elements.append(generateExpressionSource(element))

    return "[%s]" % ", ".join(elements)


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


def _generateMakeSetSource(expression):
    elements = expression.subnode_elements

    if not elements:
        return "set()"

    return "{%s}" % ", ".join(generateExpressionSource(element) for element in elements)


_template_string_conversion_characters = {
    1: "a",
    2: "r",
    3: "s",
}


def _escapeTemplateStringText(value):
    parts = []

    for char in value:
        if char == "{":
            parts.append("{{")
        elif char == "}":
            parts.append("}}")
        elif char == "\\":
            parts.append("\\\\")
        elif char == '"':
            parts.append('\\"')
        elif char == "\n":
            parts.append("\\n")
        elif char == "\r":
            parts.append("\\r")
        elif char == "\t":
            parts.append("\\t")
        elif ord(char) < 32 or ord(char) == 127:
            parts.append("\\x%02x" % ord(char))
        else:
            parts.append(char)

    return "".join(parts)


def _generateTemplateInterpolationSource(interpolation):
    value_source = generateExpressionSource(interpolation.subnode_value)

    conversion = interpolation.conversion

    if conversion > 0:
        conversion_character = _template_string_conversion_characters.get(
            conversion % 4
        )

        if conversion_character is None:
            raise PythonSourceGenerationError(
                "Unsupported conversion for template string source generation: %d"
                % conversion
            )

        value_source += "!" + conversion_character

    format_spec = interpolation.subnode_format_spec

    if format_spec is not None:
        if not format_spec.isCompileTimeConstant():
            raise PythonSourceGenerationError(
                "Unsupported dynamic format specifier for template string source generation"
            )

        value_source += ":" + _escapeTemplateStringText(
            format_spec.getCompileTimeConstant()
        )

    return "{%s}" % value_source


def _generateTemplateStringSource(expression):
    str_values = expression.str_values
    interpolations = expression.subnode_interpolations

    if not interpolations:
        if not str_values:
            return 't""'

        return 't"%s"' % _escapeTemplateStringText(str_values[0])

    if len(str_values) != len(interpolations) + 1:
        raise PythonSourceGenerationError(
            "Unexpected template string segment count for source generation"
        )

    parts = ['t"']

    for index, interpolation in enumerate(interpolations):
        parts.append(_escapeTemplateStringText(str_values[index]))
        parts.append(_generateTemplateInterpolationSource(interpolation))

    parts.append(_escapeTemplateStringText(str_values[-1]))
    parts.append('"')

    return "".join(parts)


def _generateDictSource(expression):
    items = []
    for pair in expression.subnode_pairs:
        key_source = repr(pair.getKeyCompileTimeConstant())
        value_source = generateExpressionSource(pair.getValueNode())
        items.append("%s: %s" % (key_source, value_source))

    return "{%s}" % ", ".join(items)


def _generateBuiltinMappingSource(expression, name):
    pos_arg = expression.subnode_pos_arg

    if pos_arg is None:
        return "%s(%s)" % (name, _generateDictSource(expression))

    pos_arg_source = generateExpressionSource(pos_arg)

    if not expression.subnode_pairs:
        return "%s(%s)" % (name, pos_arg_source)

    return "%s(%s, **%s)" % (name, pos_arg_source, _generateDictSource(expression))


def _generateBuiltinDictSource(expression):
    return _generateBuiltinMappingSource(expression, "dict")


def _generateBuiltinFrozendictSource(expression):
    return _generateBuiltinMappingSource(expression, "frozendict")


def _generateBuiltinFrozensetSource(expression):
    return "frozenset(%s)" % generateExpressionSource(expression.subnode_value)


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
        "Is": "is",
        "IsNot": "is not",
        "In": "in",
        "NotIn": "not in",
    }

    op = operators.get(comparator)
    if op is None:
        raise PythonSourceGenerationError("Unsupported comparison: %s" % comparator)

    left = generateExpressionSource(expression.subnode_left)
    right = generateExpressionSource(expression.subnode_right)
    return "%s %s %s" % (left, op, right)


def _generateConditionalAndOrSource(expression):
    left = generateExpressionSource(expression.subnode_left)
    right = generateExpressionSource(expression.subnode_right)
    op = "and" if expression.kind == "EXPRESSION_CONDITIONAL_AND" else "or"
    return "%s %s %s" % (left, op, right)


def _generateConditionalSourceExpression(expression):
    cond = generateExpressionSource(expression.subnode_condition)
    yes = generateExpressionSource(expression.subnode_expression_yes)
    no = generateExpressionSource(expression.subnode_expression_no)
    return "%s if %s else %s" % (yes, cond, no)


def _generateUnaryOperationSource(expression):
    if expression.isExpressionOperationNot():
        return "not %s" % _maybeParens(expression.subnode_operand)
    elif expression.isExpressionOperationUnarySub():
        return "-%s" % _maybeParens(expression.subnode_operand)
    elif expression.isExpressionOperationUnaryAdd():
        return "+%s" % _maybeParens(expression.subnode_operand)
    elif expression.isExpressionOperationUnaryInvert():
        return "~%s" % _maybeParens(expression.subnode_operand)
    elif expression.isExpressionOperationUnaryAbs():
        return "abs(%s)" % generateExpressionSource(expression.subnode_operand)
    elif expression.isExpressionOperationUnaryRepr():
        return "repr(%s)" % generateExpressionSource(expression.subnode_operand)
    else:
        raise PythonSourceGenerationError(
            "Unsupported unary operation for source generation: %s" % expression.kind
        )


def _generateYieldSource(expression):
    value = expression.subnode_value

    if value is None:
        return "(yield)"
    return "(yield %s)" % generateExpressionSource(value)


def _generateYieldFromSource(expression):
    value = expression.subnode_value
    return "(yield from %s)" % generateExpressionSource(value)


def _generateLambdaSource(expression):
    # `lambda x: y` - `EXPRESSION_FUNCTION_CREATION` with `FunctionRef` for `<lambda>`
    assert expression.isExpressionFunctionCreation()
    func_body = expression.subnode_function_ref.getFunctionBody()

    param_names = func_body.getParameters().getParameterNames()

    body = func_body.subnode_body

    if len(body.subnode_statements) != 1:
        raise PythonSourceGenerationError(
            "Unsupported lambda body for source generation: %s" % body
        )

    stmt = body.subnode_statements[0]

    if stmt.isStatementReturn() or stmt.isStatementReturnConstant():
        stmt_src = generateStatementSequenceSource(body, indent="")
        assert stmt_src.startswith("return "), stmt_src
        expr_src = stmt_src[len("return ") :]
        return "lambda %s: %s" % (", ".join(param_names), expr_src)

    raise PythonSourceGenerationError(
        "Unsupported lambda body statement for source generation: %s" % stmt.kind
    )


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


def _generateStatementsFrameSource(statement, indent):
    # Frames are only needed for C code generation of annotate functions that
    # fall back to it, the bytecode backed function gets the frame's statements
    # directly.
    return generateStatementSequenceSource(statement, indent=indent)


def _generateReturnSource(statement, indent):
    if statement.isStatementReturnConstant():
        value = _formatConstantElement(statement.getConstant(), statement)
        return "%sreturn %s" % (indent, value)
    else:
        expression = statement.subnode_expression
        value = generateExpressionSource(expression)
        return "%sreturn %s" % (indent, value)


_annotate_function_source_template = """\
def %(function_name)s(%(parameters)s):
%(body_source)s"""

_annotate_factory_source_template = """\
def %(factory_name)s(%(factory_parameters)s):
    def %(function_name)s(%(parameters)s):
%(body_source)s
    return %(function_name)s"""


# The ".0" argument of annotate functions is not a valid Python identifier,
# and is replaced in generated source with this name. A user variable of that
# name in an annotation falls back to compiled C code, where scopes are kept
# apart.
_annotate_argument_name = "_annotate_argument"


def generateFunctionSourceFromBody(function_body):
    """Generate a complete 'def ...' Python source from a function body.

    Notes:
        With closure variables, the function is wrapped in a factory taking
        them as parameters, so they become free variables of the function and
        can be resolved through real cells when the function is created.
    """
    closure_variables = function_body.getClosureVariables()

    function_name = function_body.getFunctionName()
    parameter_names = function_body.getParameters().getParameterNames()

    if closure_variables:
        indent = " " * 8
    else:
        indent = " " * 4

    parameter_spec = ", ".join(
        parameter_name if parameter_name.isidentifier() else _annotate_argument_name
        for parameter_name in parameter_names
    )

    body_source = generateStatementSequenceSource(
        function_body.subnode_body, indent=indent
    )

    if closure_variables:
        source = _annotate_factory_source_template % {
            "factory_name": "__annotate_factory__",
            "factory_parameters": ", ".join(
                variable.getName() for variable in closure_variables
            ),
            "function_name": function_name,
            "parameters": parameter_spec,
            "body_source": body_source,
        }
    else:
        source = _annotate_function_source_template % {
            "function_name": function_name,
            "parameters": parameter_spec,
            "body_source": body_source,
        }

    try:
        compile(source, function_body.getCodeName(), "exec")
    except SyntaxError as e:
        return code_generation_logger.sysexit(
            "Failed to generate valid Python source for '%s': %s\n\n%s"
            % (function_body.getCodeName(), e, source)
        )

    return source


def getFunctionCodeObjectFromSource(function_body, compiled):
    """Get the code object for a function generated from source.

    Notes:
        With closure variables, the source is wrapped in a factory, and the
        function code object is nested inside the factory's code object.

    Args:
        function_body: Function body node the source was generated for.
        compiled: Compiled source (module code object) to extract from.

    Returns:
        The code object of the generated function.
    """
    result = compiled.co_consts[0]

    if not function_body.getClosureVariables():
        return result

    for constant in result.co_consts:
        if (
            isinstance(constant, types.CodeType)
            and constant.co_name == function_body.getFunctionName()
        ):
            return constant

    raise PythonSourceGenerationError(
        "Could not find function code object in generated factory source for '%s'"
        % function_body.getCodeName()
    )


def _generateBuiltinNext1Source(expression):
    inner = generateExpressionSource(expression.subnode_value)
    return "next(iter(%s))" % inner


def _generateVariableRefSource(expression):
    variable = expression.variable

    if variable.isParameterVariable() and not variable.getName().isidentifier():
        return _annotate_argument_name

    if variable.getName() == _annotate_argument_name:
        raise PythonSourceGenerationError(
            "Variable name '%s' conflicts with the annotate function argument"
            % _annotate_argument_name
        )

    return variable.getName()


def _generateEllipsisSource(_expression):
    return "..."


def _generateBuiltinExceptionRefSource(expression):
    return expression.getBuiltinName()


def _generateImportModuleHardSource(expression):
    # Hard imports (e.g. `typing`) may be optimized away and not kept as a
    # global variable (e.g. `t` for `import typing as t` can be dead).
    # Try to find the original alias via trace collection.
    target = expression.getModuleName().asString()
    module = expression.getParentModule()
    alias = _findAliasForModule(module, target)

    if alias:
        return alias

    return "__import__(%r)" % target


def _generateImportModuleNameHardSource(expression):
    # These are `from module import name` names, e.g. `from typing import List`.
    # The import name is the local name, which is the module global resolved by
    # annotationlib, unless an `as` alias was used.
    import_name = expression.getImportName()
    module_name = expression.getModuleName()
    target = module_name.asString() if hasattr(module_name, "asString") else module_name
    module = expression.getParentModule()
    alias = _findAliasForModule(module, target)

    if alias:
        return "%s.%s" % (alias, import_name)

    return "__import__(%r).%s" % (target, import_name)


# ---------------------------------------------------------------------------
# Dispatch table

_expression_source_dispatch = {
    "EXPRESSION_CONSTANT_TYPE_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_DICT_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_LIST_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_SET_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_FROZENDICT_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_FROZENSET_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_TUPLE_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_TYPE_REF": _generateConstantTypeRefSource,
    "EXPRESSION_VARIABLE_REF": _generateVariableRefSource,
    "EXPRESSION_CONSTANT_STR_REF": _generateConstantStrRefSource,
    "EXPRESSION_CONSTANT_STR_EMPTY_REF": _generateConstantStrRefSource,
    "EXPRESSION_CONSTANT_UNICODE_REF": _generateConstantStrRefSource,
    "EXPRESSION_CONSTANT_UNICODE_EMPTY_REF": _generateConstantStrRefSource,
    "EXPRESSION_CONSTANT_BYTES_REF": _generateConstantBytesRefSource,
    "EXPRESSION_CONSTANT_BYTES_EMPTY_REF": _generateConstantBytesRefSource,
    "EXPRESSION_CONSTANT_BYTEARRAY_REF": _generateConstantBytearrayRefSource,
    "EXPRESSION_CONSTANT_INT_REF": _generateConstantIntRefSource,
    "EXPRESSION_CONSTANT_LONG_REF": _generateConstantIntRefSource,
    "EXPRESSION_CONSTANT_FLOAT_REF": _generateConstantFloatRefSource,
    "EXPRESSION_CONSTANT_COMPLEX_REF": _generateConstantComplexRefSource,
    "EXPRESSION_CONSTANT_NONE_REF": _generateConstantNoneRefSource,
    "EXPRESSION_CONSTANT_TRUE_REF": _generateConstantBoolRefSource,
    "EXPRESSION_CONSTANT_FALSE_REF": _generateConstantBoolRefSource,
    "EXPRESSION_CONSTANT_ELLIPSIS_REF": _generateEllipsisSource,
    "EXPRESSION_CONSTANT_SLICE_REF": _generateConstantSliceRefSource,
    "EXPRESSION_CONSTANT_XRANGE_REF": _generateConstantXrangeRefSource,
    "EXPRESSION_ATTRIBUTE_LOOKUP": _generateAttributeLookupSource,
    "EXPRESSION_SUBSCRIPT_LOOKUP": _generateSubscriptLookupSource,
    "EXPRESSION_OPERATION_BINARY_ADD": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_SUB": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_MULT": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_MAT_MULT": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_TRUE_DIV": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_FLOOR_DIV": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_MOD": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_POW": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_LSHIFT": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_RSHIFT": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_BIT_AND": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_BIT_OR": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_BIT_XOR": _generateBinaryOpSource,
    "EXPRESSION_FUNCTION_CALL": _generateFunctionCallSource,
    "EXPRESSION_CALL": _generateCallSource,
    "EXPRESSION_CALL_NO_KEYWORDS": _generateCallSource,
    "EXPRESSION_CALL_KEYWORDS_ONLY": _generateCallSource,
    "EXPRESSION_CALL_EMPTY": _generateCallSource,
    "EXPRESSION_MAKE_TUPLE": _generateTupleSource,
    "EXPRESSION_MAKE_LIST": _generateListSource,
    "EXPRESSION_MAKE_SET": _generateMakeSetSource,
    "EXPRESSION_MAKE_SET_LITERAL": _generateMakeSetSource,
    "EXPRESSION_TEMPLATE_STRING": _generateTemplateStringSource,
    "EXPRESSION_CONSTANT_UNION_TYPE": _generateGenericAliasSource,
    "EXPRESSION_CONSTANT_GENERIC_ALIAS": _generateGenericAliasSource,
    "EXPRESSION_CONSTANT_TUPLE_REF": _generateTupleConstantSource,
    "EXPRESSION_CONSTANT_TUPLE_MUTABLE_REF": _generateTupleConstantSource,
    "EXPRESSION_CONSTANT_TUPLE_EMPTY_REF": _generateTupleConstantSource,
    "EXPRESSION_CONSTANT_LIST_REF": _generateListConstantSource,
    "EXPRESSION_CONSTANT_LIST_EMPTY_REF": _generateListConstantSource,
    "EXPRESSION_CONSTANT_SET_REF": _generateSetConstantSource,
    "EXPRESSION_CONSTANT_SET_EMPTY_REF": _generateSetConstantSource,
    "EXPRESSION_CONSTANT_DICT_REF": _generateDictConstantSource,
    "EXPRESSION_CONSTANT_DICT_EMPTY_REF": _generateDictConstantSource,
    "EXPRESSION_CONSTANT_FROZENDICT_REF": _generateFrozendictConstantSource,
    "EXPRESSION_CONSTANT_FROZENDICT_EMPTY_REF": _generateFrozendictConstantSource,
    "EXPRESSION_CONSTANT_FROZENSET_REF": _generateFrozensetConstantSource,
    "EXPRESSION_CONSTANT_FROZENSET_EMPTY_REF": _generateFrozensetConstantSource,
    "EXPRESSION_MAKE_DICT": _generateDictSource,
    "EXPRESSION_BUILTIN_DICT": _generateBuiltinDictSource,
    "EXPRESSION_BUILTIN_FROZENDICT": _generateBuiltinFrozendictSource,
    "EXPRESSION_BUILTIN_FROZENSET": _generateBuiltinFrozensetSource,
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
    "EXPRESSION_COMPARISON_IS": _generateComparisonSource,
    "EXPRESSION_COMPARISON_IS_NOT": _generateComparisonSource,
    "EXPRESSION_COMPARISON_IN": _generateComparisonSource,
    "EXPRESSION_COMPARISON_NOT_IN": _generateComparisonSource,
    "EXPRESSION_CONDITIONAL_AND": _generateConditionalAndOrSource,
    "EXPRESSION_CONDITIONAL_OR": _generateConditionalAndOrSource,
    "EXPRESSION_CONDITIONAL": _generateConditionalSourceExpression,
    "EXPRESSION_OPERATION_NOT": _generateUnaryOperationSource,
    "EXPRESSION_OPERATION_UNARY_SUB": _generateUnaryOperationSource,
    "EXPRESSION_OPERATION_UNARY_ADD": _generateUnaryOperationSource,
    "EXPRESSION_OPERATION_UNARY_INVERT": _generateUnaryOperationSource,
    "EXPRESSION_OPERATION_UNARY_ABS": _generateUnaryOperationSource,
    "EXPRESSION_OPERATION_UNARY_REPR": _generateUnaryOperationSource,
    "EXPRESSION_YIELD": _generateYieldSource,
    "EXPRESSION_YIELD_FROM": _generateYieldFromSource,
    "EXPRESSION_FUNCTION_CREATION": _generateLambdaSource,
    "EXPRESSION_BUILTIN_EXCEPTION_REF": _generateBuiltinExceptionRefSource,
    "EXPRESSION_IMPORT_MODULE_HARD": _generateImportModuleHardSource,
    "EXPRESSION_IMPORT_MODULE_FIXED": _generateImportModuleHardSource,
    "EXPRESSION_IMPORT_MODULE_BUILTIN": _generateImportModuleHardSource,
    "EXPRESSION_IMPORT_MODULE_NAME_HARD_EXISTS": _generateImportModuleNameHardSource,
    "EXPRESSION_IMPORT_MODULE_NAME_HARD_MAYBE_EXISTS": _generateImportModuleNameHardSource,
}

_statement_source_dispatch = {
    "STATEMENT_CONDITIONAL": _generateConditionalSource,
    "STATEMENT_RAISE_EXCEPTION": _generateRaiseExceptionSource,
    "STATEMENT_RETURN": _generateReturnSource,
    "STATEMENT_RETURN_CONSTANT": _generateReturnSource,
    "STATEMENTS_FRAME_FUNCTION": _generateStatementsFrameSource,
}

_checked_dispatch_kinds = False


def _checkDispatchKinds():
    """Verify all source-generation kinds exist in C code generation."""
    # Singleton, pylint: disable=global-statement
    global _checked_dispatch_kinds

    if _checked_dispatch_kinds:
        return

    for kind in _expression_source_dispatch:
        if kind == "EXPRESSION_FUNCTION_CREATION":
            continue

        if kind not in getExpressionDispatchDict():
            raise NuitkaCodeDeficit(
                "Source generation expression kind %r is not in C dispatch" % kind
            )

    for kind in _statement_source_dispatch:
        # Frame statements are not in the dispatch dictionary, the C code
        # generation handles them manually in "_generateStatementSequenceCode".
        if kind == "STATEMENTS_FRAME_FUNCTION":
            continue

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
