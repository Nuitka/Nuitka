#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Comparison related codes.

Rich comparisons, "in", and "not in", also "is", and "is not", and the
"isinstance" check as used in conditions, as well as exception matching.
"""

from nuitka.nodes.shapes.BuiltinTypeShapes import ShapeTypeBool

from . import OperatorCodes
from .CodeHelpers import generateExpressionCode, pickCodeHelper
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode, getReleaseCodes

_cmp_obj_result_helpers_set = set(
    (
        "RICH_COMPARE_xx_OBJECT_OBJECT",
        #        "RICH_COMPARE_xx_OBJECT_INT",
        #        "RICH_COMPARE_xx_OBJECT_LONG",
        #        "RICH_COMPARE_xx_OBJECT_STR",
        #        "RICH_COMPARE_xx_FLOAT_OBJECT",
        #        "RICH_COMPARE_xx_OBJECT_UNICODE",
        #        "RICH_COMPARE_xx_OBJECT_TUPLE",
        #        "RICH_COMPARE_xx_OBJECT_LIST",
        #        "RICH_COMPARE_xx_OBJECT_BYTES",
        #        "RICH_COMPARE_xx_INT_OBJECT",
        #        "RICH_COMPARE_xx_LONG_OBJECT",
        #        "RICH_COMPARE_xx_STR_OBJECT",
        #        "RICH_COMPARE_xx_OBJECT_FLOAT",
        #        "RICH_COMPARE_xx_UNICODE_OBJECT",
        #        "RICH_COMPARE_xx_TUPLE_OBJECT",
        #        "RICH_COMPARE_xx_LIST_OBJECT",
        #        "RICH_COMPARE_xx_BYTES_OBJECT",
        #        "RICH_COMPARE_xx_INT_INT",
        #        "RICH_COMPARE_xx_LONG_LONG",
        #        "RICH_COMPARE_xx_STR_STR",
        #        "RICH_COMPARE_xx_FLOAT_FLOAT",
        #        "RICH_COMPARE_xx_UNICODE_UNICODE",
        #        "RICH_COMPARE_xx_TUPLE_TUPLE",
        #        "RICH_COMPARE_xx_LIST_LIST",
        #        "RICH_COMPARE_xx_BYTES_BYTES",
    )
)

_cmp_bool_result_helpers_set = set(
    (
        "RICH_COMPARE_BOOL_xx_OBJECT_OBJECT",
        "RICH_COMPARE_BOOL_xx_OBJECT_INT",
        #        "RICH_COMPARE_BOOL_xx_OBJECT_LONG",
        #        "RICH_COMPARE_BOOL_xx_OBJECT_STR",
        #        "RICH_COMPARE_BOOL_xx_FLOAT_OBJECT",
        #        "RICH_COMPARE_BOOL_xx_OBJECT_UNICODE",
        #        "RICH_COMPARE_BOOL_xx_OBJECT_TUPLE",
        #        "RICH_COMPARE_BOOL_xx_OBJECT_LIST",
        #        "RICH_COMPARE_BOOL_xx_OBJECT_BYTES",
        "RICH_COMPARE_BOOL_xx_INT_OBJECT",
        #        "RICH_COMPARE_BOOL_xx_LONG_OBJECT",
        #        "RICH_COMPARE_BOOL_xx_STR_OBJECT",
        #        "RICH_COMPARE_BOOL_xx_OBJECT_FLOAT",
        #        "RICH_COMPARE_BOOL_xx_UNICODE_OBJECT",
        #        "RICH_COMPARE_BOOL_xx_TUPLE_OBJECT",
        #        "RICH_COMPARE_BOOL_xx_LIST_OBJECT",
        #        "RICH_COMPARE_BOOL_xx_BYTES_OBJECT",
        "RICH_COMPARE_BOOL_xx_INT_INT",
        #        "RICH_COMPARE_BOOL_xx_LONG_LONG",
        #        "RICH_COMPARE_BOOL_xx_STR_STR",
        #        "RICH_COMPARE_BOOL_xx_FLOAT_FLOAT",
        #        "RICH_COMPARE_BOOL_xx_UNICODE_UNICODE",
        #        "RICH_COMPARE_BOOL_xx_TUPLE_TUPLE",
        #        "RICH_COMPARE_BOOL_xx_LIST_LIST",
        #        "RICH_COMPARE_BOOL_xx_BYTES_BYTES",
    )
)


def generateComparisonExpressionCode(to_name, expression, emit, context):
    # Currently high complexity, due to manual C typing and doing all
    # in one place, pylint: disable=too-many-branches,too-many-statements

    left = expression.getLeft()
    right = expression.getRight()

    comparator = expression.getComparator()

    type_name = "PyObject *"
    if comparator in ("Is", "IsNot"):
        if (
            left.getTypeShape() is ShapeTypeBool
            and right.getTypeShape() is ShapeTypeBool
        ):
            type_name = "nuitka_bool"

    left_name = context.allocateTempName("compexpr_left", type_name=type_name)
    right_name = context.allocateTempName("compexpr_right", type_name=type_name)

    generateExpressionCode(
        to_name=left_name, expression=left, emit=emit, context=context
    )
    generateExpressionCode(
        to_name=right_name, expression=right, emit=emit, context=context
    )

    if comparator in OperatorCodes.containing_comparison_codes:
        needs_check = right.mayRaiseExceptionIn(BaseException, expression.getLeft())

        res_name = context.getIntResName()

        emit(
            "%s = PySequence_Contains( %s, %s );"
            % (res_name, right_name, left_name)  # sequence goes first in the API.
        )

        getErrorExitBoolCode(
            condition="%s == -1" % res_name,
            release_names=(left_name, right_name),
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name,
            condition="%s == %d" % (res_name, 1 if comparator == "In" else 0),
            emit=emit,
        )

        return
    elif comparator == "Is":
        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition="%s == %s" % (left_name, right_name), emit=emit
        )

        getReleaseCodes(
            release_names=(left_name, right_name), emit=emit, context=context
        )

        return
    elif comparator == "IsNot":
        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition="%s != %s" % (left_name, right_name), emit=emit
        )

        getReleaseCodes(
            release_names=(left_name, right_name), emit=emit, context=context
        )

        return
    elif comparator in OperatorCodes.rich_comparison_codes:
        needs_check = expression.mayRaiseExceptionComparison()

        if comparator == "Eq" and not context.mayRecurse():
            suffix = "_NORECURSE"
        else:
            suffix = ""

        c_type = to_name.getCType()

        if c_type.c_type == "PyObject *":
            helper = pickCodeHelper(
                prefix="RICH_COMPARE_xx",
                suffix=suffix,
                left_shape=left.getTypeShape(),
                right_shape=expression.getRight().getTypeShape(),
                helpers=_cmp_obj_result_helpers_set,
                # TODO: Too many for now, so disable it
                warn_missing=False,
            )
        else:
            helper = pickCodeHelper(
                prefix="RICH_COMPARE_BOOL_xx",
                suffix=suffix,
                left_shape=left.getTypeShape(),
                right_shape=expression.getRight().getTypeShape(),
                helpers=_cmp_bool_result_helpers_set,
                # TODO: Too many for now, so disable it
                warn_missing=False,
            )

        # Lets patch this up here, instead of having one set per operation.
        helper = helper.replace("xx", comparator.upper())

        if c_type.c_type == "PyObject *":
            emit("%s = %s( %s, %s );" % (to_name, helper, left_name, right_name))

            getErrorExitCode(
                check_name=to_name,
                release_names=(left_name, right_name),
                needs_check=needs_check,
                emit=emit,
                context=context,
            )

            context.addCleanupTempName(to_name)
        elif c_type.c_type in ("nuitka_bool", "void"):
            res_name = context.getIntResName()

            emit("%s = %s( %s, %s );" % (res_name, helper, left_name, right_name))

            getErrorExitBoolCode(
                condition="%s == -1" % res_name,
                release_names=(left_name, right_name),
                needs_check=needs_check,
                emit=emit,
                context=context,
            )

            c_type.emitAssignmentCodeFromBoolCondition(
                to_name=to_name, condition="%s != 0" % res_name, emit=emit
            )
        else:
            assert False, to_name.c_type

        return
    elif comparator == "exception_match":
        needs_check = expression.mayRaiseExceptionBool(BaseException)

        res_name = context.getIntResName()

        emit("%s = EXCEPTION_MATCH_BOOL( %s, %s );" % (res_name, left_name, right_name))

        getErrorExitBoolCode(
            condition="%s == -1" % res_name,
            release_names=(left_name, right_name),
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition="%s != 0" % res_name, emit=emit
        )
    else:
        assert False, comparator


def generateBuiltinIsinstanceCode(to_name, expression, emit, context):
    inst_name = context.allocateTempName("isinstance_inst")
    cls_name = context.allocateTempName("isinstance_cls")

    generateExpressionCode(
        to_name=inst_name,
        expression=expression.getInstance(),
        emit=emit,
        context=context,
    )
    generateExpressionCode(
        to_name=cls_name, expression=expression.getCls(), emit=emit, context=context
    )

    res_name = context.getIntResName()

    emit("%s = Nuitka_IsInstance( %s, %s );" % (res_name, inst_name, cls_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_names=(inst_name, cls_name),
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s != 0" % res_name, emit=emit
    )
