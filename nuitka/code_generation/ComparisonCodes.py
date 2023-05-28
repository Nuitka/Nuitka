#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.nodes.shapes.BuiltinTypeShapes import tshape_bool
from nuitka.nodes.shapes.StandardShapes import tshape_unknown
from nuitka.PythonOperators import (
    comparison_inversions,
    rich_comparison_arg_swaps,
)

from .c_types.CTypeBooleans import CTypeBool
from .c_types.CTypeNuitkaBooleans import CTypeNuitkaBoolEnum
from .c_types.CTypeNuitkaVoids import CTypeNuitkaVoidEnum
from .c_types.CTypePyObjectPointers import CTypePyObjectPtr
from .CodeHelpers import generateChildExpressionsCode, generateExpressionCode
from .CodeHelperSelection import selectCodeHelper
from .ComparisonHelperDefinitions import (
    getNonSpecializedComparisonOperations,
    getSpecializedComparisonOperations,
    rich_comparison_codes,
    rich_comparison_subset_codes,
)
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes,
)
from .ExpressionCTypeSelectionHelpers import decideExpressionCTypes


def _handleArgumentSwapAndInversion(
    comparator, needs_argument_swap, left_c_type, right_c_type
):
    needs_result_inversion = False
    if needs_argument_swap:
        comparator = rich_comparison_arg_swaps[comparator]
    else:
        # Same types, we can swap too, but this time to avoid the comparator variety.
        if (
            left_c_type is right_c_type
            and comparator not in rich_comparison_subset_codes
        ):
            needs_result_inversion = True
            comparator = comparison_inversions[comparator]

    return comparator, needs_result_inversion


