#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for CPython C-API and Nuitka helper calls."""

from .CodeHelpers import (
    generateExpressionCode,
    promoteBorrowedValue,
    withBorrowedValueScope,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCodes


class CArg(object):
    """Raw C expression, identifier, or literal argument passed verbatim."""

    __slots__ = ("c_code",)

    def __init__(self, c_code):
        assert c_code is not None
        self.c_code = str(c_code)


class ConstantArg(object):
    """Compile-time constant argument emitted via 'context.getConstantCode'."""

    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value


class TupleArg(object):
    """Tuple-of-expressions argument built as a Python tuple object."""

    __slots__ = ("name", "elements")

    def __init__(self, name, elements):
        self.name = name
        self.elements = elements


class OptionalArg(object):
    """Expression argument using a custom C or constant default when 'None'."""

    __slots__ = ("name", "expression", "default")

    def __init__(self, name, expression, default):
        self.name = name
        self.expression = expression
        self.default = default


def _resolveDefaultArgCode(default, context):
    default_type = type(default)

    if default_type is ConstantArg:
        return context.getConstantCode(default.value)
    if default_type is CArg:
        return default.c_code
    assert default_type is str, default
    return default


def makeArgDescFromExpression(expression):
    """Build 'arg_desc' pairs for 'generateCAPIObjectCode' from node children."""

    if hasattr(expression, "named_children"):
        result = []

        for child_desc in expression.named_children:
            if "|" in child_desc:
                child_name = child_desc.split("|")[0]
            else:
                child_name = child_desc

            result.append(
                (child_name + "_value", getattr(expression, "subnode_" + child_name))
            )

        return tuple(result)

    return tuple(
        (child_name + "_value", child_value)
        for child_name, child_value in expression.getVisitableNodesNamed()
    )


def _collectExpressions(arg_desc):
    expressions = []

    for item in arg_desc:
        item_type = type(item)

        if item_type in (CArg, ConstantArg):
            continue

        if item_type is TupleArg:
            expressions.extend(item.elements)
        elif item_type is OptionalArg:
            if item.expression is not None:
                expressions.append(item.expression)
        else:
            _arg_name, arg_expression = item

            if arg_expression is None:
                continue

            if type(arg_expression) is tuple:
                expressions.extend(arg_expression)
            else:
                expressions.append(arg_expression)

    return expressions


def _generateSingleArgExpressionCode(
    arg_name, arg_expression, expr_index, all_expressions, emit, context
):
    tmp_name = context.allocateTempName(arg_name)

    generateExpressionCode(
        to_name=tmp_name,
        expression=arg_expression,
        emit=emit,
        context=context,
    )

    expr_index += 1
    if expr_index < len(all_expressions):
        promoteBorrowedValue(
            value_name=tmp_name,
            later_expressions=all_expressions[expr_index:],
            emit=emit,
            context=context,
        )

    return tmp_name, expr_index


def _generateTupleArrayArgCode(
    arg_name,
    arg_expressions,
    expr_index,
    all_expressions,
    arg_names,
    release_names,
    emit,
    context,
):
    sub_names = []

    for sub_index, sub_expression in enumerate(arg_expressions):
        sub_name, expr_index = _generateSingleArgExpressionCode(
            arg_name=arg_name + "_element_%d" % sub_index,
            arg_expression=sub_expression,
            expr_index=expr_index,
            all_expressions=all_expressions,
            emit=emit,
            context=context,
        )
        sub_names.append(sub_name)

    if len(sub_names) == 1:
        arg_names.append("&%s" % sub_names[0])
        arg_names.append("1")
        release_names.extend(sub_names)
    elif sub_names:
        array_name = "tmp_%s_array_%d" % (
            arg_name,
            context.allocateTempNumber(arg_name),
        )

        emit(
            "PyObject *%s[] = {%s};"
            % (array_name, ", ".join(str(name) for name in sub_names))
        )
        arg_names.append(array_name)
        arg_names.append(str(len(sub_names)))
        release_names.extend(sub_names)
    else:
        arg_names.append("NULL")
        arg_names.append("0")

    return expr_index


def _generateNamedArgCode(
    arg_name,
    arg_expression,
    none_null,
    expr_index,
    all_expressions,
    arg_names,
    release_names,
    emit,
    context,
):
    if arg_expression is None:
        if none_null is True or (none_null and arg_name in none_null):
            arg_names.append("NULL")
        else:
            raise ValueError("None expression not allowed for %s" % arg_name)

        return expr_index

    if type(arg_expression) is tuple:
        return _generateTupleArrayArgCode(
            arg_name=arg_name,
            arg_expressions=arg_expression,
            expr_index=expr_index,
            all_expressions=all_expressions,
            arg_names=arg_names,
            release_names=release_names,
            emit=emit,
            context=context,
        )

    tmp_name, expr_index = _generateSingleArgExpressionCode(
        arg_name=arg_name,
        arg_expression=arg_expression,
        expr_index=expr_index,
        all_expressions=all_expressions,
        emit=emit,
        context=context,
    )

    arg_names.append(tmp_name)
    release_names.append(tmp_name)

    return expr_index


def _generateCAPIArgCodes(arg_desc, tstate, none_null, all_expressions, emit, context):
    arg_names = []
    release_names = []

    if tstate:
        arg_names.append("tstate")

    expr_index = 0

    for item in arg_desc:
        item_type = type(item)

        if item_type is CArg:
            arg_names.append(item.c_code)
        elif item_type is ConstantArg:
            arg_names.append(context.getConstantCode(item.value))
        elif item_type is TupleArg:
            from .TupleCodes import getTupleCreationCode

            tmp_name = context.allocateTempName(item.name)

            getTupleCreationCode(
                to_name=tmp_name,
                elements=item.elements,
                emit=emit,
                context=context,
            )

            expr_index += len(item.elements)

            arg_names.append(tmp_name)
            release_names.append(tmp_name)
        elif item_type is OptionalArg:
            if item.expression is None:
                arg_names.append(_resolveDefaultArgCode(item.default, context))
            else:
                tmp_name, expr_index = _generateSingleArgExpressionCode(
                    arg_name=item.name,
                    arg_expression=item.expression,
                    expr_index=expr_index,
                    all_expressions=all_expressions,
                    emit=emit,
                    context=context,
                )

                arg_names.append(tmp_name)
                release_names.append(tmp_name)
        else:
            arg_name, arg_expression = item

            expr_index = _generateNamedArgCode(
                arg_name=arg_name,
                arg_expression=arg_expression,
                none_null=none_null,
                expr_index=expr_index,
                all_expressions=all_expressions,
                arg_names=arg_names,
                release_names=release_names,
                emit=emit,
                context=context,
            )

    return arg_names, release_names


def _generateScopedCAPIArgCodes(arg_desc, tstate, none_null, emit, context):
    all_expressions = _collectExpressions(arg_desc)

    if len(all_expressions) > 1:
        with withBorrowedValueScope(context):
            return _generateCAPIArgCodes(
                arg_desc=arg_desc,
                tstate=tstate,
                none_null=none_null,
                all_expressions=all_expressions,
                emit=emit,
                context=context,
            )

    return _generateCAPIArgCodes(
        arg_desc=arg_desc,
        tstate=tstate,
        none_null=none_null,
        all_expressions=all_expressions,
        emit=emit,
        context=context,
    )


def _injectFetchedExceptionArg(capi, arg_names, context):
    assert arg_names and arg_names[0] == "tstate", (capi, arg_names)

    (
        exception_state_name,
        _exception_lineno,
    ) = context.getExceptionVariableDescriptions()

    return (
        arg_names[0],
        "&%s" % exception_state_name,
    ) + tuple(arg_names[1:])


def generateCAPIObjectCodeCommon(
    to_name,
    capi,
    tstate,
    arg_desc,
    may_raise,
    conversion_check,
    ref_count,
    source_ref,
    emit,
    context,
    none_null=False,
    fetched_exception=False,
):
    # pylint: disable=too-many-arguments
    """Generate C code for calling an object-returning C-API or helper function.

    Args:
        arg_desc: Sequence of '(arg_name, expression_or_tuple)' pairs, 'CArg',
            'ConstantArg', 'TupleArg', or 'OptionalArg' descriptors; a tuple of
            expressions expands into a 'PyObject *[]' array (or '&elem' for a
            single element) and length pair.
        ref_count: '1' for a new reference return, '0' for a borrowed return.
        none_null: If True, 'None' expressions pass 'NULL'; otherwise a
            container of 'arg_name' strings allowed to pass 'NULL' when 'None'.
        fetched_exception: If True and 'may_raise' is True, pass '&exception_state'
            after 'tstate' and forward 'fetched_exception=True' to error exit.
    """
    arg_names, release_names = _generateScopedCAPIArgCodes(
        arg_desc=arg_desc,
        tstate=tstate,
        none_null=none_null,
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(source_ref):
        getCAPIObjectCode(
            to_name=to_name,
            capi=capi,
            arg_names=arg_names,
            may_raise=may_raise,
            conversion_check=conversion_check,
            ref_count=ref_count,
            release_names=release_names,
            fetched_exception=fetched_exception,
            emit=emit,
            context=context,
        )


def generateCAPIObjectCode(
    to_name,
    capi,
    tstate,
    arg_desc,
    may_raise,
    conversion_check,
    source_ref,
    emit,
    context,
    none_null=False,
    fetched_exception=False,
):
    """Call 'generateCAPIObjectCodeCommon' for helpers returning a new reference."""
    generateCAPIObjectCodeCommon(
        to_name=to_name,
        capi=capi,
        tstate=tstate,
        arg_desc=arg_desc,
        may_raise=may_raise,
        conversion_check=conversion_check,
        ref_count=1,
        source_ref=source_ref,
        emit=emit,
        context=context,
        none_null=none_null,
        fetched_exception=fetched_exception,
    )


def generateCAPIObjectCode0(
    to_name,
    capi,
    tstate,
    arg_desc,
    may_raise,
    conversion_check,
    source_ref,
    emit,
    context,
    none_null=False,
    fetched_exception=False,
):
    """Call 'generateCAPIObjectCodeCommon' for helpers returning a borrowed reference."""
    generateCAPIObjectCodeCommon(
        to_name=to_name,
        capi=capi,
        tstate=tstate,
        arg_desc=arg_desc,
        may_raise=may_raise,
        conversion_check=conversion_check,
        ref_count=0,
        source_ref=source_ref,
        emit=emit,
        context=context,
        none_null=none_null,
        fetched_exception=fetched_exception,
    )


def getCAPIObjectCode(
    to_name,
    capi,
    arg_names,
    may_raise,
    conversion_check,
    ref_count,
    release_names,
    emit,
    context,
    fetched_exception=False,
):
    if fetched_exception and may_raise:
        arg_names = _injectFetchedExceptionArg(
            capi=capi, arg_names=arg_names, context=context
        )

    if to_name is not None:
        with withObjectCodeTemporaryAssignment(
            to_name, "capi_result", conversion_check, emit, context
        ) as value_name:
            emit(
                "%s = %s(%s);"
                % (
                    value_name,
                    capi,
                    ", ".join(str(arg_name) for arg_name in arg_names),
                )
            )

            getErrorExitCode(
                check_name=value_name,
                release_names=release_names,
                needs_check=may_raise,
                fetched_exception=fetched_exception,
                emit=emit,
                context=context,
            )

            if ref_count:
                context.addCleanupTempName(value_name)
    else:
        assert not may_raise, capi
        assert not ref_count

        emit("%s(%s);" % (capi, ", ".join(str(arg_name) for arg_name in arg_names)))

        getReleaseCodes(release_names, emit, context)


def generateCAPIBoolCode(
    to_name,
    capi,
    tstate,
    arg_desc,
    may_raise,
    source_ref,
    emit,
    context,
    res_type="tristate",
    inverted=False,
    none_null=False,
    fetched_exception=False,
):
    # pylint: disable=too-many-arguments
    """Generate C code for calling a boolean-returning C-API or helper function.

    Args:
        res_type: '"tristate"' for '-1' error / '0' false / '!= 0' true 'int'
            helpers, '"bool"' for infallible C 'bool' helpers, or '"int"' for
            infallible 'int' ('0' / '!= 0') helpers.
        inverted: If True, negate the resulting boolean condition.
    """
    arg_names, release_names = _generateScopedCAPIArgCodes(
        arg_desc=arg_desc,
        tstate=tstate,
        none_null=none_null,
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(source_ref):
        getCAPIBoolCode(
            to_name=to_name,
            capi=capi,
            arg_names=arg_names,
            may_raise=may_raise,
            release_names=release_names,
            emit=emit,
            context=context,
            res_type=res_type,
            inverted=inverted,
            fetched_exception=fetched_exception,
        )


def getCAPIBoolCode(
    to_name,
    capi,
    arg_names,
    may_raise,
    release_names,
    emit,
    context,
    res_type="tristate",
    inverted=False,
    fetched_exception=False,
):
    assert res_type in ("tristate", "bool", "int"), res_type

    if fetched_exception and may_raise:
        arg_names = _injectFetchedExceptionArg(
            capi=capi, arg_names=arg_names, context=context
        )

    if res_type == "bool":
        assert not may_raise, capi

        res_name = context.getBoolResName()
        emit(
            "%s = %s(%s);"
            % (
                res_name,
                capi,
                ", ".join(str(arg_name) for arg_name in arg_names),
            )
        )

        getReleaseCodes(release_names, emit, context)

        condition = "!%s" % res_name if inverted else res_name
    else:
        res_name = context.getIntResName()
        emit(
            "%s = %s(%s);"
            % (
                res_name,
                capi,
                ", ".join(str(arg_name) for arg_name in arg_names),
            )
        )

        if res_type == "tristate":
            getErrorExitBoolCode(
                condition="%s == -1" % res_name,
                release_names=release_names,
                needs_check=may_raise,
                fetched_exception=fetched_exception,
                emit=emit,
                context=context,
            )
        else:
            assert not may_raise, capi
            getReleaseCodes(release_names, emit, context)

        condition = "%s %s 0" % (res_name, "==" if inverted else "!=")

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name,
        condition=condition,
        emit=emit,
    )


def generateCAPIErrorCode(
    capi,
    tstate,
    arg_desc,
    may_raise,
    source_ref,
    emit,
    context,
    res_type="bool",
    none_null=False,
    fetched_exception=False,
):
    """Generate C code for calling an error-status-returning C-API or helper function.

    Args:
        res_type: '"bool"' for 'false'-on-error C 'bool' helpers,
            '"int_neg1"' for '-1'-on-error 'int' helpers, or
            '"int_nonzero"' for '!= 0'-on-error 'int' helpers.
    """
    arg_names, release_names = _generateScopedCAPIArgCodes(
        arg_desc=arg_desc,
        tstate=tstate,
        none_null=none_null,
        emit=emit,
        context=context,
    )

    with context.withCurrentSourceCodeReference(source_ref):
        getCAPIErrorCode(
            capi=capi,
            arg_names=arg_names,
            may_raise=may_raise,
            release_names=release_names,
            emit=emit,
            context=context,
            res_type=res_type,
            fetched_exception=fetched_exception,
        )


def getCAPIErrorCode(
    capi,
    arg_names,
    may_raise,
    release_names,
    emit,
    context,
    res_type="bool",
    fetched_exception=False,
):
    assert res_type in ("bool", "int_neg1", "int_nonzero"), res_type

    if fetched_exception and may_raise:
        arg_names = _injectFetchedExceptionArg(
            capi=capi, arg_names=arg_names, context=context
        )

    if res_type == "bool":
        res_name = context.getBoolResName()
        condition = "%s == false" % res_name
    elif res_type == "int_neg1":
        res_name = context.getIntResName()
        condition = "%s == -1" % res_name
    else:
        res_name = context.getIntResName()
        condition = "%s != 0" % res_name

    emit(
        "%s = %s(%s);"
        % (
            res_name,
            capi,
            ", ".join(str(arg_name) for arg_name in arg_names),
        )
    )

    getErrorExitBoolCode(
        condition=condition,
        release_names=release_names,
        needs_check=may_raise,
        fetched_exception=fetched_exception,
        emit=emit,
        context=context,
    )


def getReferenceExportCode(base_name, emit, context):
    if not context.needsCleanup(base_name):
        emit("Py_INCREF(%s);" % base_name)

        # The value now owns a reference and no longer needs protection
        # against writes to the variable it was read from.
        context.unregisterBorrowedValue(base_name)


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
