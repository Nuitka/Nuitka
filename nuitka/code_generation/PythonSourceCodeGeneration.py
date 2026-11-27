#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for Python source from Nuitka node tree.

Used for generating bytecode-backed functions, if so decided. The main
important use is '__annotate__' functions.
"""

import keyword
import os
import re
import types

from nuitka.__past__ import GenericAlias, UnionType, frozendict, re_sub
from nuitka.Constants import EllipsisType, NoneType, NotImplementedType
from nuitka.Errors import NuitkaCodeDeficit
from nuitka.nodes.AttributeNodesGenerated import (
    attribute_classes,
    attribute_typed_classes,
)
from nuitka.nodes.HardImportNodes import (
    getBuiltinRefNodes,
    getHardImportNodeClasses,
)
from nuitka.PythonVersions import python_version
from nuitka.Tracing import code_generation_logger

from .CodeHelpers import getExpressionDispatchDict, getStatementDispatchDict
from .ConstantCodes import addDistributionMetadataValue


def getFunctionEntryPointIdentifier(function_identifier):
    return "impl_" + function_identifier


def getFunctionMakerIdentifier(function_identifier):
    return "MAKE_FUNCTION_" + function_identifier


class PythonSourceGenerationError(Exception):
    pass


# Operator precedence levels from lowest to highest, matching the Python
# grammar so sub-expressions are parenthesized precisely when needed.
_PREC_LAMBDA = 1
_PREC_CONDITIONAL = 2
_PREC_OR = 3
_PREC_AND = 4
_PREC_NOT = 5
_PREC_CMP = 6
_PREC_BIT_OR = 7
_PREC_BIT_XOR = 8
_PREC_BIT_AND = 9
_PREC_SHIFT = 10
_PREC_ADD = 11
_PREC_MULT = 12
_PREC_UNARY = 13
_PREC_POW = 14
_PREC_POSTFIX = 15
_PREC_ATOM = 16


def _getEnclosingVariableProvider(node):
    current = node.getParent()

    while current is not None and not current.isParentVariableProvider():
        current = current.getParent()

    return current


def _isNameShadowedInLocalOrClosureScope(node, name):
    current = _getEnclosingVariableProvider(node)

    if current is None or not current.isExpressionFunctionBodyBase():
        return False

    for parameter_name in current.getParameters().getParameterNames():
        source_name = (
            parameter_name if parameter_name.isidentifier() else _annotate_argument_name
        )
        if source_name == name:
            return True

    for closure_variable in current.getClosureVariables():
        if getAnnotateSourceVariableName(closure_variable) == name:
            return True

    if current.getClosureVariables() and current.getFunctionName() == name:
        return True

    return False


def _isBuiltinNameShadowed(node, builtin_name):
    current = _getEnclosingVariableProvider(node)

    if current is None:
        return False

    if _isNameShadowedInLocalOrClosureScope(node, builtin_name):
        return True

    module = current if current.isCompiledPythonModule() else current.getParentModule()

    if (
        builtin_name in module.variables
        and module.variables[builtin_name].hasDefiniteWrites() is not False
    ):
        return True

    return False


def _getBuiltinCallableSource(node, builtin_name):
    if _isBuiltinNameShadowed(node, builtin_name):
        if _isBuiltinNameShadowed(node, "__import__"):
            raise PythonSourceGenerationError(
                "Shadowed builtin '%s' cannot be accessed when '__import__' is also shadowed"
                % builtin_name
            )

        return "__import__('builtins').%s" % builtin_name

    return builtin_name


def _formatTypeSource(value, expression):
    """Format a type constant as Python source via module alias or '__import__'."""
    if value.__module__ in ("builtins", None):
        return _getBuiltinCallableSource(expression, value.__name__)

    source, _precedence = _formatHardImportRefSource(
        expression, value.__module__, value.__name__
    )
    return source


def _generateConstantTypeRefSource(expression):
    return (
        _formatTypeSource(expression.getCompileTimeConstant(), expression),
        _PREC_POSTFIX,
    )


def _formatConstantFloat(value, expression):
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
    if repr(real) in ("inf", "-inf", "nan") or repr(imag) in ("inf", "-inf", "nan"):
        return "complex(%s, %s)" % (
            _formatConstantFloat(real, expression),
            _formatConstantFloat(imag, expression),
        )

    return repr(value)


def _formatConstantRepr(value, expression):
    # pylint: disable=unused-argument
    return repr(value)


def _formatConstantStr(value, expression):
    # pylint: disable=unused-argument
    return str(value)


def _formatEllipsisValue(value, expression):
    # pylint: disable=unused-argument
    return "..."


def _formatNotImplementedValue(_value, expression):
    return _getBuiltinCallableSource(expression, "NotImplemented")


def _formatFunctionValue(value, expression):
    # pylint: disable=unused-argument
    return value.__name__


def _formatConstantSlice(value, expression):
    parts = [
        _formatConstantElement(value.start, expression),
        _formatConstantElement(value.stop, expression),
        _formatConstantElement(value.step, expression),
    ]

    while len(parts) > 1 and parts[-1] == "None":
        parts.pop()

    return "slice(%s)" % ", ".join(parts)


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
    NotImplementedType: _formatNotImplementedValue,
    slice: _formatConstantSlice,
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
    return (
        _formatConstantList(expression.getCompileTimeConstant(), expression),
        _PREC_ATOM,
    )


def _generateSetConstantSource(expression):
    return (
        _formatConstantSet(expression.getCompileTimeConstant(), expression),
        _PREC_POSTFIX,
    )


def _generateFrozensetConstantSource(expression):
    return (
        _formatConstantFrozenset(expression.getCompileTimeConstant(), expression),
        _PREC_POSTFIX,
    )


def _generateDictConstantSource(expression):
    return (
        _formatConstantDict(expression.getCompileTimeConstant(), expression),
        _PREC_ATOM,
    )


def _generateFrozendictConstantSource(expression):
    constant_value = expression.getCompileTimeConstant()

    if not constant_value:
        return "frozendict()", _PREC_POSTFIX

    return (
        "frozendict(%s)" % _formatConstantDict(constant_value, expression),
        _PREC_POSTFIX,
    )


def _getImportedAttributePath(node):
    """Return dotted module/attribute path represented by an import node, or 'None'."""
    if (
        node.isExpressionImportModuleHard()
        or node.isExpressionImportModuleFixed()
        or node.isExpressionImportModuleBuiltin()
    ):
        value_name = (
            node.getValueName()
            if hasattr(node, "getValueName")
            else node.getModuleName()
        )
        return value_name.asString() if hasattr(value_name, "asString") else value_name
    elif node.isExpressionImportName():
        parent_path = _getImportedAttributePath(node.subnode_module)
        if parent_path is not None:
            return "%s.%s" % (parent_path, node.getImportName())
    elif node.isExpressionBuiltinImport():
        name_node = node.subnode_name

        if name_node is not None and name_node.isExpressionConstantRef():
            module_name_str = name_node.getCompileTimeConstant()
            if isinstance(module_name_str, str):
                fromlist_node = node.subnode_fromlist
                has_fromlist = fromlist_node is not None and (
                    not fromlist_node.isCompileTimeConstant()
                    or bool(fromlist_node.getCompileTimeConstant())
                )
                return (
                    module_name_str if has_fromlist else module_name_str.split(".")[0]
                )
    elif node.isExpressionSysModulesRef():
        return "sys.modules"
    elif hasattr(node, "getModuleName") and hasattr(node, "getImportName"):
        module_name = node.getModuleName()
        module_str = (
            module_name.asString() if hasattr(module_name, "asString") else module_name
        )
        return "%s.%s" % (module_str, node.getImportName())

    return None


def _findModuleScopeAliasForPath(module, target_path, expression=None):
    """Return non-shadowed module variable name bound to 'target_path', or 'None'."""
    trace_collection = module.getTraceCollection()

    for variable, traces in trace_collection.variable_traces.items():
        if not variable.isModuleVariable():
            continue

        var_name = variable.getName()
        if expression is not None and _isNameShadowedInLocalOrClosureScope(
            expression, var_name
        ):
            continue

        matched = False
        for trace in traces.values():
            node = trace.getAttributeNode()
            if node is None:
                continue

            imported_path = _getImportedAttributePath(node)
            if imported_path != target_path:
                matched = False
                break

            matched = True

        if matched:
            return var_name

    return None


def _findAliasForModule(module, target):
    """Return module variable name imported for 'target', or 'None'."""
    return _findModuleScopeAliasForPath(module, target)


def _findModuleAccessAliasOnly(expression, target):
    module = expression.getParentModule()

    direct_alias = _findModuleScopeAliasForPath(module, target, expression)
    if direct_alias is not None:
        return direct_alias, _PREC_ATOM

    if "." in target:
        parts = target.split(".")
        for index in range(len(parts) - 1, 0, -1):
            prefix = ".".join(parts[:index])
            alias = _findModuleScopeAliasForPath(module, prefix, expression)
            if alias is not None:
                tail = parts[index:]
                dotted_expr = "%s.%s" % (alias, ".".join(tail))
                if target == "os.path":
                    return dotted_expr, _PREC_POSTFIX

                hasattr_fn = _getBuiltinCallableSource(expression, "hasattr")
                import_fn = _getBuiltinCallableSource(expression, "__import__")
                checks = " and ".join(
                    "%s(%s, %r)"
                    % (hasattr_fn, ".".join([alias] + tail[:pos]), tail[pos])
                    for pos in range(len(tail))
                )
                return (
                    "%s if %s else %s(%r, None, None, ('*',))"
                    % (dotted_expr, checks, import_fn, target),
                    _PREC_CONDITIONAL,
                )

    return None


def _formatModuleAccessSource(expression, target, module_to_import=None):
    found = _findModuleAccessAliasOnly(expression, target)
    if found is not None:
        return found

    if target in ("ntpath", "posixpath"):
        found_os_path = _findModuleAccessAliasOnly(expression, "os.path")
        if found_os_path is not None:
            return found_os_path

    import_fn = _getBuiltinCallableSource(expression, "__import__")
    imported_module_name = module_to_import if module_to_import is not None else target

    if imported_module_name != target:
        return "%s(%r)" % (import_fn, imported_module_name), _PREC_POSTFIX

    if "." in target:
        return "%s(%r, None, None, ('*',))" % (import_fn, target), _PREC_POSTFIX

    return "%s(%r)" % (import_fn, target), _PREC_POSTFIX


def _formatHardImportRefSource(expression, target, import_name):
    module = expression.getParentModule()

    direct_symbol = _findModuleScopeAliasForPath(
        module, "%s.%s" % (target, import_name), expression
    )
    if direct_symbol is None and target in ("ntpath", "posixpath"):
        direct_symbol = _findModuleScopeAliasForPath(
            module, "os.path.%s" % import_name, expression
        )
    if direct_symbol is not None:
        return direct_symbol, _PREC_ATOM

    module_source, precedence = _formatModuleAccessSource(expression, target)
    if precedence < _PREC_POSTFIX:
        module_source = "(%s)" % module_source
    return "%s.%s" % (module_source, import_name), _PREC_POSTFIX


def _generateGenericAliasSource(expression):
    value = expression.getCompileTimeConstant()
    s = str(value)

    module = expression.getParentModule()

    alias_cache = {}

    def _replaceAlias(match):
        tgt = match.group(1)

        if tgt not in alias_cache:
            alias_cache[tgt] = _findAliasForModule(module, tgt)

        alias = alias_cache[tgt]

        if alias:
            return alias + "."

        return match.group(0)

    source = re_sub(r"\b([^\W\d]\w*)\.", _replaceAlias, s, flags=re.UNICODE)
    precedence = (
        _PREC_BIT_OR if expression.isExpressionConstantUnionType() else _PREC_POSTFIX
    )
    return source, precedence


def _generateTupleConstantSource(expression):
    return (
        _formatConstantTuple(expression.getCompileTimeConstant(), expression),
        _PREC_ATOM,
    )


def _generateConstantStrRefSource(expression):
    return repr(expression.getCompileTimeConstant()), _PREC_ATOM


def _generateConstantBytesRefSource(expression):
    return repr(expression.getCompileTimeConstant()), _PREC_ATOM


def _getNumericLiteralPrecedence(source):
    if source.startswith("-"):
        return _PREC_UNARY

    return _PREC_ATOM


def _generateConstantIntRefSource(expression):
    source = repr(expression.getCompileTimeConstant())
    return source, _getNumericLiteralPrecedence(source)


def _generateConstantFloatRefSource(expression):
    source = _formatConstantFloat(expression.getCompileTimeConstant(), expression)
    return source, _getNumericLiteralPrecedence(source)


def _generateConstantComplexRefSource(expression):
    source = _formatConstantComplex(expression.getCompileTimeConstant(), expression)
    return source, _getNumericLiteralPrecedence(source)


def _generateConstantBytearrayRefSource(expression):
    return repr(expression.getCompileTimeConstant()), _PREC_POSTFIX


def _generateConstantSliceRefSource(expression):
    return (
        _formatConstantSlice(expression.getCompileTimeConstant(), expression),
        _PREC_POSTFIX,
    )


def _generateConstantXrangeRefSource(expression):
    value = expression.getCompileTimeConstant()

    parts = [
        _formatConstantElement(value.start, expression),
        _formatConstantElement(value.stop, expression),
    ]

    step = _formatConstantElement(value.step, expression)
    if step != "1":
        parts.append(step)

    return "range(%s)" % ", ".join(parts), _PREC_POSTFIX


def _generateConstantBoolRefSource(expression):
    constant = expression.getCompileTimeConstant()
    assert constant is True or constant is False
    return ("True" if constant is True else "False"), _PREC_ATOM


def _generateConstantNoneRefSource(_expression):
    return "None", _PREC_ATOM


def _formatMethodReceiverSource(expression):
    left = _generateSubExpressionSource(expression, _PREC_POSTFIX)

    # Decimal integer literals followed immediately by "." are lexed as floats
    # in Python (e.g. "1.__class__" is a SyntaxError), so parenthesize them.
    if left.isdigit():
        left = "(%s)" % left

    return left


def _generateAttributeLookupSource(expression):
    left = _formatMethodReceiverSource(expression.subnode_expression)
    attr = expression.getAttributeName()
    return "%s.%s" % (left, attr), _PREC_POSTFIX


def _formatConstantSliceSubscript(value, expression):
    start_source = (
        "" if value.start is None else _formatConstantElement(value.start, expression)
    )
    stop_source = (
        "" if value.stop is None else _formatConstantElement(value.stop, expression)
    )

    if value.step is None:
        return "%s:%s" % (start_source, stop_source)

    step_source = _formatConstantElement(value.step, expression)
    return "%s:%s:%s" % (start_source, stop_source, step_source)


def _formatConstantSubscriptElement(value, expression):
    if type(value) is slice:
        return _formatConstantSliceSubscript(value, expression)

    return _formatConstantElement(value, expression)


def _generateSubscriptItemSource(expression):
    if expression.isExpressionBuiltinSlice1():
        stop = expression.subnode_stop
        stop_source = (
            "" if stop.isExpressionConstantNoneRef() else generateExpressionSource(stop)
        )
        return ":%s" % stop_source
    elif expression.isExpressionBuiltinSlice2():
        start = expression.subnode_start
        stop = expression.subnode_stop
        start_source = (
            ""
            if start.isExpressionConstantNoneRef()
            else generateExpressionSource(start)
        )
        stop_source = (
            "" if stop.isExpressionConstantNoneRef() else generateExpressionSource(stop)
        )
        return "%s:%s" % (start_source, stop_source)
    elif expression.isExpressionBuiltinSlice3():
        start = expression.subnode_start
        stop = expression.subnode_stop
        step = expression.subnode_step
        start_source = (
            ""
            if start.isExpressionConstantNoneRef()
            else generateExpressionSource(start)
        )
        stop_source = (
            "" if stop.isExpressionConstantNoneRef() else generateExpressionSource(stop)
        )
        step_source = (
            "" if step.isExpressionConstantNoneRef() else generateExpressionSource(step)
        )
        return "%s:%s:%s" % (start_source, stop_source, step_source)
    elif expression.isExpressionConstantSliceRef():
        return _formatConstantSliceSubscript(
            expression.getCompileTimeConstant(), expression
        )
    else:
        return generateExpressionSource(expression)


def _formatSubscriptTupleItems(item_sources):
    if not item_sources:
        return "()"
    elif len(item_sources) == 1:
        return "%s," % item_sources[0]
    else:
        return ", ".join(item_sources)


def _generateSubscriptArgumentSource(subscript):
    if subscript.isExpressionMakeTuple():
        return _formatSubscriptTupleItems(
            [
                _generateSubscriptItemSource(element)
                for element in subscript.subnode_elements
            ]
        )
    elif subscript.isExpressionConstantTupleRef():
        return _formatSubscriptTupleItems(
            [
                _formatConstantSubscriptElement(element, subscript)
                for element in subscript.getCompileTimeConstant()
            ]
        )
    elif subscript.isExpressionBuiltinTuple() and _isUnpackListCall(
        subscript.subnode_value
    ):
        return _formatSubscriptTupleItems(
            _formatSequenceUnpackItems(subscript.subnode_value.subnode_values[0])
        )
    else:
        return _generateSubscriptItemSource(subscript)


def _generateSubscriptLookupSource(expression):
    looked_up = _generateSubExpressionSource(
        expression.subnode_expression, _PREC_POSTFIX
    )
    subscript = _generateSubscriptArgumentSource(expression.subnode_subscript)
    return "%s[%s]" % (looked_up, subscript), _PREC_POSTFIX


def _generateSubscriptForUnpackSource(expression):
    return _generateSubscriptLookupSource(expression)


def _generateSliceLookupSource(expression):
    looked_up = _generateSubExpressionSource(
        expression.subnode_expression, _PREC_POSTFIX
    )
    lower = expression.subnode_lower
    upper = expression.subnode_upper
    lower_source = "" if lower is None else generateExpressionSource(lower)
    upper_source = "" if upper is None else generateExpressionSource(upper)
    return "%s[%s:%s]" % (looked_up, lower_source, upper_source), _PREC_POSTFIX


def _generateImportlibReloadRefSource(expression):
    return _formatHardImportRefSource(expression, "importlib", "reload")


def _generateImportlibReloadCallSource(expression):
    callable_source, _precedence = _formatHardImportRefSource(
        expression, "importlib", "reload"
    )
    return (
        "%s(%s)"
        % (callable_source, generateExpressionSource(expression.subnode_module)),
        _PREC_POSTFIX,
    )


def _generateSysModulesRefSource(expression):
    return _formatHardImportRefSource(expression, "sys", "modules")


def _generateSysModulesCallSource(expression):
    arguments = [generateExpressionSource(expression.subnode_key)]

    default = getattr(expression, "subnode_default", None)

    if default is not None:
        arguments.append(generateExpressionSource(default))

    method_name = (
        "get"
        if (
            expression.isExpressionSysModulesGet2()
            or expression.isExpressionSysModulesGet3()
        )
        else "pop"
    )

    sys_modules_source, _precedence = _formatHardImportRefSource(
        expression, "sys", "modules"
    )
    return (
        "%s.%s(%s)" % (sys_modules_source, method_name, ", ".join(arguments)),
        _PREC_POSTFIX,
    )


_binary_operator_info = {
    "BitOr": ("|", _PREC_BIT_OR),
    "BitXor": ("^", _PREC_BIT_XOR),
    "BitAnd": ("&", _PREC_BIT_AND),
    "LShift": ("<<", _PREC_SHIFT),
    "RShift": (">>", _PREC_SHIFT),
    "Add": ("+", _PREC_ADD),
    "Sub": ("-", _PREC_ADD),
    "Mult": ("*", _PREC_MULT),
    "MatMult": ("@", _PREC_MULT),
    "TrueDiv": ("/", _PREC_MULT),
    "FloorDiv": ("//", _PREC_MULT),
    "OldDiv": ("/", _PREC_MULT),
    "Mod": ("%", _PREC_MULT),
    "Pow": ("**", _PREC_POW),
}


def _generateDivmodSource(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "divmod"),
            generateExpressionSource(expression.subnode_left),
            generateExpressionSource(expression.subnode_right),
        ),
        _PREC_POSTFIX,
    )


def _generateBinaryOpSource(expression):
    operator = expression.getOperator()

    operator_info = _binary_operator_info.get(operator)

    if operator_info is None:
        raise PythonSourceGenerationError(
            "Unsupported binary operator for source generation: %s" % operator
        )

    symbol, precedence = operator_info

    if operator == "Pow":
        # Exponentiation is right-associative and binds tighter than unary
        # operators on its left operand (e.g. "(-2) ** 2" vs "-2 ** 2").
        left = _generateSubExpressionSource(expression.subnode_left, _PREC_POSTFIX)
        right = _generateSubExpressionSource(expression.subnode_right, _PREC_POW)
    else:
        left = _generateSubExpressionSource(expression.subnode_left, precedence)
        right = _generateSubExpressionSource(expression.subnode_right, precedence + 1)

    return "%s %s %s" % (left, symbol, right), precedence


def _generatePairKeySource(pair):
    if (
        pair.isExpressionKeyValuePairConstantKey()
        or pair.isExpressionKeyValuePairConstantKeyValue()
    ):
        return _formatConstantElement(pair.getKeyCompileTimeConstant(), pair)

    return generateExpressionSource(pair.subnode_key)


def _generatePairValueSource(pair):
    if pair.isExpressionKeyValuePairConstantKeyValue():
        return _formatConstantElement(pair.getValueCompileTimeConstant(), pair)

    return generateExpressionSource(pair.subnode_value)


def _formatKeywordPairsArguments(pairs):
    arguments = []

    for pair in pairs:
        if (
            pair.isExpressionKeyValuePairConstantKey()
            or pair.isExpressionKeyValuePairConstantKeyValue()
        ):
            key = pair.getKeyCompileTimeConstant()
            if (
                isinstance(key, str)
                and key.isidentifier()
                and not keyword.iskeyword(key)
            ):
                arguments.append("%s=%s" % (key, _generatePairValueSource(pair)))
                continue

        arguments.append(
            "**{%s: %s}"
            % (_generatePairKeySource(pair), _generatePairValueSource(pair))
        )

    return arguments


def _getInternalHelperFunctionBody(expression):
    if expression.isExpressionFunctionCall():
        func = expression.subnode_function
        if func.isExpressionFunctionCreation():
            func_body = func.subnode_function_ref.getFunctionBody()
            if func_body.isExpressionFunctionPureBody():
                return func_body

    return None


def _isUnpackListCall(expression):
    helper_body = _getInternalHelperFunctionBody(expression)
    return helper_body is not None and helper_body.getFunctionName() == "_unpack_list"


def _formatSequenceUnpackItems(tuple_arg):
    items = []

    if tuple_arg.isExpressionMakeTuple():
        for item in tuple_arg.subnode_elements:
            if item.isExpressionMakeTuple() and len(item.subnode_elements) == 1:
                items.append(generateExpressionSource(item.subnode_elements[0]))
            elif (
                item.isExpressionConstantTupleRef()
                and len(item.getCompileTimeConstant()) == 1
            ):
                items.append(
                    _formatConstantElement(item.getCompileTimeConstant()[0], tuple_arg)
                )
            else:
                items.append("*" + _generateSubExpressionSource(item, _PREC_BIT_OR))
    else:
        for item in tuple_arg.getCompileTimeConstant():
            if type(item) is tuple and len(item) == 1:
                items.append(_formatConstantElement(item[0], tuple_arg))
            else:
                items.append("*" + _formatConstantElement(item, tuple_arg))

    return items


def _formatDictUnpackItems(tuple_arg):
    items = []

    if tuple_arg.isExpressionMakeDict():
        items.extend(
            "%s: %s" % (_generatePairKeySource(pair), _generatePairValueSource(pair))
            for pair in tuple_arg.subnode_pairs
        )
    elif tuple_arg.isExpressionMakeTuple():
        for item in tuple_arg.subnode_elements:
            if item.isExpressionMakeDict() and len(item.subnode_pairs) == 1:
                pair = item.subnode_pairs[0]
                items.append(
                    "%s: %s"
                    % (_generatePairKeySource(pair), _generatePairValueSource(pair))
                )
            elif (
                item.isExpressionConstantDictRef()
                and len(item.getCompileTimeConstant()) == 1
            ):
                key, value = next(iter(item.getCompileTimeConstant().items()))
                items.append(
                    "%s: %s"
                    % (
                        _formatConstantElement(key, tuple_arg),
                        _formatConstantElement(value, tuple_arg),
                    )
                )
            else:
                items.append("**" + _generateSubExpressionSource(item, _PREC_BIT_OR))
    else:
        for item in tuple_arg.getCompileTimeConstant():
            if type(item) is dict and len(item) == 1:
                key, value = next(iter(item.items()))
                items.append(
                    "%s: %s"
                    % (
                        _formatConstantElement(key, tuple_arg),
                        _formatConstantElement(value, tuple_arg),
                    )
                )
            else:
                items.append("**" + _formatConstantElement(item, tuple_arg))

    return items


def _appendPositionalCallArgs(argument_sources, args, context_node):
    if args.isExpressionMakeTuple():
        for element in args.subnode_elements:
            argument_sources.append(generateExpressionSource(element))
    else:
        for element in args.getCompileTimeConstant():
            argument_sources.append(_formatConstantElement(element, context_node))


def _appendKeywordCallArgs(argument_sources, kwargs, context_node):
    if kwargs.isExpressionMakeDict():
        argument_sources.extend(_formatKeywordPairsArguments(kwargs.subnode_pairs))
    else:
        for key, value in kwargs.getCompileTimeConstant().items():
            value_source = _formatConstantElement(value, context_node)
            if (
                isinstance(key, str)
                and key.isidentifier()
                and not keyword.iskeyword(key)
            ):
                argument_sources.append("%s=%s" % (key, value_source))
            else:
                argument_sources.append(
                    "**{%s: %s}"
                    % (_formatConstantElement(key, context_node), value_source)
                )


def _generateComplexCallHelperSource(expression, helper_body):
    param_names = helper_body.getParameters().getParameterNames()
    param_map = dict(zip(param_names, expression.subnode_values))

    called_source = _generateSubExpressionSource(param_map["called"], _PREC_POSTFIX)
    argument_sources = []

    if "args" in param_map:
        _appendPositionalCallArgs(argument_sources, param_map["args"], expression)

    if "star_arg_list" in param_map:
        star_list = param_map["star_arg_list"]
        if _isUnpackListCall(star_list):
            argument_sources.extend(
                _formatSequenceUnpackItems(star_list.subnode_values[0])
            )
        else:
            argument_sources.append(
                "*" + _generateSubExpressionSource(star_list, _PREC_BIT_OR)
            )

    if "kw" in param_map:
        _appendKeywordCallArgs(argument_sources, param_map["kw"], expression)

    if "star_arg_dict" in param_map:
        star_dict = param_map["star_arg_dict"]
        argument_sources.append(
            "**" + _generateSubExpressionSource(star_dict, _PREC_BIT_OR)
        )

    return "%s(%s)" % (called_source, ", ".join(argument_sources)), _PREC_POSTFIX


def _generateFunctionCallSource(expression):
    helper_body = _getInternalHelperFunctionBody(expression)
    if helper_body is not None:
        helper_name = helper_body.getFunctionName()
        if helper_name == "_unpack_list":
            return (
                "[%s]"
                % ", ".join(_formatSequenceUnpackItems(expression.subnode_values[0])),
                _PREC_ATOM,
            )
        if helper_name == "_unpack_set":
            return (
                "{%s}"
                % ", ".join(_formatSequenceUnpackItems(expression.subnode_values[0])),
                _PREC_ATOM,
            )
        if helper_name == "_unpack_dict":
            return (
                "{%s}"
                % ", ".join(_formatDictUnpackItems(expression.subnode_values[0])),
                _PREC_ATOM,
            )
        if helper_name.startswith("complex_call_helper_"):
            return _generateComplexCallHelperSource(expression, helper_body)

    called_source = _generateSubExpressionSource(
        expression.subnode_function, _PREC_POSTFIX
    )

    arg_sources = []
    for arg in expression.subnode_values:
        arg_sources.append(generateExpressionSource(arg))

    return "%s(%s)" % (called_source, ", ".join(arg_sources)), _PREC_POSTFIX


def _generateCallSource(expression):
    called_source = _generateSubExpressionSource(
        expression.subnode_called, _PREC_POSTFIX
    )

    argument_sources = []

    args = expression.subnode_args
    if args is not None:
        _appendPositionalCallArgs(argument_sources, args, expression)

    kwargs = expression.subnode_kwargs
    if kwargs is not None:
        _appendKeywordCallArgs(argument_sources, kwargs, expression)

    return "%s(%s)" % (called_source, ", ".join(argument_sources)), _PREC_POSTFIX


def _generateListSource(expression):
    elements = []
    for element in expression.subnode_elements:
        elements.append(generateExpressionSource(element))

    return "[%s]" % ", ".join(elements), _PREC_ATOM


def _generateTupleSource(expression):
    elements = []
    for element in expression.subnode_elements:
        elements.append(generateExpressionSource(element))

    if len(elements) == 0:
        return "()", _PREC_ATOM
    elif len(elements) == 1:
        return "(%s,)" % elements[0], _PREC_ATOM
    else:
        return "(%s)" % ", ".join(elements), _PREC_ATOM


def _generateMakeSetSource(expression):
    elements = expression.subnode_elements

    if not elements:
        return "set()", _PREC_POSTFIX

    return (
        "{%s}" % ", ".join(generateExpressionSource(element) for element in elements),
        _PREC_ATOM,
    )


_template_string_conversion_characters = {
    1: "a",
    2: "r",
    3: "s",
}


def _escapeFormattedStringText(value, in_format_spec=False):
    parts = []

    for char in value:
        code_point = ord(char)

        if char == "{":
            parts.append('{"{"}' if in_format_spec else "{{")
        elif char == "}":
            parts.append('{"}"}' if in_format_spec else "}}")
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
        elif code_point < 32 or code_point == 127:
            parts.append("\\x%02x" % code_point)
        elif 0xD800 <= code_point <= 0xDFFF:
            parts.append("\\u%04x" % code_point)
        else:
            parts.append(char)

    return "".join(parts)


def _escapeTemplateStringText(value):
    return _escapeFormattedStringText(value, in_format_spec=False)


def _generateTemplateInterpolationSource(interpolation):
    value_source = _generateSubExpressionSource(
        interpolation.subnode_value, _PREC_CONDITIONAL
    )

    if value_source.startswith("{"):
        value_source = " %s " % value_source

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

        value_source += ":" + _escapeFormattedStringText(
            format_spec.getCompileTimeConstant(), in_format_spec=True
        )

    return "{%s}" % value_source


def _generateTemplateStringSource(expression):
    str_values = expression.str_values
    interpolations = expression.subnode_interpolations

    if not interpolations:
        if not str_values:
            return 't""', _PREC_ATOM

        return 't"%s"' % _escapeTemplateStringText(str_values[0]), _PREC_ATOM

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

    return "".join(parts), _PREC_ATOM


def _unwrapFormattedValueConversion(inner):
    if (
        inner.isExpressionBuiltinStrP3()
        and inner.subnode_value is not None
        and inner.subnode_encoding is None
        and inner.subnode_errors is None
    ):
        return inner.subnode_value, "!s", "str"
    elif inner.isExpressionOperationUnaryRepr():
        return inner.subnode_operand, "!r", "repr"
    elif inner.isExpressionBuiltinAscii():
        return inner.subnode_value, "!a", "ascii"
    else:
        return inner, "", None


def _generateFStringPartSource(part, in_format_spec=False):
    if part.isExpressionConstantStrOrUnicodeRef():
        return _escapeFormattedStringText(
            part.getCompileTimeConstant(), in_format_spec=in_format_spec
        )
    elif part.isExpressionStringConcatenation():
        return "".join(
            _generateFStringPartSource(value, in_format_spec=in_format_spec)
            for value in part.subnode_values
        )
    elif part.isExpressionBuiltinFormat():
        value_node, conversion, _builtin_name = _unwrapFormattedValueConversion(
            part.subnode_value
        )

        value_source = _generateSubExpressionSource(value_node, _PREC_CONDITIONAL)
        if value_source.startswith("{"):
            value_source = " %s " % value_source

        format_spec = part.subnode_format_spec
        if format_spec is None:
            spec_source = ""
        else:
            spec_source = ":" + _generateFStringPartSource(
                format_spec, in_format_spec=True
            )

        return "{%s%s%s}" % (value_source, conversion, spec_source)
    elif part.isExpressionBuiltinAscii():
        value_source = _generateSubExpressionSource(
            part.subnode_value, _PREC_CONDITIONAL
        )
        if value_source.startswith("{"):
            value_source = " %s " % value_source

        return "{%s!a}" % value_source
    else:
        value_source = _generateSubExpressionSource(part, _PREC_CONDITIONAL)
        if value_source.startswith("{"):
            value_source = " %s " % value_source

        return "{%s}" % value_source


def _generateStringConcatenationSource(expression):
    parts = [_generateFStringPartSource(value) for value in expression.subnode_values]
    return 'f"%s"' % "".join(parts), _PREC_ATOM


def _generateBuiltinFormatSource(expression):
    _value_node, _conversion, conversion_builtin = _unwrapFormattedValueConversion(
        expression.subnode_value
    )

    if _isBuiltinNameShadowed(expression, "format") or (
        conversion_builtin is not None
        and _isBuiltinNameShadowed(expression, conversion_builtin)
    ):
        return 'f"%s"' % _generateFStringPartSource(expression), _PREC_ATOM

    value_source = generateExpressionSource(expression.subnode_value)
    format_spec = expression.subnode_format_spec

    if format_spec is None:
        return "format(%s)" % value_source, _PREC_POSTFIX

    return (
        "format(%s, %s)" % (value_source, generateExpressionSource(format_spec)),
        _PREC_POSTFIX,
    )


def _generateBuiltinStrSource(expression):
    callable_source = _getBuiltinCallableSource(expression, "str")
    value = expression.subnode_value

    if expression.isExpressionBuiltinStrP2():
        if value is None:
            return "%s()" % callable_source, _PREC_POSTFIX

        return (
            "%s(%s)" % (callable_source, generateExpressionSource(value)),
            _PREC_POSTFIX,
        )

    encoding = expression.subnode_encoding
    errors = expression.subnode_errors

    arguments = []

    if value is not None:
        arguments.append(generateExpressionSource(value))

        if encoding is not None:
            arguments.append(generateExpressionSource(encoding))
            if errors is not None:
                arguments.append(generateExpressionSource(errors))
        elif errors is not None:
            arguments.append("errors=%s" % generateExpressionSource(errors))
    else:
        if encoding is not None:
            arguments.append("encoding=%s" % generateExpressionSource(encoding))
        if errors is not None:
            arguments.append("errors=%s" % generateExpressionSource(errors))

    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateBuiltinAsciiSource(expression):
    if _isBuiltinNameShadowed(expression, "ascii"):
        return 'f"%s"' % _generateFStringPartSource(expression), _PREC_ATOM

    return (
        "ascii(%s)" % generateExpressionSource(expression.subnode_value),
        _PREC_POSTFIX,
    )


def _generateDictOperationFromkeysRefSource(expression):
    return (
        "%s.fromkeys" % _getBuiltinCallableSource(expression, "dict"),
        _PREC_POSTFIX,
    )


def _generateDictLiteralSource(expression):
    items = []
    for pair in expression.subnode_pairs:
        key_source = _generatePairKeySource(pair)
        value_source = _generatePairValueSource(pair)
        items.append("%s: %s" % (key_source, value_source))

    return "{%s}" % ", ".join(items)


def _generateDictSource(expression):
    return _generateDictLiteralSource(expression), _PREC_ATOM


def _generateBuiltinMappingSource(expression, name):
    callable_source = _getBuiltinCallableSource(expression, name)
    pos_arg = expression.subnode_pos_arg

    if pos_arg is None:
        return (
            "%s(%s)" % (callable_source, _generateDictLiteralSource(expression)),
            _PREC_POSTFIX,
        )

    pos_arg_source = generateExpressionSource(pos_arg)

    if not expression.subnode_pairs:
        return "%s(%s)" % (callable_source, pos_arg_source), _PREC_POSTFIX

    return (
        "%s(%s, **%s)"
        % (callable_source, pos_arg_source, _generateDictLiteralSource(expression)),
        _PREC_POSTFIX,
    )


def _generateBuiltinDictSource(expression):
    return _generateBuiltinMappingSource(expression, "dict")


def _generateBuiltinFrozendictSource(expression):
    return _generateBuiltinMappingSource(expression, "frozendict")


def _generateBuiltinFrozensetSource(expression):
    return (
        "%s(%s)"
        % (
            _getBuiltinCallableSource(expression, "frozenset"),
            generateExpressionSource(expression.subnode_value),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinSentinelSource(expression):
    if expression.subnode_repr_value is None:
        return (
            "sentinel(%s)" % generateExpressionSource(expression.subnode_name),
            _PREC_POSTFIX,
        )

    return (
        "sentinel(%s, repr=%s)"
        % (
            generateExpressionSource(expression.subnode_name),
            generateExpressionSource(expression.subnode_repr_value),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinType1Source(expression):
    return (
        "%s(%s)"
        % (
            _getBuiltinCallableSource(expression, "type"),
            generateExpressionSource(expression.subnode_value),
        ),
        _PREC_POSTFIX,
    )


def _generateSliceSource(expression):
    if expression.isExpressionBuiltinSlice1():
        arguments = [generateExpressionSource(expression.subnode_stop)]
    elif expression.isExpressionBuiltinSlice2():
        arguments = [
            generateExpressionSource(expression.subnode_start),
            generateExpressionSource(expression.subnode_stop),
        ]
    else:
        arguments = [
            generateExpressionSource(expression.subnode_start),
            generateExpressionSource(expression.subnode_stop),
            generateExpressionSource(expression.subnode_step),
        ]

    return (
        "%s(%s)"
        % (_getBuiltinCallableSource(expression, "slice"), ", ".join(arguments)),
        _PREC_POSTFIX,
    )


def _generateComparisonSource(expression):
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

    left = _generateSubExpressionSource(expression.subnode_left, _PREC_CMP + 1)
    right = _generateSubExpressionSource(expression.subnode_right, _PREC_CMP + 1)
    return "%s %s %s" % (left, op, right), _PREC_CMP


def _generateConditionalAndOrSource(expression):
    if expression.isExpressionConditionalAnd():
        op = "and"
        precedence = _PREC_AND
    else:
        op = "or"
        precedence = _PREC_OR

    left = _generateSubExpressionSource(expression.subnode_left, precedence)
    right = _generateSubExpressionSource(expression.subnode_right, precedence)
    return "%s %s %s" % (left, op, right), precedence


def _generateConditionalSourceExpression(expression):
    cond = _generateSubExpressionSource(
        expression.subnode_condition, _PREC_CONDITIONAL + 1
    )
    yes = _generateSubExpressionSource(
        expression.subnode_expression_yes, _PREC_CONDITIONAL + 1
    )
    no = _generateSubExpressionSource(expression.subnode_expression_no, _PREC_LAMBDA)
    return "%s if %s else %s" % (yes, cond, no), _PREC_CONDITIONAL


def _generateUnaryOperationSource(expression):
    if expression.isExpressionOperationNot():
        return (
            "not %s"
            % _generateSubExpressionSource(expression.subnode_operand, _PREC_NOT),
            _PREC_NOT,
        )
    elif expression.isExpressionOperationUnarySub():
        return (
            "-%s"
            % _generateSubExpressionSource(expression.subnode_operand, _PREC_UNARY),
            _PREC_UNARY,
        )
    elif expression.isExpressionOperationUnaryAdd():
        return (
            "+%s"
            % _generateSubExpressionSource(expression.subnode_operand, _PREC_UNARY),
            _PREC_UNARY,
        )
    elif expression.isExpressionOperationUnaryInvert():
        return (
            "~%s"
            % _generateSubExpressionSource(expression.subnode_operand, _PREC_UNARY),
            _PREC_UNARY,
        )
    elif expression.isExpressionOperationUnaryAbs():
        return (
            "%s(%s)"
            % (
                _getBuiltinCallableSource(expression, "abs"),
                generateExpressionSource(expression.subnode_operand),
            ),
            _PREC_POSTFIX,
        )
    elif expression.isExpressionOperationUnaryRepr():
        return (
            "%s(%s)"
            % (
                _getBuiltinCallableSource(expression, "repr"),
                generateExpressionSource(expression.subnode_operand),
            ),
            _PREC_POSTFIX,
        )
    else:
        raise PythonSourceGenerationError(
            "Unsupported unary operation for source generation: %s" % expression.kind
        )


def _generateYieldSource(expression):
    value = expression.subnode_value

    if value is None:
        return "(yield)", _PREC_ATOM
    return "(yield %s)" % generateExpressionSource(value), _PREC_ATOM


def _generateYieldFromSource(expression):
    value = expression.subnode_value
    return "(yield from %s)" % generateExpressionSource(value), _PREC_ATOM


def _extractLambdaKwDefaultSources(kw_defaults, expression):
    if kw_defaults is None:
        return {}

    if kw_defaults.isExpressionMakeDict():
        kw_default_sources = {}

        for pair in kw_defaults.subnode_pairs:
            if (
                pair.isExpressionKeyValuePairConstantKey()
                or pair.isExpressionKeyValuePairConstantKeyValue()
            ):
                key = pair.getKeyCompileTimeConstant()
            elif pair.subnode_key.isCompileTimeConstant():
                key = pair.subnode_key.getCompileTimeConstant()
            else:
                raise PythonSourceGenerationError(
                    "Unsupported non-constant lambda keyword default key: %s"
                    % pair.kind
                )

            kw_default_sources[key] = _generatePairValueSource(pair)

        return kw_default_sources

    if kw_defaults.isCompileTimeConstant():
        kw_defaults_value = kw_defaults.getCompileTimeConstant()
        if type(kw_defaults_value) is dict:
            return dict(
                (key, _formatConstantElement(value, expression))
                for key, value in kw_defaults_value.items()
            )

    raise PythonSourceGenerationError(
        "Unsupported lambda kw_defaults node for source generation: %s"
        % kw_defaults.kind
    )


def _formatLambdaParameters(expression, func_body):
    parameters = func_body.getParameters()

    pos_only_count = parameters.getPosOnlyParameterCount()
    all_pos_args = parameters.getArgumentNames()
    defaults = expression.subnode_defaults
    assert len(defaults) <= len(all_pos_args), (defaults, all_pos_args)
    first_default_idx = len(all_pos_args) - len(defaults)

    param_sources = []

    for idx, name in enumerate(all_pos_args):
        if idx < first_default_idx:
            param_sources.append(name)
        else:
            param_sources.append(
                "%s=%s"
                % (name, generateExpressionSource(defaults[idx - first_default_idx]))
            )

        if pos_only_count and idx == pos_only_count - 1:
            param_sources.append("/")

    list_star_arg = parameters.getStarListArgumentName()
    kw_only_args = parameters.getKwOnlyParameterNames()

    if list_star_arg is not None:
        param_sources.append("*%s" % list_star_arg)
    elif kw_only_args:
        param_sources.append("*")

    kw_default_sources = _extractLambdaKwDefaultSources(
        expression.subnode_kw_defaults, expression
    )

    for name in kw_only_args:
        if name in kw_default_sources:
            param_sources.append("%s=%s" % (name, kw_default_sources[name]))
        else:
            param_sources.append(name)

    dict_star_arg = parameters.getStarDictArgumentName()
    if dict_star_arg is not None:
        param_sources.append("**%s" % dict_star_arg)

    return param_sources


def _generateLambdaSource(expression):
    assert expression.isExpressionFunctionCreation()

    func_body = expression.subnode_function_ref.getFunctionBody()

    if (
        expression.subnode_annotations is not None
        or expression.subnode_type_params is not None
        or func_body.getFunctionName() != "<lambda>"
    ):
        raise PythonSourceGenerationError(
            "Unsupported function creation for lambda source generation: %s"
            % func_body.getFunctionName()
        )

    body = func_body.subnode_body

    while body is not None and len(body.subnode_statements) == 1:
        stmt = body.subnode_statements[0]
        if stmt.isStatementsFrameFunction():
            body = stmt
        else:
            break
    else:
        raise PythonSourceGenerationError(
            "Unsupported lambda body for source generation: %s" % body
        )

    if stmt.isStatementReturnConstant():
        expr_src = _formatConstantElement(stmt.getConstant(), stmt)
    elif stmt.isStatementReturn():
        expr_src = generateExpressionSource(stmt.subnode_expression)
    else:
        raise PythonSourceGenerationError(
            "Unsupported lambda body statement for source generation: %s" % stmt.kind
        )

    param_sources = _formatLambdaParameters(expression, func_body)
    if param_sources:
        return "lambda %s: %s" % (", ".join(param_sources), expr_src), _PREC_LAMBDA

    return "lambda: %s" % expr_src, _PREC_LAMBDA


def generateStatementSequenceSource(statement_seq, indent=""):
    assert statement_seq is not None
    assert statement_seq.subnode_statements, statement_seq

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


def _generateSysModulesAssignmentSource(statement, indent):
    return "%s%s[%s] = %s" % (
        indent,
        _generateSubExpressionSource(statement.subnode_subscribed, _PREC_POSTFIX),
        _generateSubscriptArgumentSource(statement.subnode_subscript),
        generateExpressionSource(statement.subnode_source),
    )


def _generateSysModulesDelSource(statement, indent):
    return "%sdel %s[%s]" % (
        indent,
        _generateSubExpressionSource(statement.subnode_subscribed, _PREC_POSTFIX),
        _generateSubscriptArgumentSource(statement.subnode_subscript),
    )


def _generateConditionalSource(statement, indent):
    condition = generateExpressionSource(statement.subnode_condition)

    if statement.subnode_yes_branch is None:
        yes_body = "%s    pass" % indent
    else:
        yes_body = generateStatementSequenceSource(
            statement.subnode_yes_branch, indent=indent + "    "
        )

    if statement.subnode_no_branch is None:
        return "%sif %s:\n%s" % (indent, condition, yes_body)
    else:
        no_body = generateStatementSequenceSource(
            statement.subnode_no_branch, indent=indent + "    "
        )

        return "%sif %s:\n%s\n%selse:\n%s" % (
            indent,
            condition,
            yes_body,
            indent,
            no_body,
        )


def _formatRaiseExceptionWithValueSource(
    statement, exception_type_node, exception_value
):
    if python_version < 0x300:
        return "%s, %s" % (
            generateExpressionSource(exception_type_node),
            generateExpressionSource(exception_value),
        )

    exception_type = _generateSubExpressionSource(exception_type_node, _PREC_POSTFIX)

    if exception_value.isExpressionMakeTuple():
        arg_sources = [
            generateExpressionSource(element)
            for element in exception_value.subnode_elements
        ]
        return "%s(%s)" % (exception_type, ", ".join(arg_sources))

    if (
        exception_value.isCompileTimeConstant()
        and type(exception_value.getCompileTimeConstant()) is tuple
    ):
        arg_sources = [
            _formatConstantElement(element, statement)
            for element in exception_value.getCompileTimeConstant()
        ]
        return "%s(%s)" % (exception_type, ", ".join(arg_sources))

    if exception_value.isExpressionConstantNoneRef():
        return "%s()" % exception_type

    return "%s(%s)" % (exception_type, generateExpressionSource(exception_value))


def _generateRaiseExceptionSource(statement, indent):
    exception_type_node = statement.subnode_exception_type
    exception_value = statement.subnode_exception_value
    exception_trace = statement.subnode_exception_trace
    exception_cause = statement.subnode_exception_cause

    if exception_cause is not None:
        assert exception_value is None
        assert exception_trace is None
        return "%sraise %s from %s" % (
            indent,
            generateExpressionSource(exception_type_node),
            generateExpressionSource(exception_cause),
        )

    if exception_trace is not None:
        if python_version < 0x300:
            value_source = (
                "None"
                if exception_value is None
                else generateExpressionSource(exception_value)
            )
            return "%sraise %s, %s, %s" % (
                indent,
                generateExpressionSource(exception_type_node),
                value_source,
                generateExpressionSource(exception_trace),
            )

        raise PythonSourceGenerationError(
            "Unsupported raise statement with traceback for source generation"
        )

    if exception_value is not None:
        return "%sraise %s" % (
            indent,
            _formatRaiseExceptionWithValueSource(
                statement, exception_type_node, exception_value
            ),
        )

    return "%sraise %s" % (indent, generateExpressionSource(exception_type_node))


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


def getAnnotateSourceVariableName(variable):
    """Translate a Nuitka variable name (e.g. containing '$') into a valid Python identifier."""
    variable_name = variable.getName()

    if variable_name.isidentifier():
        return variable_name

    # A leading underscore allows checking for identifier continuation
    # characters, which includes digits, but not e.g. "$".
    result = "".join(
        char if ("_" + char).isidentifier() else "_%x_" % ord(char)
        for char in variable_name
    )

    if not result.isidentifier():
        result = "_" + result

    return result


def getAnnotateClosureVariables(function_body):
    return tuple(
        sorted(
            function_body.getClosureVariables(),
            key=getAnnotateSourceVariableName,
        )
    )


def generateFunctionSourceFromBody(function_body):
    """Generate a complete 'def ...' Python source from a function body.

    Notes:
        With closure variables, the function is wrapped in a factory taking
        them as parameters, so they become free variables of the function and
        can be resolved through real cells when the function is created.
    """
    closure_variables = getAnnotateClosureVariables(function_body)

    function_name = function_body.getFunctionName()
    parameter_names = function_body.getParameters().getParameterNames()

    if closure_variables:
        indent = " " * 8
    else:
        indent = " " * 4

    parameter_source_names = [
        parameter_name if parameter_name.isidentifier() else _annotate_argument_name
        for parameter_name in parameter_names
    ]

    closure_source_names = [
        getAnnotateSourceVariableName(variable) for variable in closure_variables
    ]

    if len(set(closure_source_names)) != len(closure_source_names) or set(
        closure_source_names
    ).intersection(parameter_source_names):
        raise PythonSourceGenerationError(
            "Closure variable source names of annotate function '%s' collide"
            % function_body.getCodeName()
        )

    parameter_spec = ", ".join(parameter_source_names)

    assert function_body.subnode_body is not None, function_body

    body_source = generateStatementSequenceSource(
        function_body.subnode_body, indent=indent
    )

    if closure_variables:
        source = _annotate_factory_source_template % {
            "factory_name": "__annotate_factory__",
            "factory_parameters": ", ".join(
                getAnnotateSourceVariableName(variable)
                for variable in closure_variables
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
    """Extract the generated function code object (unwrapping closure factory if used)."""
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
    value = expression.subnode_value

    if value.isExpressionBuiltinIterForUnpack():
        return (
            "(lambda _v: [e for (e,) in (_v,)][0])(%s)"
            % generateExpressionSource(value.subnode_value),
            _PREC_POSTFIX,
        )

    return (
        "%s(%s)"
        % (
            _getBuiltinCallableSource(expression, "next"),
            generateExpressionSource(value),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinNext2Source(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "next"),
            generateExpressionSource(expression.subnode_iterator),
            generateExpressionSource(expression.subnode_default),
        ),
        _PREC_POSTFIX,
    )


def _makeSingleArgBuiltinSourceHandler(builtin_name, child_attr="subnode_value"):
    def _handler(expression):
        return (
            "%s(%s)"
            % (
                _getBuiltinCallableSource(expression, builtin_name),
                generateExpressionSource(getattr(expression, child_attr)),
            ),
            _PREC_POSTFIX,
        )

    return _handler


def _generateBuiltinTupleSource(expression):
    value = expression.subnode_value
    if _isUnpackListCall(value):
        items = _formatSequenceUnpackItems(value.subnode_values[0])
        if len(items) == 1:
            return "(%s,)" % items[0], _PREC_ATOM
        return "(%s)" % ", ".join(items), _PREC_ATOM

    return (
        "%s(%s)"
        % (
            _getBuiltinCallableSource(expression, "tuple"),
            generateExpressionSource(value),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinGlobalsSource(expression):
    return "%s()" % _getBuiltinCallableSource(expression, "globals"), _PREC_POSTFIX


def _generateBuiltinLocalsSource(expression):
    return "%s()" % _getBuiltinCallableSource(expression, "locals"), _PREC_POSTFIX


def _generateBuiltinInputSource(expression):
    callable_source = _getBuiltinCallableSource(expression, "input")
    prompt = expression.subnode_prompt

    if prompt is None:
        return "%s()" % callable_source, _PREC_POSTFIX

    return (
        "%s(%s)" % (callable_source, generateExpressionSource(prompt)),
        _PREC_POSTFIX,
    )


def _formatOptionalArgumentsCall(callable_source, arg_specs):
    """Format positional/optional arguments, switching to 'name=val' once a 'None' is skipped."""
    arguments = []
    use_keyword = False

    for name, node in arg_specs:
        if node is None:
            use_keyword = True
            continue

        value_source = generateExpressionSource(node)
        if use_keyword:
            arguments.append("%s=%s" % (name, value_source))
        else:
            arguments.append(value_source)

    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateBuiltinInt2Source(expression):
    builtin_name = (
        "long" if (str is bytes and expression.isExpressionBuiltinLong2()) else "int"
    )
    callable_source = _getBuiltinCallableSource(expression, builtin_name)
    value = expression.subnode_value
    base_source = generateExpressionSource(expression.subnode_base)

    if value is None:
        return "%s(base=%s)" % (callable_source, base_source), _PREC_POSTFIX

    return (
        "%s(%s, %s)" % (callable_source, generateExpressionSource(value), base_source),
        _PREC_POSTFIX,
    )


def _generateBuiltinComplex2Source(expression):
    callable_source = _getBuiltinCallableSource(expression, "complex")
    real = expression.subnode_real
    imag_source = generateExpressionSource(expression.subnode_imag)

    if real is None:
        return "%s(imag=%s)" % (callable_source, imag_source), _PREC_POSTFIX

    return (
        "%s(%s, %s)" % (callable_source, generateExpressionSource(real), imag_source),
        _PREC_POSTFIX,
    )


def _generateBuiltinBytes3Source(expression):
    callable_source = _getBuiltinCallableSource(expression, "bytes")
    return _formatOptionalArgumentsCall(
        callable_source,
        (
            ("source", expression.subnode_value),
            ("encoding", expression.subnode_encoding),
            ("errors", expression.subnode_errors),
        ),
    )


def _generateBuiltinUnicodeP2Source(expression):
    callable_source = _getBuiltinCallableSource(
        expression, "unicode" if str is bytes else "str"
    )
    return _formatOptionalArgumentsCall(
        callable_source,
        (
            ("string", expression.subnode_value),
            ("encoding", expression.subnode_encoding),
            ("errors", expression.subnode_errors),
        ),
    )


def _generateBuiltinBytearray3Source(expression):
    callable_source = _getBuiltinCallableSource(expression, "bytearray")
    return _formatOptionalArgumentsCall(
        callable_source,
        (
            ("source", expression.subnode_string),
            ("encoding", expression.subnode_encoding),
            ("errors", expression.subnode_errors),
        ),
    )


def _generateBuiltinRangeSource(expression):
    is_xrange_p2 = str is bytes and (
        expression.isExpressionBuiltinXrange1()
        or expression.isExpressionBuiltinXrange2()
        or expression.isExpressionBuiltinXrange3()
    )
    callable_source = _getBuiltinCallableSource(
        expression, "xrange" if is_xrange_p2 else "range"
    )

    arguments = [generateExpressionSource(expression.subnode_low)]
    high = getattr(expression, "subnode_high", None)
    if high is not None:
        arguments.append(generateExpressionSource(high))
        step = getattr(expression, "subnode_step", None)
        if step is not None:
            arguments.append(generateExpressionSource(step))

    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateBuiltinIter2Source(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "iter"),
            generateExpressionSource(expression.subnode_callable_arg),
            generateExpressionSource(expression.subnode_sentinel),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinSumSource(expression):
    callable_source = _getBuiltinCallableSource(expression, "sum")
    arguments = [generateExpressionSource(expression.subnode_sequence)]
    start = getattr(expression, "subnode_start", None)
    if start is not None:
        arguments.append(generateExpressionSource(start))

    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateBuiltinEnumerateSource(expression):
    callable_source = _getBuiltinCallableSource(expression, "enumerate")
    arguments = [generateExpressionSource(expression.subnode_sequence)]
    start = getattr(expression, "subnode_start", None)
    if start is not None:
        arguments.append(generateExpressionSource(start))

    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateBuiltinZipSource(expression):
    callable_source = _getBuiltinCallableSource(expression, "zip")
    arguments = [
        generateExpressionSource(element) for element in expression.subnode_values
    ]
    strict = getattr(expression, "subnode_strict", None)
    if strict is not None:
        arguments.append("strict=%s" % generateExpressionSource(strict))

    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateBuiltinGetattrSource(expression):
    callable_source = _getBuiltinCallableSource(expression, "getattr")
    arguments = [
        generateExpressionSource(expression.subnode_expression),
        generateExpressionSource(expression.subnode_name),
    ]
    default = expression.subnode_default
    if default is not None:
        arguments.append(generateExpressionSource(default))

    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateBuiltinSetattrSource(expression):
    return (
        "%s(%s, %s, %s)"
        % (
            _getBuiltinCallableSource(expression, "setattr"),
            generateExpressionSource(expression.subnode_expression),
            generateExpressionSource(expression.subnode_name),
            generateExpressionSource(expression.subnode_value),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinHasattrSource(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "hasattr"),
            generateExpressionSource(expression.subnode_expression),
            generateExpressionSource(expression.subnode_name),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinDelattrSource(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "delattr"),
            generateExpressionSource(expression.subnode_expression),
            generateExpressionSource(expression.subnode_name),
        ),
        _PREC_POSTFIX,
    )


def _generateAttributeCheckSource(expression):
    return (
        "%s(%s, %r)"
        % (
            _getBuiltinCallableSource(expression, "hasattr"),
            generateExpressionSource(expression.subnode_expression),
            expression.getAttributeName(),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinIsinstanceSource(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "isinstance"),
            generateExpressionSource(expression.subnode_instance),
            generateExpressionSource(expression.subnode_classes),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinIssubclassSource(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "issubclass"),
            generateExpressionSource(expression.subnode_cls),
            generateExpressionSource(expression.subnode_classes),
        ),
        _PREC_POSTFIX,
    )


def _generateTypeCheckSource(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "isinstance"),
            generateExpressionSource(expression.subnode_cls),
            _getBuiltinCallableSource(expression, "type"),
        ),
        _PREC_POSTFIX,
    )


def _generateSubtypeCheckSource(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "issubclass"),
            generateExpressionSource(expression.subnode_left),
            generateExpressionSource(expression.subnode_right),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinType3Source(expression):
    return (
        "%s(%s, %s, %s)"
        % (
            _getBuiltinCallableSource(expression, "type"),
            generateExpressionSource(expression.subnode_type_name),
            generateExpressionSource(expression.subnode_bases),
            generateExpressionSource(expression.subnode_dict_arg),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinSuper0Source(expression):
    type_arg = expression.subnode_type_arg
    object_arg = expression.subnode_object_arg
    enclosing_provider = _getEnclosingVariableProvider(expression)

    if (
        not _isBuiltinNameShadowed(expression, "super")
        and enclosing_provider is not None
        and enclosing_provider.isExpressionFunctionBodyBase()
        and type_arg.isExpressionVariableRef()
        and type_arg.variable.getName() == "__class__"
        and object_arg.isExpressionVariableRef()
        and object_arg.variable.isParameterVariable()
        and object_arg.variable.getOwner() is enclosing_provider
    ):
        parameter_names = enclosing_provider.getParameters().getParameterNames()
        if parameter_names and object_arg.variable.getName() == parameter_names[0]:
            return "super()", _PREC_POSTFIX

    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "super"),
            generateExpressionSource(type_arg),
            generateExpressionSource(object_arg),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinSuper1Source(expression):
    return (
        "%s(%s)"
        % (
            _getBuiltinCallableSource(expression, "super"),
            generateExpressionSource(expression.subnode_type_arg),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinSuper2Source(expression):
    return (
        "%s(%s, %s)"
        % (
            _getBuiltinCallableSource(expression, "super"),
            generateExpressionSource(expression.subnode_type_arg),
            generateExpressionSource(expression.subnode_object_arg),
        ),
        _PREC_POSTFIX,
    )


def _generateBuiltinMakeExceptionSource(expression):
    callable_source = _getBuiltinCallableSource(
        expression, expression.getExceptionName()
    )
    arguments = [generateExpressionSource(arg) for arg in expression.subnode_args]

    for kw_name in ("name", "path", "obj"):
        kw_node = getattr(expression, "subnode_" + kw_name, None)
        if kw_node is not None:
            arguments.append("%s=%s" % (kw_name, generateExpressionSource(kw_node)))

    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateBuiltinCompileSource(expression):
    callable_source = _getBuiltinCallableSource(expression, "compile")
    arg_specs = [
        ("source", expression.subnode_source),
        ("filename", expression.subnode_filename),
        ("mode", expression.subnode_mode),
        ("flags", expression.subnode_flags),
        ("dont_inherit", expression.subnode_dont_inherit),
    ]

    if expression.isExpressionBuiltinCompileSince3():
        arg_specs.append(("optimize", expression.subnode_optimize))

    return _formatOptionalArgumentsCall(callable_source, tuple(arg_specs))


def _generateBuiltinEvalExecSource(expression):
    if expression.isExpressionBuiltinEval():
        builtin_name = "eval"
    elif expression.isExpressionBuiltinExec():
        builtin_name = "exec"
    else:
        builtin_name = "execfile"

    callable_source = _getBuiltinCallableSource(expression, builtin_name)
    arg_specs = [
        ("source", expression.subnode_source_code),
        ("globals", expression.subnode_globals_arg),
        ("locals", expression.subnode_locals_arg),
    ]
    closure = getattr(expression, "subnode_closure", None)
    if closure is not None:
        arg_specs.append(("closure", closure))

    return _formatOptionalArgumentsCall(callable_source, arg_specs)


def _generateBuiltinImportSource(expression):
    callable_source = _getBuiltinCallableSource(expression, "__import__")
    return _formatOptionalArgumentsCall(
        callable_source,
        (
            ("name", expression.subnode_name),
            ("globals", expression.subnode_globals_arg),
            ("locals", expression.subnode_locals_arg),
            ("fromlist", expression.subnode_fromlist),
            ("level", expression.subnode_level),
        ),
    )


def _generateDictOperationItemSource(expression):
    dict_source = _generateSubExpressionSource(
        expression.subnode_dict_arg, _PREC_POSTFIX
    )
    key_source = generateExpressionSource(expression.subnode_key)
    return "%s[%s]" % (dict_source, key_source), _PREC_POSTFIX


def _generateDictOperationInSource(expression):
    op = "not in" if expression.isExpressionDictOperationNotIn() else "in"
    key_source = _generateSubExpressionSource(expression.subnode_key, _PREC_CMP + 1)
    dict_source = _generateSubExpressionSource(
        expression.subnode_dict_arg, _PREC_CMP + 1
    )
    return "%s %s %s" % (key_source, op, dict_source), _PREC_CMP


def _generateDictOperationHaskeySource(expression):
    if str is bytes:
        receiver = _formatMethodReceiverSource(expression.subnode_dict_arg)
        return (
            "%s.has_key(%s)"
            % (receiver, generateExpressionSource(expression.subnode_key)),
            _PREC_POSTFIX,
        )

    key_source = _generateSubExpressionSource(expression.subnode_key, _PREC_CMP + 1)
    dict_source = _generateSubExpressionSource(
        expression.subnode_dict_arg, _PREC_CMP + 1
    )
    return "%s in %s" % (key_source, dict_source), _PREC_CMP


_method_operation_source_handlers = {}


def _makeMethodOperationSourceHandler(method_name):
    handler = _method_operation_source_handlers.get(method_name)
    if handler is not None:
        return handler

    def _handler(expression):
        visitable = expression.getVisitableNodes()
        receiver = _formatMethodReceiverSource(visitable[0])
        arguments = [generateExpressionSource(node) for node in visitable[1:]]
        return (
            "%s.%s(%s)" % (receiver, method_name, ", ".join(arguments)),
            _PREC_POSTFIX,
        )

    _method_operation_source_handlers[method_name] = _handler
    return _handler


def _makeDictCollectionOperationSourceHandler(part_name, mode):
    def _handler(expression):
        receiver = _formatMethodReceiverSource(expression.subnode_dict_arg)
        if str is bytes:
            prefix = "" if mode == "list" else mode
            return "%s.%s%s()" % (receiver, prefix, part_name), _PREC_POSTFIX

        view_call = "%s.%s()" % (receiver, part_name)
        if mode == "view":
            return view_call, _PREC_POSTFIX
        if mode == "iter":
            return (
                "%s(%s)" % (_getBuiltinCallableSource(expression, "iter"), view_call),
                _PREC_POSTFIX,
            )
        return (
            "%s(%s)" % (_getBuiltinCallableSource(expression, "list"), view_call),
            _PREC_POSTFIX,
        )

    return _handler


def _generateDictOperationUpdateSource(expression):
    receiver = _formatMethodReceiverSource(expression.subnode_dict_arg)
    arguments = []

    iterable = getattr(expression, "subnode_iterable", None)
    if iterable is not None:
        arguments.append(generateExpressionSource(iterable))

    pairs = getattr(expression, "subnode_pairs", None)
    if pairs:
        arguments.extend(_formatKeywordPairsArguments(pairs))

    return "%s.update(%s)" % (receiver, ", ".join(arguments)), _PREC_POSTFIX


def _generateDictOperationFromkeysSource(expression):
    dict_source = _getBuiltinCallableSource(expression, "dict")
    arguments = [generateExpressionSource(expression.subnode_iterable)]
    value = getattr(expression, "subnode_value", None)
    if value is not None:
        arguments.append(generateExpressionSource(value))

    return "%s.fromkeys(%s)" % (dict_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateListOperationSortSource(expression):
    receiver = _formatMethodReceiverSource(expression.subnode_list_arg)
    arguments = []

    key_node = getattr(expression, "subnode_key", None)
    if key_node is not None:
        arguments.append("key=%s" % generateExpressionSource(key_node))

    reverse_node = getattr(expression, "subnode_reverse", None)
    if reverse_node is not None:
        arguments.append("reverse=%s" % generateExpressionSource(reverse_node))

    return "%s.sort(%s)" % (receiver, ", ".join(arguments)), _PREC_POSTFIX


def _generateStrOperationFormatSource(expression):
    receiver = _formatMethodReceiverSource(expression.subnode_str_arg)
    arguments = [generateExpressionSource(arg) for arg in expression.subnode_args]
    if expression.subnode_pairs:
        arguments.extend(_formatKeywordPairsArguments(expression.subnode_pairs))

    return "%s.format(%s)" % (receiver, ", ".join(arguments)), _PREC_POSTFIX


def _generateVariableRefSource(expression):
    variable = expression.variable

    if variable.isParameterVariable() and not variable.getName().isidentifier():
        return _annotate_argument_name, _PREC_ATOM

    if variable.getName() == _annotate_argument_name:
        raise PythonSourceGenerationError(
            "Variable name '%s' conflicts with the annotate function argument"
            % _annotate_argument_name
        )

    return getAnnotateSourceVariableName(variable), _PREC_ATOM


def _generateClassMappingVariableRefOrFallbackSource(expression):
    mapping = _generateSubExpressionSource(expression.subnode_mapping, _PREC_POSTFIX)
    fallback = generateExpressionSource(expression.subnode_fallback)

    variable_name = repr(expression.getVariableName())

    return (
        "(%(mapping)s[%(name)s] if %(name)s in %(mapping)s else %(fallback)s)"
        % {
            "mapping": mapping,
            "name": variable_name,
            "fallback": fallback,
        },
        _PREC_ATOM,
    )


def _generateEllipsisSource(_expression):
    return "...", _PREC_ATOM


def _generateBuiltinRefSource(expression):
    builtin_name = expression.getBuiltinName()

    if _isBuiltinNameShadowed(expression, builtin_name):
        return _getBuiltinCallableSource(expression, builtin_name), _PREC_POSTFIX

    return builtin_name, _PREC_ATOM


# Anonymous builtin references, e.g. "NoneType" or "function" do not have
# names that are available at runtime, so they get an equivalent expression
# to produce the value instead.
_anonymous_ref_sources = {
    "NoneType": "type(None)",
    "ellipsis": "type(...)",
    "NotImplementedType": "type(NotImplemented)",
    "function": "type(lambda: None)",
    "generator": "type(_ for _ in ())",
    "builtin_function_or_method": "type(len)",
    "code": "type((lambda: None).__code__)",
    "module": "type(__import__('types'))",
    "version_info": "type(__import__('sys').version_info)",
    "GenericAlias": "type(list[int])",
    "UnionType": "type(int | str)",
    "Union": "type(int | str)",
}


def _generateBuiltinAnonymousRefSource(expression):
    source = _anonymous_ref_sources.get(expression.getBuiltinName())

    if source is None:
        raise PythonSourceGenerationError(
            "Unsupported anonymous builtin reference for source generation: %s"
            % expression.getBuiltinName()
        )

    return source, _PREC_POSTFIX


def _generateBuiltinPatchableTypeRefSource(expression):
    import_name = expression.getImportName()
    module = expression.getParentModule()
    alias = _findModuleScopeAliasForPath(module, "builtins", expression)

    if alias is not None:
        return "%s.%s" % (alias, import_name), _PREC_POSTFIX

    if _isBuiltinNameShadowed(expression, import_name):
        return _getBuiltinCallableSource(expression, import_name), _PREC_POSTFIX

    return import_name, _PREC_ATOM


def _generateImportModuleHardSource(expression):
    module_name = expression.getModuleName().asString()
    value_name = (
        expression.getValueName().asString()
        if hasattr(expression, "getValueName")
        else module_name
    )
    return _formatModuleAccessSource(
        expression, value_name, module_to_import=module_name
    )


def _generateImportModuleNameHardSource(expression):
    import_name = expression.getImportName()
    module_name = expression.getModuleName()
    target = module_name.asString() if hasattr(module_name, "asString") else module_name
    return _formatHardImportRefSource(expression, target, import_name)


def _generateImportNameSource(expression):
    import_name = expression.getImportName()

    if import_name.isidentifier() and not keyword.iskeyword(import_name):
        return (
            "%s.%s"
            % (_formatMethodReceiverSource(expression.subnode_module), import_name),
            _PREC_POSTFIX,
        )

    return (
        "%s(%s, %r)"
        % (
            _getBuiltinCallableSource(expression, "getattr"),
            generateExpressionSource(expression.subnode_module),
            import_name,
        ),
        _PREC_POSTFIX,
    )


def _isModuleAttributeRebound(expression, attr_name):
    if _isNameShadowedInLocalOrClosureScope(expression, attr_name):
        return True

    module = expression.getParentModule()
    variable = module.variables.get(attr_name)
    if variable is not None:
        trace_collection = module.getTraceCollection()
        for version, trace in trace_collection.variable_traces.get(
            variable, {}
        ).items():
            if version <= 0:
                continue
            if (
                trace.isAssignTrace()
                and not trace.getAssignNode().getSourceReference().isInternal()
            ):
                return True
            if trace.mustNotHaveValue():
                return True

    return False


def _generateModuleAttributeRefSource(expression):
    attr_name = expression.getVariable().getName()

    if _isModuleAttributeRebound(expression, attr_name):
        raise PythonSourceGenerationError(
            "Shadowed module attribute '%s' cannot be referenced in generated source"
            % attr_name
        )

    return attr_name, _PREC_ATOM


def _generateRuntimePathSource(expression):
    if _isModuleAttributeRebound(expression, "__file__"):
        raise PythonSourceGenerationError(
            "Shadowed '__file__' cannot be used to reconstruct runtime path"
        )

    relative_path = expression.getRelativePath()
    module_runtime_filename = expression.getParentModule().getRunTimeFilename()

    if relative_path == module_runtime_filename:
        return "__file__", _PREC_ATOM

    dirname_callable, _precedence = _formatHardImportRefSource(
        expression, "os.path", "dirname"
    )
    base_expr = "%s(__file__)" % dirname_callable
    parent_dir = os.path.dirname(module_runtime_filename)
    while parent_dir:
        base_expr = "%s(%s)" % (dirname_callable, base_expr)
        parent_dir = os.path.dirname(parent_dir)

    if not relative_path:
        return base_expr, _PREC_POSTFIX

    join_callable, _precedence = _formatHardImportRefSource(
        expression, "os.path", "join"
    )
    return "%s(%s, %r)" % (join_callable, base_expr, relative_path), _PREC_POSTFIX


def _generateSysVersionInfoRefSource(expression):
    return _formatHardImportRefSource(expression, "sys", "version_info")


def _generateSpecArgumentsSource(expression, spec):
    arguments = []
    use_keyword = False

    for arg_name in spec.getArgumentNames():
        arg_node = getattr(expression, "subnode_" + arg_name, None)
        if arg_node is None:
            use_keyword = True
            continue

        value_source = generateExpressionSource(arg_node)
        if use_keyword:
            arguments.append("%s=%s" % (arg_name, value_source))
        else:
            arguments.append(value_source)

    star_list_name = spec.getStarListArgumentName()
    if star_list_name:
        star_items = getattr(expression, "subnode_" + star_list_name, ())
        assert type(star_items) is tuple, star_items
        if star_items:
            assert not use_keyword
            for item in star_items:
                arguments.append(generateExpressionSource(item))

    for kw_only_name in spec.getKwOnlyParameterNames():
        kw_node = getattr(expression, "subnode_" + kw_only_name, None)
        if kw_node is not None:
            arguments.append(
                "%s=%s" % (kw_only_name, generateExpressionSource(kw_node))
            )

    star_dict_name = spec.getStarDictArgumentName()
    if star_dict_name:
        pairs = getattr(expression, "subnode_" + star_dict_name, ())
        assert type(pairs) is tuple, pairs
        if pairs:
            arguments.extend(_formatKeywordPairsArguments(pairs))

    return arguments


def _generateBuiltinSpecCallSource(expression):
    spec = expression.spec
    callable_source = _getBuiltinCallableSource(expression, spec.getName())
    arguments = _generateSpecArgumentsSource(expression, spec)
    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateHardImportSpecCallSource(expression):
    spec = expression.spec
    module_name, import_name = spec.getName().rsplit(".", 1)
    callable_source, _precedence = _formatHardImportRefSource(
        expression, module_name, import_name
    )
    arguments = _generateSpecArgumentsSource(expression, spec)
    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateOsPathNormpathCallSource(expression):
    callable_source, _precedence = _formatHardImportRefSource(
        expression, "os.path", "normpath"
    )
    arguments = _generateSpecArgumentsSource(expression, expression.spec)
    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateImportlibMetadataBackportDistributionCallSource(expression):
    callable_source, _precedence = _formatHardImportRefSource(
        expression, "importlib_metadata", "distribution"
    )
    arguments = _generateSpecArgumentsSource(expression, expression.spec)
    return "%s(%s)" % (callable_source, ", ".join(arguments)), _PREC_POSTFIX


def _generateMetadataDistFailedCallSource(expression):
    callable_source, _precedence = _formatHardImportRefSource(
        expression, expression.importlib_metadata_name, "distribution"
    )
    return (
        "%s(%s)"
        % (
            callable_source,
            generateExpressionSource(expression.subnode_distribution_name),
        ),
        _PREC_POSTFIX,
    )


def _generateImportlibResourcesFilesCallFixedSource(expression):
    callable_source, _precedence = _formatHardImportRefSource(
        expression, expression.importlib_resources_name, "files"
    )
    return (
        "%s(%r)" % (callable_source, expression.package_name.asString()),
        _PREC_POSTFIX,
    )


def _generateImportlibImportModuleCallSource(expression):
    callable_source, _precedence = _formatHardImportRefSource(
        expression, "importlib", "import_module"
    )
    return _formatOptionalArgumentsCall(
        callable_source,
        (
            ("name", expression.subnode_name),
            ("package", expression.subnode_package),
        ),
    )


def _generateImportlibMetadataDistributionValueRefSource(expression):
    addDistributionMetadataValue(
        distribution_name=expression.original_name,
        distribution=expression.distribution,
        reason="static analysis",
    )

    target = "importlib.metadata"
    if (
        _findModuleAccessAliasOnly(expression, "importlib.metadata") is None
        and _findModuleAccessAliasOnly(expression, "importlib_metadata") is not None
    ):
        target = "importlib_metadata"

    callable_source, _precedence = _formatHardImportRefSource(
        expression, target, "distribution"
    )
    return "%s(%r)" % (callable_source, expression.original_name), _PREC_POSTFIX


def _generatePkgResourcesDistributionValueRefSource(expression):
    callable_source, _precedence = _formatHardImportRefSource(
        expression, "pkg_resources", "Distribution"
    )
    attr_names = list(expression.preserved_attributes)
    if (
        "location" not in attr_names
        and getattr(expression.distribution, "location", None) is not None
    ):
        attr_names.append("location")

    kw_args = [
        "%s=%s"
        % (
            attr_name,
            _formatConstantElement(
                getattr(expression.distribution, attr_name), expression
            ),
        )
        for attr_name in attr_names
    ]
    return "%s(%s)" % (callable_source, ", ".join(kw_args)), _PREC_POSTFIX


def _generatePkgResourcesEntryPointValueRefSource(expression):
    callable_source, _precedence = _formatHardImportRefSource(
        expression, "pkg_resources", "EntryPoint"
    )
    kw_args = [
        "%s=%s"
        % (
            attr_name,
            _formatConstantElement(
                getattr(expression.entry_point, attr_name), expression
            ),
        )
        for attr_name in expression.preserved_attributes
    ]
    return "%s(%s)" % (callable_source, ", ".join(kw_args)), _PREC_POSTFIX


def _generateImportlibMetadataEntryPointValueRefSource(expression):
    callable_source, _precedence = _formatHardImportRefSource(
        expression, expression.importlib_metadata_name, "EntryPoint"
    )
    kw_args = [
        "%s=%s"
        % (
            attr_name,
            _formatConstantElement(
                getattr(expression.entry_point, attr_name), expression
            ),
        )
        for attr_name in expression.preserved_attributes
    ]
    return "%s(%s)" % (callable_source, ", ".join(kw_args)), _PREC_POSTFIX


def _generateMetadataSelectableGroupsSource(expression):
    module_name = (
        "importlib_metadata"
        if expression.isExpressionImportlibMetadataBackportSelectableGroupsValueRef()
        else "importlib.metadata"
    )
    callable_source, _precedence = _formatHardImportRefSource(
        expression, module_name, "SelectableGroups"
    )
    return (
        "%s(%s)" % (callable_source, _generateDictLiteralSource(expression)),
        _PREC_POSTFIX,
    )


def _generateImportlibMetadataEntryPointsValueRefSource(expression):
    module_name = (
        "importlib_metadata"
        if expression.isExpressionImportlibMetadataBackportEntryPointsValueRef()
        else "importlib.metadata"
    )
    callable_source, _precedence = _formatHardImportRefSource(
        expression, module_name, "EntryPoints"
    )
    tuple_source, _tuple_prec = _generateTupleSource(expression)
    return "%s(%s)" % (callable_source, tuple_source), _PREC_POSTFIX


def _generateSideEffectsSource(expression):
    parts = [
        generateExpressionSource(side_effect)
        for side_effect in expression.subnode_side_effects
    ]
    parts.append(generateExpressionSource(expression.subnode_expression))
    return "(%s)[-1]" % ", ".join(parts), _PREC_POSTFIX


def _generateRaiseExpressionSource(expression):
    return (
        "(lambda _e: _e if _e.__class__.__name__ == '_Stringifier' else (_ for _ in ()).throw(_e))(%s)"
        % generateExpressionSource(expression.subnode_exception_type),
        _PREC_POSTFIX,
    )


_expression_source_dispatch = {
    "EXPRESSION_CONSTANT_TYPE_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_DICT_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_LIST_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_SET_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_FROZENDICT_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_FROZENSET_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_TUPLE_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CONSTANT_TYPE_TYPE_REF": _generateConstantTypeRefSource,
    "EXPRESSION_CLASS_MAPPING_VARIABLE_REF_OR_FALLBACK": _generateClassMappingVariableRefOrFallbackSource,
    "EXPRESSION_TEMP_VARIABLE_REF": _generateVariableRefSource,
    "EXPRESSION_VARIABLE_REF": _generateVariableRefSource,
    "EXPRESSION_VARIABLE_OR_BUILTIN_REF": _generateVariableRefSource,
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
    "EXPRESSION_CONSTANT_SYS_VERSION_INFO_REF": _generateSysVersionInfoRefSource,
    "EXPRESSION_ATTRIBUTE_CHECK": _generateAttributeCheckSource,
    "EXPRESSION_ATTRIBUTE_LOOKUP": _generateAttributeLookupSource,
    "EXPRESSION_ATTRIBUTE_LOOKUP_SPECIAL": _generateAttributeLookupSource,
    "EXPRESSION_SUBSCRIPT_LOOKUP": _generateSubscriptLookupSource,
    "EXPRESSION_SUBSCRIPT_LOOKUP_FOR_UNPACK": _generateSubscriptForUnpackSource,
    "EXPRESSION_SLICE_LOOKUP": _generateSliceLookupSource,
    "EXPRESSION_IMPORTLIB_RELOAD_REF": _generateImportlibReloadRefSource,
    "EXPRESSION_IMPORTLIB_RELOAD_CALL": _generateImportlibReloadCallSource,
    "EXPRESSION_IMPORTLIB_IMPORT_MODULE_REF": _generateImportModuleNameHardSource,
    "EXPRESSION_IMPORTLIB_IMPORT_MODULE_CALL": _generateImportlibImportModuleCallSource,
    "EXPRESSION_SYS_MODULES_REF": _generateSysModulesRefSource,
    "EXPRESSION_SYS_MODULES_LOOKUP": _generateSubscriptLookupSource,
    "EXPRESSION_SYS_MODULES_GET2": _generateSysModulesCallSource,
    "EXPRESSION_SYS_MODULES_GET3": _generateSysModulesCallSource,
    "EXPRESSION_SYS_MODULES_POP2": _generateSysModulesCallSource,
    "EXPRESSION_SYS_MODULES_POP3": _generateSysModulesCallSource,
    "EXPRESSION_OPERATION_BINARY_ADD": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_SUB": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_MULT": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_MAT_MULT": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_TRUE_DIV": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_FLOOR_DIV": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_OLD_DIV": _generateBinaryOpSource,
    "EXPRESSION_OPERATION_BINARY_DIVMOD": _generateDivmodSource,
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
    "EXPRESSION_STRING_CONCATENATION": _generateStringConcatenationSource,
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
    "EXPRESSION_BUILTIN_ALL": _makeSingleArgBuiltinSourceHandler("all"),
    "EXPRESSION_BUILTIN_ANY": _makeSingleArgBuiltinSourceHandler("any"),
    "EXPRESSION_BUILTIN_ASCII": _generateBuiltinAsciiSource,
    "EXPRESSION_BUILTIN_BIN": _makeSingleArgBuiltinSourceHandler("bin"),
    "EXPRESSION_BUILTIN_BOOL": _makeSingleArgBuiltinSourceHandler("bool"),
    "EXPRESSION_BUILTIN_BYTEARRAY1": _makeSingleArgBuiltinSourceHandler("bytearray"),
    "EXPRESSION_BUILTIN_BYTEARRAY3": _generateBuiltinBytearray3Source,
    "EXPRESSION_BUILTIN_BYTES1": _makeSingleArgBuiltinSourceHandler("bytes"),
    "EXPRESSION_BUILTIN_BYTES3": _generateBuiltinBytes3Source,
    "EXPRESSION_BUILTIN_CHR": _makeSingleArgBuiltinSourceHandler("chr"),
    "EXPRESSION_BUILTIN_CLASSMETHOD": _makeSingleArgBuiltinSourceHandler("classmethod"),
    "EXPRESSION_BUILTIN_COMPILE_BEFORE3": _generateBuiltinCompileSource,
    "EXPRESSION_BUILTIN_COMPILE_SINCE3": _generateBuiltinCompileSource,
    "EXPRESSION_BUILTIN_COMPLEX1": _makeSingleArgBuiltinSourceHandler("complex"),
    "EXPRESSION_BUILTIN_COMPLEX2": _generateBuiltinComplex2Source,
    "EXPRESSION_BUILTIN_DELATTR": _generateBuiltinDelattrSource,
    "EXPRESSION_BUILTIN_DICT": _generateBuiltinDictSource,
    "EXPRESSION_BUILTIN_DIR1": _makeSingleArgBuiltinSourceHandler("dir"),
    "EXPRESSION_BUILTIN_ENUMERATE1": _generateBuiltinEnumerateSource,
    "EXPRESSION_BUILTIN_ENUMERATE2": _generateBuiltinEnumerateSource,
    "EXPRESSION_BUILTIN_EVAL": _generateBuiltinEvalExecSource,
    "EXPRESSION_BUILTIN_EXEC": _generateBuiltinEvalExecSource,
    "EXPRESSION_BUILTIN_EXECFILE": _generateBuiltinEvalExecSource,
    "EXPRESSION_BUILTIN_FLOAT": _makeSingleArgBuiltinSourceHandler("float"),
    "EXPRESSION_BUILTIN_FORMAT": _generateBuiltinFormatSource,
    "EXPRESSION_BUILTIN_FROZENDICT": _generateBuiltinFrozendictSource,
    "EXPRESSION_BUILTIN_FROZENSET": _generateBuiltinFrozensetSource,
    "EXPRESSION_BUILTIN_GETATTR": _generateBuiltinGetattrSource,
    "EXPRESSION_BUILTIN_GLOBALS": _generateBuiltinGlobalsSource,
    "EXPRESSION_BUILTIN_HASATTR": _generateBuiltinHasattrSource,
    "EXPRESSION_BUILTIN_HASH": _makeSingleArgBuiltinSourceHandler("hash"),
    "EXPRESSION_BUILTIN_HEX": _makeSingleArgBuiltinSourceHandler("hex"),
    "EXPRESSION_BUILTIN_ID": _makeSingleArgBuiltinSourceHandler("id"),
    "EXPRESSION_BUILTIN_IMPORT": _generateBuiltinImportSource,
    "EXPRESSION_BUILTIN_INPUT": _generateBuiltinInputSource,
    "EXPRESSION_BUILTIN_INT1": _makeSingleArgBuiltinSourceHandler("int"),
    "EXPRESSION_BUILTIN_INT2": _generateBuiltinInt2Source,
    "EXPRESSION_BUILTIN_ISINSTANCE": _generateBuiltinIsinstanceSource,
    "EXPRESSION_BUILTIN_ISSUBCLASS": _generateBuiltinIssubclassSource,
    "EXPRESSION_BUILTIN_ITER1": _makeSingleArgBuiltinSourceHandler("iter"),
    "EXPRESSION_BUILTIN_ITER2": _generateBuiltinIter2Source,
    "EXPRESSION_BUILTIN_ITER_FOR_UNPACK": _makeSingleArgBuiltinSourceHandler("iter"),
    "EXPRESSION_BUILTIN_LEN": _makeSingleArgBuiltinSourceHandler("len"),
    "EXPRESSION_BUILTIN_LIST": _makeSingleArgBuiltinSourceHandler("list"),
    "EXPRESSION_BUILTIN_LOCALS_COPY": _generateBuiltinLocalsSource,
    "EXPRESSION_BUILTIN_LOCALS_REF": _generateBuiltinLocalsSource,
    "EXPRESSION_BUILTIN_LOCALS_UPDATED": _generateBuiltinLocalsSource,
    "EXPRESSION_BUILTIN_LONG1": _makeSingleArgBuiltinSourceHandler(
        "long" if str is bytes else "int"
    ),
    "EXPRESSION_BUILTIN_LONG2": _generateBuiltinInt2Source,
    "EXPRESSION_BUILTIN_MAKE_EXCEPTION": _generateBuiltinMakeExceptionSource,
    "EXPRESSION_BUILTIN_MAKE_EXCEPTION_ATTRIBUTE_ERROR": _generateBuiltinMakeExceptionSource,
    "EXPRESSION_BUILTIN_MAKE_EXCEPTION_IMPORT_ERROR": _generateBuiltinMakeExceptionSource,
    "EXPRESSION_BUILTIN_MAKE_EXCEPTION_MODULE_NOT_FOUND_ERROR": _generateBuiltinMakeExceptionSource,
    "EXPRESSION_BUILTIN_MAKE_EXCEPTION_NAME_ERROR": _generateBuiltinMakeExceptionSource,
    "EXPRESSION_BUILTIN_NEXT1": _generateBuiltinNext1Source,
    "EXPRESSION_BUILTIN_NEXT2": _generateBuiltinNext2Source,
    "EXPRESSION_BUILTIN_OCT": _makeSingleArgBuiltinSourceHandler("oct"),
    "EXPRESSION_BUILTIN_ORD": _makeSingleArgBuiltinSourceHandler("ord"),
    "EXPRESSION_BUILTIN_RANGE1": _generateBuiltinRangeSource,
    "EXPRESSION_BUILTIN_RANGE2": _generateBuiltinRangeSource,
    "EXPRESSION_BUILTIN_RANGE3": _generateBuiltinRangeSource,
    "EXPRESSION_BUILTIN_SENTINEL_CALL": _generateBuiltinSentinelSource,
    "EXPRESSION_BUILTIN_SET": _makeSingleArgBuiltinSourceHandler("set"),
    "EXPRESSION_BUILTIN_SETATTR": _generateBuiltinSetattrSource,
    "EXPRESSION_BUILTIN_SLICE1": _generateSliceSource,
    "EXPRESSION_BUILTIN_SLICE2": _generateSliceSource,
    "EXPRESSION_BUILTIN_SLICE3": _generateSliceSource,
    "EXPRESSION_BUILTIN_STATICMETHOD": _makeSingleArgBuiltinSourceHandler(
        "staticmethod"
    ),
    "EXPRESSION_BUILTIN_STR_P2": _generateBuiltinStrSource,
    "EXPRESSION_BUILTIN_STR_P3": _generateBuiltinStrSource,
    "EXPRESSION_BUILTIN_SUM1": _generateBuiltinSumSource,
    "EXPRESSION_BUILTIN_SUM2": _generateBuiltinSumSource,
    "EXPRESSION_BUILTIN_SUPER0": _generateBuiltinSuper0Source,
    "EXPRESSION_BUILTIN_SUPER1": _generateBuiltinSuper1Source,
    "EXPRESSION_BUILTIN_SUPER2": _generateBuiltinSuper2Source,
    "EXPRESSION_BUILTIN_TUPLE": _generateBuiltinTupleSource,
    "EXPRESSION_BUILTIN_TYPE1": _generateBuiltinType1Source,
    "EXPRESSION_BUILTIN_TYPE3": _generateBuiltinType3Source,
    "EXPRESSION_BUILTIN_UNICODE_P2": _generateBuiltinUnicodeP2Source,
    "EXPRESSION_BUILTIN_VARS": _makeSingleArgBuiltinSourceHandler(
        "vars", child_attr="subnode_source"
    ),
    "EXPRESSION_BUILTIN_XRANGE1": _generateBuiltinRangeSource,
    "EXPRESSION_BUILTIN_XRANGE2": _generateBuiltinRangeSource,
    "EXPRESSION_BUILTIN_XRANGE3": _generateBuiltinRangeSource,
    "EXPRESSION_BUILTIN_ZIP": _generateBuiltinZipSource,
    "EXPRESSION_BUILTIN_ZIP310": _generateBuiltinZipSource,
    "EXPRESSION_BUILTINS_MEMORYVIEW_CALL": _generateBuiltinSpecCallSource,
    "EXPRESSION_BUILTINS_OPEN_BEFORE3_CALL": _generateBuiltinSpecCallSource,
    "EXPRESSION_BUILTINS_OPEN_SINCE3_CALL": _generateBuiltinSpecCallSource,
    "EXPRESSION_BUILTINS_PRINT_BEFORE3_CALL": _generateBuiltinSpecCallSource,
    "EXPRESSION_BUILTINS_PRINT_SINCE3_CALL": _generateBuiltinSpecCallSource,
    "EXPRESSION_BUILTINS_PRINT_SINCE3_CALL1": _generateBuiltinSpecCallSource,
    "EXPRESSION_BUILTINS_REVERSED_CALL": _generateBuiltinSpecCallSource,
    "EXPRESSION_BUILTINS_SORTED_BEFORE3_CALL": _generateBuiltinSpecCallSource,
    "EXPRESSION_BUILTINS_SORTED_SINCE3_CALL": _generateBuiltinSpecCallSource,
    "EXPRESSION_BUILTINS_SORTED_SINCE3_CALL1": _generateBuiltinSpecCallSource,
    "EXPRESSION_TYPE_CHECK": _generateTypeCheckSource,
    "EXPRESSION_SUBTYPE_CHECK": _generateSubtypeCheckSource,
    "EXPRESSION_SPECIAL_UNPACK": _generateBuiltinNext1Source,
    "EXPRESSION_DICT_OPERATION_FROMKEYS_REF": _generateDictOperationFromkeysRefSource,
    "EXPRESSION_DICT_OPERATION_ITEM": _generateDictOperationItemSource,
    "EXPRESSION_DICT_OPERATION_GET2": _makeMethodOperationSourceHandler("get"),
    "EXPRESSION_DICT_OPERATION_GET3": _makeMethodOperationSourceHandler("get"),
    "EXPRESSION_DICT_OPERATION_HASKEY": _generateDictOperationHaskeySource,
    "EXPRESSION_DICT_OPERATION_IN": _generateDictOperationInSource,
    "EXPRESSION_DICT_OPERATION_NOT_IN": _generateDictOperationInSource,
    "EXPRESSION_DICT_OPERATION_COPY": _makeMethodOperationSourceHandler("copy"),
    "EXPRESSION_DICT_OPERATION_CLEAR": _makeMethodOperationSourceHandler("clear"),
    "EXPRESSION_DICT_OPERATION_ITEMS": _makeDictCollectionOperationSourceHandler(
        "items", "list"
    ),
    "EXPRESSION_DICT_OPERATION_ITERITEMS": _makeDictCollectionOperationSourceHandler(
        "items", "iter"
    ),
    "EXPRESSION_DICT_OPERATION_VIEWITEMS": _makeDictCollectionOperationSourceHandler(
        "items", "view"
    ),
    "EXPRESSION_DICT_OPERATION_KEYS": _makeDictCollectionOperationSourceHandler(
        "keys", "list"
    ),
    "EXPRESSION_DICT_OPERATION_ITERKEYS": _makeDictCollectionOperationSourceHandler(
        "keys", "iter"
    ),
    "EXPRESSION_DICT_OPERATION_VIEWKEYS": _makeDictCollectionOperationSourceHandler(
        "keys", "view"
    ),
    "EXPRESSION_DICT_OPERATION_VALUES": _makeDictCollectionOperationSourceHandler(
        "values", "list"
    ),
    "EXPRESSION_DICT_OPERATION_ITERVALUES": _makeDictCollectionOperationSourceHandler(
        "values", "iter"
    ),
    "EXPRESSION_DICT_OPERATION_VIEWVALUES": _makeDictCollectionOperationSourceHandler(
        "values", "view"
    ),
    "EXPRESSION_DICT_OPERATION_SETDEFAULT2": _makeMethodOperationSourceHandler(
        "setdefault"
    ),
    "EXPRESSION_DICT_OPERATION_SETDEFAULT3": _makeMethodOperationSourceHandler(
        "setdefault"
    ),
    "EXPRESSION_DICT_OPERATION_POP2": _makeMethodOperationSourceHandler("pop"),
    "EXPRESSION_DICT_OPERATION_POP3": _makeMethodOperationSourceHandler("pop"),
    "EXPRESSION_DICT_OPERATION_POPITEM": _makeMethodOperationSourceHandler("popitem"),
    "EXPRESSION_DICT_OPERATION_UPDATE2": _generateDictOperationUpdateSource,
    "EXPRESSION_DICT_OPERATION_UPDATE3": _generateDictOperationUpdateSource,
    "EXPRESSION_DICT_OPERATION_UPDATE_PAIRS": _generateDictOperationUpdateSource,
    "EXPRESSION_DICT_OPERATION_FROMKEYS2": _generateDictOperationFromkeysSource,
    "EXPRESSION_DICT_OPERATION_FROMKEYS3": _generateDictOperationFromkeysSource,
    "EXPRESSION_LIST_OPERATION_APPEND": _makeMethodOperationSourceHandler("append"),
    "EXPRESSION_LIST_OPERATION_EXTEND": _makeMethodOperationSourceHandler("extend"),
    "EXPRESSION_LIST_OPERATION_EXTEND_FOR_UNPACK": _makeMethodOperationSourceHandler(
        "extend"
    ),
    "EXPRESSION_LIST_OPERATION_CLEAR": _makeMethodOperationSourceHandler("clear"),
    "EXPRESSION_LIST_OPERATION_COPY": _makeMethodOperationSourceHandler("copy"),
    "EXPRESSION_LIST_OPERATION_COUNT": _makeMethodOperationSourceHandler("count"),
    "EXPRESSION_LIST_OPERATION_INSERT": _makeMethodOperationSourceHandler("insert"),
    "EXPRESSION_LIST_OPERATION_INDEX2": _makeMethodOperationSourceHandler("index"),
    "EXPRESSION_LIST_OPERATION_INDEX3": _makeMethodOperationSourceHandler("index"),
    "EXPRESSION_LIST_OPERATION_INDEX4": _makeMethodOperationSourceHandler("index"),
    "EXPRESSION_LIST_OPERATION_POP1": _makeMethodOperationSourceHandler("pop"),
    "EXPRESSION_LIST_OPERATION_POP2": _makeMethodOperationSourceHandler("pop"),
    "EXPRESSION_LIST_OPERATION_REMOVE": _makeMethodOperationSourceHandler("remove"),
    "EXPRESSION_LIST_OPERATION_REVERSE": _makeMethodOperationSourceHandler("reverse"),
    "EXPRESSION_LIST_OPERATION_SORT1": _generateListOperationSortSource,
    "EXPRESSION_LIST_OPERATION_SORT2": _generateListOperationSortSource,
    "EXPRESSION_LIST_OPERATION_SORT3": _generateListOperationSortSource,
    "EXPRESSION_SET_OPERATION_UPDATE": _makeMethodOperationSourceHandler("update"),
    "EXPRESSION_STR_OPERATION_CAPITALIZE": _makeMethodOperationSourceHandler(
        "capitalize"
    ),
    "EXPRESSION_STR_OPERATION_CASEFOLD": _makeMethodOperationSourceHandler("casefold"),
    "EXPRESSION_STR_OPERATION_CENTER2": _makeMethodOperationSourceHandler("center"),
    "EXPRESSION_STR_OPERATION_CENTER3": _makeMethodOperationSourceHandler("center"),
    "EXPRESSION_STR_OPERATION_COUNT2": _makeMethodOperationSourceHandler("count"),
    "EXPRESSION_STR_OPERATION_COUNT3": _makeMethodOperationSourceHandler("count"),
    "EXPRESSION_STR_OPERATION_COUNT4": _makeMethodOperationSourceHandler("count"),
    "EXPRESSION_STR_OPERATION_DECODE1": _makeMethodOperationSourceHandler("decode"),
    "EXPRESSION_STR_OPERATION_DECODE2": _makeMethodOperationSourceHandler("decode"),
    "EXPRESSION_STR_OPERATION_DECODE3": _makeMethodOperationSourceHandler("decode"),
    "EXPRESSION_STR_OPERATION_ENCODE1": _makeMethodOperationSourceHandler("encode"),
    "EXPRESSION_STR_OPERATION_ENCODE2": _makeMethodOperationSourceHandler("encode"),
    "EXPRESSION_STR_OPERATION_ENCODE3": _makeMethodOperationSourceHandler("encode"),
    "EXPRESSION_STR_OPERATION_ENDSWITH2": _makeMethodOperationSourceHandler("endswith"),
    "EXPRESSION_STR_OPERATION_ENDSWITH3": _makeMethodOperationSourceHandler("endswith"),
    "EXPRESSION_STR_OPERATION_ENDSWITH4": _makeMethodOperationSourceHandler("endswith"),
    "EXPRESSION_STR_OPERATION_EXPANDTABS1": _makeMethodOperationSourceHandler(
        "expandtabs"
    ),
    "EXPRESSION_STR_OPERATION_EXPANDTABS2": _makeMethodOperationSourceHandler(
        "expandtabs"
    ),
    "EXPRESSION_STR_OPERATION_FIND2": _makeMethodOperationSourceHandler("find"),
    "EXPRESSION_STR_OPERATION_FIND3": _makeMethodOperationSourceHandler("find"),
    "EXPRESSION_STR_OPERATION_FIND4": _makeMethodOperationSourceHandler("find"),
    "EXPRESSION_STR_OPERATION_FORMAT": _generateStrOperationFormatSource,
    "EXPRESSION_STR_OPERATION_INDEX2": _makeMethodOperationSourceHandler("index"),
    "EXPRESSION_STR_OPERATION_INDEX3": _makeMethodOperationSourceHandler("index"),
    "EXPRESSION_STR_OPERATION_INDEX4": _makeMethodOperationSourceHandler("index"),
    "EXPRESSION_STR_OPERATION_ISALNUM": _makeMethodOperationSourceHandler("isalnum"),
    "EXPRESSION_STR_OPERATION_ISALPHA": _makeMethodOperationSourceHandler("isalpha"),
    "EXPRESSION_STR_OPERATION_ISASCII": _makeMethodOperationSourceHandler("isascii"),
    "EXPRESSION_STR_OPERATION_ISDECIMAL": _makeMethodOperationSourceHandler(
        "isdecimal"
    ),
    "EXPRESSION_STR_OPERATION_ISDIGIT": _makeMethodOperationSourceHandler("isdigit"),
    "EXPRESSION_STR_OPERATION_ISIDENTIFIER": _makeMethodOperationSourceHandler(
        "isidentifier"
    ),
    "EXPRESSION_STR_OPERATION_ISLOWER": _makeMethodOperationSourceHandler("islower"),
    "EXPRESSION_STR_OPERATION_ISNUMERIC": _makeMethodOperationSourceHandler(
        "isnumeric"
    ),
    "EXPRESSION_STR_OPERATION_ISPRINTABLE": _makeMethodOperationSourceHandler(
        "isprintable"
    ),
    "EXPRESSION_STR_OPERATION_ISSPACE": _makeMethodOperationSourceHandler("isspace"),
    "EXPRESSION_STR_OPERATION_ISTITLE": _makeMethodOperationSourceHandler("istitle"),
    "EXPRESSION_STR_OPERATION_ISUPPER": _makeMethodOperationSourceHandler("isupper"),
    "EXPRESSION_STR_OPERATION_JOIN": _makeMethodOperationSourceHandler("join"),
    "EXPRESSION_STR_OPERATION_LJUST2": _makeMethodOperationSourceHandler("ljust"),
    "EXPRESSION_STR_OPERATION_LJUST3": _makeMethodOperationSourceHandler("ljust"),
    "EXPRESSION_STR_OPERATION_LOWER": _makeMethodOperationSourceHandler("lower"),
    "EXPRESSION_STR_OPERATION_LSTRIP1": _makeMethodOperationSourceHandler("lstrip"),
    "EXPRESSION_STR_OPERATION_LSTRIP2": _makeMethodOperationSourceHandler("lstrip"),
    "EXPRESSION_STR_OPERATION_PARTITION": _makeMethodOperationSourceHandler(
        "partition"
    ),
    "EXPRESSION_STR_OPERATION_REPLACE3": _makeMethodOperationSourceHandler("replace"),
    "EXPRESSION_STR_OPERATION_REPLACE4": _makeMethodOperationSourceHandler("replace"),
    "EXPRESSION_STR_OPERATION_RFIND2": _makeMethodOperationSourceHandler("rfind"),
    "EXPRESSION_STR_OPERATION_RFIND3": _makeMethodOperationSourceHandler("rfind"),
    "EXPRESSION_STR_OPERATION_RFIND4": _makeMethodOperationSourceHandler("rfind"),
    "EXPRESSION_STR_OPERATION_RINDEX2": _makeMethodOperationSourceHandler("rindex"),
    "EXPRESSION_STR_OPERATION_RINDEX3": _makeMethodOperationSourceHandler("rindex"),
    "EXPRESSION_STR_OPERATION_RINDEX4": _makeMethodOperationSourceHandler("rindex"),
    "EXPRESSION_STR_OPERATION_RJUST2": _makeMethodOperationSourceHandler("rjust"),
    "EXPRESSION_STR_OPERATION_RJUST3": _makeMethodOperationSourceHandler("rjust"),
    "EXPRESSION_STR_OPERATION_RPARTITION": _makeMethodOperationSourceHandler(
        "rpartition"
    ),
    "EXPRESSION_STR_OPERATION_RSPLIT1": _makeMethodOperationSourceHandler("rsplit"),
    "EXPRESSION_STR_OPERATION_RSPLIT2": _makeMethodOperationSourceHandler("rsplit"),
    "EXPRESSION_STR_OPERATION_RSPLIT3": _makeMethodOperationSourceHandler("rsplit"),
    "EXPRESSION_STR_OPERATION_RSTRIP1": _makeMethodOperationSourceHandler("rstrip"),
    "EXPRESSION_STR_OPERATION_RSTRIP2": _makeMethodOperationSourceHandler("rstrip"),
    "EXPRESSION_STR_OPERATION_SPLIT1": _makeMethodOperationSourceHandler("split"),
    "EXPRESSION_STR_OPERATION_SPLIT2": _makeMethodOperationSourceHandler("split"),
    "EXPRESSION_STR_OPERATION_SPLIT3": _makeMethodOperationSourceHandler("split"),
    "EXPRESSION_STR_OPERATION_SPLITLINES1": _makeMethodOperationSourceHandler(
        "splitlines"
    ),
    "EXPRESSION_STR_OPERATION_SPLITLINES2": _makeMethodOperationSourceHandler(
        "splitlines"
    ),
    "EXPRESSION_STR_OPERATION_STARTSWITH2": _makeMethodOperationSourceHandler(
        "startswith"
    ),
    "EXPRESSION_STR_OPERATION_STARTSWITH3": _makeMethodOperationSourceHandler(
        "startswith"
    ),
    "EXPRESSION_STR_OPERATION_STARTSWITH4": _makeMethodOperationSourceHandler(
        "startswith"
    ),
    "EXPRESSION_STR_OPERATION_STRIP1": _makeMethodOperationSourceHandler("strip"),
    "EXPRESSION_STR_OPERATION_STRIP2": _makeMethodOperationSourceHandler("strip"),
    "EXPRESSION_STR_OPERATION_SWAPCASE": _makeMethodOperationSourceHandler("swapcase"),
    "EXPRESSION_STR_OPERATION_TITLE": _makeMethodOperationSourceHandler("title"),
    "EXPRESSION_STR_OPERATION_TRANSLATE2": _makeMethodOperationSourceHandler(
        "translate"
    ),
    "EXPRESSION_STR_OPERATION_TRANSLATE3": _makeMethodOperationSourceHandler(
        "translate"
    ),
    "EXPRESSION_STR_OPERATION_UPPER": _makeMethodOperationSourceHandler("upper"),
    "EXPRESSION_STR_OPERATION_ZFILL": _makeMethodOperationSourceHandler("zfill"),
    "EXPRESSION_BYTES_OPERATION_CAPITALIZE": _makeMethodOperationSourceHandler(
        "capitalize"
    ),
    "EXPRESSION_BYTES_OPERATION_CENTER2": _makeMethodOperationSourceHandler("center"),
    "EXPRESSION_BYTES_OPERATION_CENTER3": _makeMethodOperationSourceHandler("center"),
    "EXPRESSION_BYTES_OPERATION_COUNT2": _makeMethodOperationSourceHandler("count"),
    "EXPRESSION_BYTES_OPERATION_COUNT3": _makeMethodOperationSourceHandler("count"),
    "EXPRESSION_BYTES_OPERATION_COUNT4": _makeMethodOperationSourceHandler("count"),
    "EXPRESSION_BYTES_OPERATION_DECODE1": _makeMethodOperationSourceHandler("decode"),
    "EXPRESSION_BYTES_OPERATION_DECODE2": _makeMethodOperationSourceHandler("decode"),
    "EXPRESSION_BYTES_OPERATION_DECODE3": _makeMethodOperationSourceHandler("decode"),
    "EXPRESSION_BYTES_OPERATION_ENDSWITH2": _makeMethodOperationSourceHandler(
        "endswith"
    ),
    "EXPRESSION_BYTES_OPERATION_ENDSWITH3": _makeMethodOperationSourceHandler(
        "endswith"
    ),
    "EXPRESSION_BYTES_OPERATION_ENDSWITH4": _makeMethodOperationSourceHandler(
        "endswith"
    ),
    "EXPRESSION_BYTES_OPERATION_EXPANDTABS1": _makeMethodOperationSourceHandler(
        "expandtabs"
    ),
    "EXPRESSION_BYTES_OPERATION_EXPANDTABS2": _makeMethodOperationSourceHandler(
        "expandtabs"
    ),
    "EXPRESSION_BYTES_OPERATION_FIND2": _makeMethodOperationSourceHandler("find"),
    "EXPRESSION_BYTES_OPERATION_FIND3": _makeMethodOperationSourceHandler("find"),
    "EXPRESSION_BYTES_OPERATION_FIND4": _makeMethodOperationSourceHandler("find"),
    "EXPRESSION_BYTES_OPERATION_INDEX2": _makeMethodOperationSourceHandler("index"),
    "EXPRESSION_BYTES_OPERATION_INDEX3": _makeMethodOperationSourceHandler("index"),
    "EXPRESSION_BYTES_OPERATION_INDEX4": _makeMethodOperationSourceHandler("index"),
    "EXPRESSION_BYTES_OPERATION_ISALNUM": _makeMethodOperationSourceHandler("isalnum"),
    "EXPRESSION_BYTES_OPERATION_ISALPHA": _makeMethodOperationSourceHandler("isalpha"),
    "EXPRESSION_BYTES_OPERATION_ISDIGIT": _makeMethodOperationSourceHandler("isdigit"),
    "EXPRESSION_BYTES_OPERATION_ISLOWER": _makeMethodOperationSourceHandler("islower"),
    "EXPRESSION_BYTES_OPERATION_ISSPACE": _makeMethodOperationSourceHandler("isspace"),
    "EXPRESSION_BYTES_OPERATION_ISTITLE": _makeMethodOperationSourceHandler("istitle"),
    "EXPRESSION_BYTES_OPERATION_ISUPPER": _makeMethodOperationSourceHandler("isupper"),
    "EXPRESSION_BYTES_OPERATION_JOIN": _makeMethodOperationSourceHandler("join"),
    "EXPRESSION_BYTES_OPERATION_LJUST2": _makeMethodOperationSourceHandler("ljust"),
    "EXPRESSION_BYTES_OPERATION_LJUST3": _makeMethodOperationSourceHandler("ljust"),
    "EXPRESSION_BYTES_OPERATION_LOWER": _makeMethodOperationSourceHandler("lower"),
    "EXPRESSION_BYTES_OPERATION_LSTRIP1": _makeMethodOperationSourceHandler("lstrip"),
    "EXPRESSION_BYTES_OPERATION_LSTRIP2": _makeMethodOperationSourceHandler("lstrip"),
    "EXPRESSION_BYTES_OPERATION_PARTITION": _makeMethodOperationSourceHandler(
        "partition"
    ),
    "EXPRESSION_BYTES_OPERATION_REPLACE3": _makeMethodOperationSourceHandler("replace"),
    "EXPRESSION_BYTES_OPERATION_REPLACE4": _makeMethodOperationSourceHandler("replace"),
    "EXPRESSION_BYTES_OPERATION_RFIND2": _makeMethodOperationSourceHandler("rfind"),
    "EXPRESSION_BYTES_OPERATION_RFIND3": _makeMethodOperationSourceHandler("rfind"),
    "EXPRESSION_BYTES_OPERATION_RFIND4": _makeMethodOperationSourceHandler("rfind"),
    "EXPRESSION_BYTES_OPERATION_RINDEX2": _makeMethodOperationSourceHandler("rindex"),
    "EXPRESSION_BYTES_OPERATION_RINDEX3": _makeMethodOperationSourceHandler("rindex"),
    "EXPRESSION_BYTES_OPERATION_RINDEX4": _makeMethodOperationSourceHandler("rindex"),
    "EXPRESSION_BYTES_OPERATION_RJUST2": _makeMethodOperationSourceHandler("rjust"),
    "EXPRESSION_BYTES_OPERATION_RJUST3": _makeMethodOperationSourceHandler("rjust"),
    "EXPRESSION_BYTES_OPERATION_RPARTITION": _makeMethodOperationSourceHandler(
        "rpartition"
    ),
    "EXPRESSION_BYTES_OPERATION_RSPLIT1": _makeMethodOperationSourceHandler("rsplit"),
    "EXPRESSION_BYTES_OPERATION_RSPLIT2": _makeMethodOperationSourceHandler("rsplit"),
    "EXPRESSION_BYTES_OPERATION_RSPLIT3": _makeMethodOperationSourceHandler("rsplit"),
    "EXPRESSION_BYTES_OPERATION_RSTRIP1": _makeMethodOperationSourceHandler("rstrip"),
    "EXPRESSION_BYTES_OPERATION_RSTRIP2": _makeMethodOperationSourceHandler("rstrip"),
    "EXPRESSION_BYTES_OPERATION_SPLIT1": _makeMethodOperationSourceHandler("split"),
    "EXPRESSION_BYTES_OPERATION_SPLIT2": _makeMethodOperationSourceHandler("split"),
    "EXPRESSION_BYTES_OPERATION_SPLIT3": _makeMethodOperationSourceHandler("split"),
    "EXPRESSION_BYTES_OPERATION_SPLITLINES1": _makeMethodOperationSourceHandler(
        "splitlines"
    ),
    "EXPRESSION_BYTES_OPERATION_SPLITLINES2": _makeMethodOperationSourceHandler(
        "splitlines"
    ),
    "EXPRESSION_BYTES_OPERATION_STARTSWITH2": _makeMethodOperationSourceHandler(
        "startswith"
    ),
    "EXPRESSION_BYTES_OPERATION_STARTSWITH3": _makeMethodOperationSourceHandler(
        "startswith"
    ),
    "EXPRESSION_BYTES_OPERATION_STARTSWITH4": _makeMethodOperationSourceHandler(
        "startswith"
    ),
    "EXPRESSION_BYTES_OPERATION_STRIP1": _makeMethodOperationSourceHandler("strip"),
    "EXPRESSION_BYTES_OPERATION_STRIP2": _makeMethodOperationSourceHandler("strip"),
    "EXPRESSION_BYTES_OPERATION_SWAPCASE": _makeMethodOperationSourceHandler(
        "swapcase"
    ),
    "EXPRESSION_BYTES_OPERATION_TITLE": _makeMethodOperationSourceHandler("title"),
    "EXPRESSION_BYTES_OPERATION_TRANSLATE2": _makeMethodOperationSourceHandler(
        "translate"
    ),
    "EXPRESSION_BYTES_OPERATION_TRANSLATE3": _makeMethodOperationSourceHandler(
        "translate"
    ),
    "EXPRESSION_BYTES_OPERATION_UPPER": _makeMethodOperationSourceHandler("upper"),
    "EXPRESSION_BYTES_OPERATION_ZFILL": _makeMethodOperationSourceHandler("zfill"),
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
    "EXPRESSION_BUILTIN_REF": _generateBuiltinRefSource,
    "EXPRESSION_BUILTIN_WITH_CONTEXT_REF": _generateBuiltinRefSource,
    "EXPRESSION_BUILTIN_ANONYMOUS_REF": _generateBuiltinAnonymousRefSource,
    "EXPRESSION_BUILTIN_PATCHABLE_TYPE_REF": _generateBuiltinPatchableTypeRefSource,
    "EXPRESSION_BUILTIN_EXCEPTION_REF": _generateBuiltinRefSource,
    "EXPRESSION_MODULE_ATTRIBUTE_DUNDER_COMPILED_REF": _generateModuleAttributeRefSource,
    "EXPRESSION_MODULE_ATTRIBUTE_FILE_REF": _generateModuleAttributeRefSource,
    "EXPRESSION_MODULE_ATTRIBUTE_NAME_REF": _generateModuleAttributeRefSource,
    "EXPRESSION_MODULE_ATTRIBUTE_PACKAGE_REF": _generateModuleAttributeRefSource,
    "EXPRESSION_MODULE_ATTRIBUTE_LOADER_REF": _generateModuleAttributeRefSource,
    "EXPRESSION_MODULE_ATTRIBUTE_SPEC_REF": _generateModuleAttributeRefSource,
    "EXPRESSION_RUNTIME_PATH": _generateRuntimePathSource,
    "EXPRESSION_IMPORT_NAME": _generateImportNameSource,
    "EXPRESSION_IMPORT_MODULE_HARD": _generateImportModuleHardSource,
    "EXPRESSION_IMPORT_MODULE_FIXED": _generateImportModuleHardSource,
    "EXPRESSION_IMPORT_MODULE_BUILTIN": _generateImportModuleHardSource,
    "EXPRESSION_IMPORT_MODULE_NAME_HARD_EXISTS": _generateImportModuleNameHardSource,
    "EXPRESSION_IMPORT_MODULE_NAME_HARD_MAYBE_EXISTS": _generateImportModuleNameHardSource,
    "EXPRESSION_CTYPES_CDLL_SINCE38_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_CTYPES_CDLL_BEFORE38_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_PKGUTIL_GET_DATA_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_PKGUTIL_ITER_MODULES_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_PKG_RESOURCES_REQUIRE_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_PKG_RESOURCES_GET_DISTRIBUTION_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_PKG_RESOURCES_ITER_ENTRY_POINTS_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_PKG_RESOURCES_RESOURCE_STRING_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_PKG_RESOURCES_RESOURCE_STREAM_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_PKG_RESOURCES_DISTRIBUTION_VALUE_REF": _generatePkgResourcesDistributionValueRefSource,
    "EXPRESSION_PKG_RESOURCES_ENTRY_POINT_VALUE_REF": _generatePkgResourcesEntryPointValueRefSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_OPEN_BINARY_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_OPEN_TEXT_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_READ_BINARY_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_BEFORE_313_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_READ_TEXT_SINCE_313_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_FILES_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_FILES_SINCE312_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_FILES_SINCE315_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_FILES_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_FILES_CALL_FIXED": _generateImportlibResourcesFilesCallFixedSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_FILES_CALL_FIXED": _generateImportlibResourcesFilesCallFixedSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_OPEN_BINARY_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_OPEN_TEXT_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_READ_BINARY_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_RESOURCES_BACKPORT_READ_TEXT_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_VERSION_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_VERSION_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_DISTRIBUTION_CALL": _generateImportlibMetadataBackportDistributionCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_FAILED_CALL": _generateMetadataDistFailedCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_DISTRIBUTION_FAILED_CALL": _generateMetadataDistFailedCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_BEFORE310_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_SINCE310_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINTS_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_IMPORTLIB_METADATA_DISTRIBUTION_VALUE_REF": _generateImportlibMetadataDistributionValueRefSource,
    "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINT_VALUE_REF": _generateImportlibMetadataEntryPointValueRefSource,
    "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINT_VALUE_REF": _generateImportlibMetadataEntryPointValueRefSource,
    "EXPRESSION_IMPORTLIB_METADATA_SELECTABLE_GROUPS_VALUE_REF": _generateMetadataSelectableGroupsSource,
    "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_SELECTABLE_GROUPS_VALUE_REF": _generateMetadataSelectableGroupsSource,
    "EXPRESSION_IMPORTLIB_METADATA_ENTRY_POINTS_VALUE_REF": _generateImportlibMetadataEntryPointsValueRefSource,
    "EXPRESSION_IMPORTLIB_METADATA_BACKPORT_ENTRY_POINTS_VALUE_REF": _generateImportlibMetadataEntryPointsValueRefSource,
    "EXPRESSION_OS_UNAME_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_FSPATH_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_PATH_EXISTS_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_PATH_ISFILE_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_PATH_ISDIR_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_PATH_BASENAME_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_PATH_DIRNAME_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_PATH_JOIN_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_PATH_ABSPATH_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_PATH_NORMPATH_CALL": _generateOsPathNormpathCallSource,
    "EXPRESSION_OS_PATH_ISABS_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_LISTDIR_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_STAT_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_OS_LSTAT_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_TENSORFLOW_FUNCTION_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_NETWORKX_UTILS_DECORATORS_ARGMAP_CALL": _generateHardImportSpecCallSource,
    "EXPRESSION_SIDE_EFFECTS": _generateSideEffectsSource,
    "EXPRESSION_RAISE_EXCEPTION": _generateRaiseExpressionSource,
}

_expression_source_dispatch.update(
    (attribute_class.kind, _generateAttributeLookupSource)
    for attribute_class in attribute_classes.values()
)

_expression_source_dispatch.update(
    (attribute_class.kind, _generateAttributeLookupSource)
    for attribute_class in attribute_typed_classes
)

_expression_source_dispatch.update(
    (hard_import_class.kind, _generateImportModuleNameHardSource)
    for hard_import_class in getHardImportNodeClasses()
)

_expression_source_dispatch.update(
    (builtin_ref_class.kind, _generateBuiltinRefSource)
    for builtin_ref_class in getBuiltinRefNodes().values()
)

_statement_source_dispatch = {
    "STATEMENT_ASSIGNMENT_SYS_MODULES_SUBSCRIPT": _generateSysModulesAssignmentSource,
    "STATEMENT_DEL_SYS_MODULES_SUBSCRIPT": _generateSysModulesDelSource,
    "STATEMENT_CONDITIONAL": _generateConditionalSource,
    "STATEMENT_RAISE_EXCEPTION": _generateRaiseExceptionSource,
    "STATEMENT_RETURN": _generateReturnSource,
    "STATEMENT_RETURN_CONSTANT": _generateReturnSource,
    "STATEMENTS_FRAME_FUNCTION": _generateStatementsFrameSource,
}

_checked_dispatch_kinds = False


def _checkDispatchKinds():
    """Verify all source-generation kinds exist in C code generation."""
    # pylint: disable=global-statement
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
        if kind == "STATEMENTS_FRAME_FUNCTION":
            continue

        if kind not in getStatementDispatchDict():
            raise NuitkaCodeDeficit(
                "Source generation statement kind %r is not in C dispatch" % kind
            )

    _checked_dispatch_kinds = True


def _generateExpressionSourceWithPrecedence(expression):
    _checkDispatchKinds()

    kind = expression.kind

    handler = _expression_source_dispatch.get(kind)
    if handler is None:
        raise PythonSourceGenerationError(
            "Unsupported expression kind for source generation: %s" % kind
        )

    return handler(expression)


def _generateSubExpressionSource(expression, min_precedence):
    source, precedence = _generateExpressionSourceWithPrecedence(expression)

    if precedence < min_precedence:
        return "(%s)" % source

    return source


def generateExpressionSource(expression):
    """Generate Python source for 'expression', raising 'PythonSourceGenerationError' if unsupported."""
    source, _precedence = _generateExpressionSourceWithPrecedence(expression)
    return source


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