def getRichComparisonCode(
    to_name, comparator, left, right, needs_check, source_ref, emit, context
):
    # This is detail rich stuff, encoding the complexity of what helpers are
    # available, and can be used as a fallback.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    # TODO: Move the value_name to a context generator, then this will be
    # a bit less complex.
    (
        unknown_types,
        needs_argument_swap,
        left_shape,
        right_shape,
        left_c_type,
        right_c_type,
    ) = decideExpressionCTypes(left=left, right=right, may_swap_arguments="always")

    if unknown_types:
        assert not needs_argument_swap
        needs_result_inversion = False
    else:
        # Same types, we can swap too, but this time to avoid the comparator variety.
        comparator, needs_result_inversion = _handleArgumentSwapAndInversion(
            comparator, needs_argument_swap, left_c_type, right_c_type
        )

    # If a more specific C type was picked that "PyObject *" then we can use that to have the helper.
    helper_type = target_type = to_name.getCType()

    if needs_check:
        # If an exception may occur, we do not have the "NVOID" helpers though, we
        # instead can use the CTypeNuitkaBoolEnum that will easily convert to
        # it.
        if helper_type is CTypeNuitkaVoidEnum:
            helper_type = CTypeNuitkaBoolEnum

        # Need to represent the intermediate exception, so we cannot have that.
        if helper_type is CTypeBool:
            helper_type = CTypeNuitkaBoolEnum

        report_missing = True
    else:
        # If no exception can occur, do not require a helper that can indicate
        # it, but use the one that produces simpler code, this means we can
        # avoid the CTypeNuitkaBoolEnum (NBOOL) helpers except for things that
        # can really raise. Once we have expression for types depending on the
        # value to raise or not, this will get us into trouble, due to using a
        # fallback
        helper_type = CTypeBool
        report_missing = False

    specialized_helpers_set = getSpecializedComparisonOperations()
    non_specialized_helpers_set = getNonSpecializedComparisonOperations()

    prefix = "RICH_COMPARE_" + rich_comparison_codes[comparator]

    helper_type, helper_function = selectCodeHelper(
        prefix=prefix,
        specialized_helpers_set=specialized_helpers_set,
        non_specialized_helpers_set=non_specialized_helpers_set,
        result_type=helper_type,
        left_shape=left_shape,
        right_shape=right_shape,
        left_c_type=left_c_type,
        right_c_type=right_c_type,
        argument_swap=needs_argument_swap,
        report_missing=report_missing,
        source_ref=source_ref,
    )

    # If we failed to find CTypeBool, that should be OK.
    if helper_function is None and not report_missing:
        helper_type, helper_function = selectCodeHelper(
            prefix=prefix,
            specialized_helpers_set=specialized_helpers_set,
            non_specialized_helpers_set=non_specialized_helpers_set,
            result_type=CTypeNuitkaBoolEnum,
            left_shape=left_shape,
            right_shape=right_shape,
            left_c_type=left_c_type,
            right_c_type=right_c_type,
            argument_swap=needs_argument_swap,
            report_missing=True,
            source_ref=source_ref,
        )

    # print("PICKED", left, right, left_c_type, right_c_type, helper_function)

    if helper_function is None:
        # Give up and warn about it.
        left_c_type = CTypePyObjectPtr
        right_c_type = CTypePyObjectPtr

        helper_type, helper_function = selectCodeHelper(
            prefix=prefix,
            specialized_helpers_set=specialized_helpers_set,
            non_specialized_helpers_set=non_specialized_helpers_set,
            result_type=helper_type,
            left_shape=tshape_unknown,
            right_shape=tshape_unknown,
            left_c_type=left_c_type,
            right_c_type=right_c_type,
            argument_swap=needs_argument_swap,
            report_missing=True,
            source_ref=source_ref,
        )

        assert helper_function is not None, (to_name, left_shape, right_shape)

    left_name = context.allocateTempName("cmp_expr_left", type_name=left_c_type.c_type)
    right_name = context.allocateTempName(
        "cmp_expr_right", type_name=right_c_type.c_type
    )

    generateExpressionCode(
        to_name=left_name, expression=left, emit=emit, context=context
    )
    generateExpressionCode(
        to_name=right_name, expression=right, emit=emit, context=context
    )

    if needs_argument_swap:
        arg1_name = right_name
        arg2_name = left_name
    else:
        arg1_name = left_name
        arg2_name = right_name

    # May need to convert return value.
    if helper_type is not target_type:
        value_name = context.allocateTempName(
            to_name.code_name + "_" + helper_type.helper_code.lower(),
            type_name=helper_type.c_type,
            unique=to_name.code_name == "tmp_unused",
        )
    else:
        value_name = to_name

    emit(
        "%s = %s(%s, %s);"
        % (
            value_name,
            helper_function,
            arg1_name,
            arg2_name,
        )
    )

    if value_name.getCType().hasErrorIndicator():
        getErrorExitCode(
            check_name=value_name,
            release_names=(left_name, right_name),
            needs_check=needs_check,
            emit=emit,
            context=context,
        )
    else:
        # Otherwise we picked the wrong kind of helper.
        assert not needs_check, (
            to_name,
            left_shape,
            right_shape,
            helper_function,
            value_name.getCType(),
        )

        getReleaseCodes(
            release_names=(left_name, right_name), emit=emit, context=context
        )

    # TODO: Depending on operation, we could not produce a reference, if result *must*
    # be boolean, but then we would have some helpers that do it, and some that do not
    # do it.
    if helper_type is CTypePyObjectPtr:
        context.addCleanupTempName(value_name)

    if value_name is not to_name:
        target_type.emitAssignConversionCode(
            to_name=to_name,
            value_name=value_name,
            # TODO: Right now we don't do conversions here that could fail.
            needs_check=False,
            emit=emit,
            context=context,
        )

    # When this is done on freshly assigned "Py_True" and "Py_False", the C
    # compiler should be able to optimize it away by inlining "CHECK_IF_TRUE"
    # branches on these two values.
    if needs_result_inversion:
        target_type.emitAssignInplaceNegatedValueCode(
            to_name=to_name,
            # We only do get here, target_type doesn't cause issues.
            needs_check=False,
            emit=emit,
            context=context,
        )


def generateComparisonExpressionCode(to_name, expression, emit, context):
    left = expression.subnode_left
    right = expression.subnode_right

    comparator = expression.getComparator()

    type_name = "PyObject *"
    if comparator in ("Is", "IsNot"):
        if left.getTypeShape() is tshape_bool and right.getTypeShape() is tshape_bool:
            type_name = "nuitka_bool"

    left_name = context.allocateTempName("cmp_expr_left", type_name=type_name)
    right_name = context.allocateTempName("cmp_expr_right", type_name=type_name)

    generateExpressionCode(
        to_name=left_name, expression=left, emit=emit, context=context
    )
    generateExpressionCode(
        to_name=right_name, expression=right, emit=emit, context=context
    )

    if comparator in ("In", "NotIn"):
        needs_check = right.mayRaiseExceptionIn(BaseException, expression.subnode_left)

        res_name = context.getIntResName()

        emit(
            "%s = PySequence_Contains(%s, %s);"
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
    elif comparator == "Is":
        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition="%s == %s" % (left_name, right_name), emit=emit
        )

        getReleaseCodes(
            release_names=(left_name, right_name), emit=emit, context=context
        )
    elif comparator == "IsNot":
        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition="%s != %s" % (left_name, right_name), emit=emit
        )

        getReleaseCodes(
            release_names=(left_name, right_name), emit=emit, context=context
        )
    elif comparator in ("exception_match", "exception_mismatch"):
        needs_check = expression.mayRaiseExceptionComparison()

        res_name = context.getIntResName()

        emit("%s = EXCEPTION_MATCH_BOOL(%s, %s);" % (res_name, left_name, right_name))

        getErrorExitBoolCode(
            condition="%s == -1" % res_name,
            release_names=(left_name, right_name),
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name,
            condition="%s %s 0"
            % (res_name, "!=" if comparator == "exception_match" else "=="),
            emit=emit,
        )
    else:
        assert False, comparator


def generateRichComparisonExpressionCode(to_name, expression, emit, context):
    return getRichComparisonCode(
        to_name=to_name,
        comparator=expression.getComparator(),
        left=expression.subnode_left,
        right=expression.subnode_right,
        needs_check=expression.mayRaiseExceptionComparison(),
        source_ref=expression.source_ref,
        emit=emit,
        context=context,
    )


def generateBuiltinIsinstanceCode(to_name, expression, emit, context):
    inst_name = context.allocateTempName("isinstance_inst")
    cls_name = context.allocateTempName("isinstance_cls")

    generateExpressionCode(
        to_name=inst_name,
        expression=expression.subnode_instance,
        emit=emit,
        context=context,
    )
    generateExpressionCode(
        to_name=cls_name,
        expression=expression.subnode_classes,
        emit=emit,
        context=context,
    )

    context.setCurrentSourceCodeReference(expression.getCompatibleSourceReference())

    res_name = context.getIntResName()

    emit("%s = PyObject_IsInstance(%s, %s);" % (res_name, inst_name, cls_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_names=(inst_name, cls_name),
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s != 0" % res_name, emit=emit
    )


def generateBuiltinIssubclassCode(to_name, expression, emit, context):
    cls_name = context.allocateTempName("issubclass_cls")
    classes_name = context.allocateTempName("issubclass_classes")

    generateExpressionCode(
        to_name=cls_name,
        expression=expression.subnode_cls,
        emit=emit,
        context=context,
    )
    generateExpressionCode(
        to_name=classes_name,
        expression=expression.subnode_classes,
        emit=emit,
        context=context,
    )

    context.setCurrentSourceCodeReference(expression.getCompatibleSourceReference())

    res_name = context.getIntResName()

    emit("%s = PyObject_IsSubclass(%s, %s);" % (res_name, cls_name, classes_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_names=(cls_name, classes_name),
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s != 0" % res_name, emit=emit
    )


def generateTypeCheckCode(to_name, expression, emit, context):
    cls_name = context.allocateTempName("type_check_cls")

    generateExpressionCode(
        to_name=cls_name,
        expression=expression.subnode_cls,
        emit=emit,
        context=context,
    )
    context.setCurrentSourceCodeReference(expression.getCompatibleSourceReference())

    res_name = context.getIntResName()

    emit("%s = PyType_Check(%s);" % (res_name, cls_name))

    getReleaseCode(
        release_name=cls_name,
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s != 0" % res_name, emit=emit
    )


def generateSubtypeCheckCode(to_name, expression, emit, context):
    left_name, right_name = generateChildExpressionsCode(
        expression=expression,
        emit=emit,
        context=context,
    )
    context.setCurrentSourceCodeReference(expression.getCompatibleSourceReference())

    res_name = context.getBoolResName()

    emit(
        "%s = Nuitka_Type_IsSubtype((PyTypeObject *)%s, (PyTypeObject *)%s);"
        % (res_name, left_name, right_name)
    )

    getReleaseCodes(
        release_names=(left_name, right_name),
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition=res_name, emit=emit
    )


def generateMatchTypeCheckMappingCode(to_name, expression, emit, context):
    cls_name = context.allocateTempName("mapping_check_cls")

    generateExpressionCode(
        to_name=cls_name,
        expression=expression.subnode_value,
        emit=emit,
        context=context,
    )

    res_name = context.getIntResName()

    emit("%s = Py_TYPE(%s)->tp_flags & Py_TPFLAGS_MAPPING;" % (res_name, cls_name))

    getReleaseCode(
        release_name=cls_name,
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s" % res_name, emit=emit
    )


def generateMatchTypeCheckSequenceCode(to_name, expression, emit, context):
    cls_name = context.allocateTempName("sequence_check_cls")

    generateExpressionCode(
        to_name=cls_name,
        expression=expression.subnode_value,
        emit=emit,
        context=context,
    )

    res_name = context.getIntResName()

    emit("%s = Py_TYPE(%s)->tp_flags & Py_TPFLAGS_SEQUENCE;" % (res_name, cls_name))

    getReleaseCode(
        release_name=cls_name,
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s" % res_name, emit=emit
    )
