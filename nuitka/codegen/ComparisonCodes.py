#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.containers.oset import OrderedSet
from nuitka.nodes.shapes.BuiltinTypeShapes import tshape_bool
from nuitka.Options import isExperimental

from . import OperatorCodes
from .CodeHelpers import generateExpressionCode, pickCodeHelper
from .ErrorCodes import getErrorExitBoolCode, getReleaseCode, getReleaseCodes

specialized_cmp_helpers_set = OrderedSet(
    (
        "RICH_COMPARE_xx_OBJECT_OBJECT_OBJECT",
        "RICH_COMPARE_xx_CBOOL_OBJECT_OBJECT",
        "RICH_COMPARE_xx_NBOOL_OBJECT_OBJECT",
        "RICH_COMPARE_xx_OBJECT_OBJECT_STR",
        "RICH_COMPARE_xx_CBOOL_OBJECT_STR",
        "RICH_COMPARE_xx_NBOOL_OBJECT_STR",
        "RICH_COMPARE_xx_OBJECT_STR_OBJECT",
        "RICH_COMPARE_xx_CBOOL_STR_OBJECT",
        "RICH_COMPARE_xx_NBOOL_STR_OBJECT",
        "RICH_COMPARE_xx_OBJECT_STR_STR",
        "RICH_COMPARE_xx_CBOOL_STR_STR",
        "RICH_COMPARE_xx_NBOOL_STR_STR",
        "RICH_COMPARE_xx_OBJECT_OBJECT_UNICODE",
        "RICH_COMPARE_xx_CBOOL_OBJECT_UNICODE",
        "RICH_COMPARE_xx_NBOOL_OBJECT_UNICODE",
        "RICH_COMPARE_xx_OBJECT_UNICODE_OBJECT",
        "RICH_COMPARE_xx_CBOOL_UNICODE_OBJECT",
        "RICH_COMPARE_xx_NBOOL_UNICODE_OBJECT",
        "RICH_COMPARE_xx_OBJECT_UNICODE_UNICODE",
        "RICH_COMPARE_xx_CBOOL_UNICODE_UNICODE",
        "RICH_COMPARE_xx_NBOOL_UNICODE_UNICODE",
        "RICH_COMPARE_xx_CBOOL_OBJECT_BYTES",
        "RICH_COMPARE_xx_NBOOL_OBJECT_BYTES",
        "RICH_COMPARE_xx_OBJECT_BYTES_OBJECT",
        "RICH_COMPARE_xx_CBOOL_BYTES_OBJECT",
        "RICH_COMPARE_xx_NBOOL_BYTES_OBJECT",
        "RICH_COMPARE_xx_OBJECT_BYTES_BYTES",
        "RICH_COMPARE_xx_CBOOL_BYTES_BYTES",
        "RICH_COMPARE_xx_NBOOL_BYTES_BYTES",
        #        "RICH_COMPARE_xx_OBJECT_UNICODE",
        #        "RICH_COMPARE_xx_LONG_OBJECT",
        #        "RICH_COMPARE_xx_UNICODE_OBJECT",
        #        "RICH_COMPARE_xx_LONG_LONG",
        #        "RICH_COMPARE_xx_UNICODE_UNICODE",
        "RICH_COMPARE_xx_OBJECT_INT_INT",
        "RICH_COMPARE_xx_CBOOL_INT_INT",
        "RICH_COMPARE_xx_NBOOL_INT_INT",
        "RICH_COMPARE_xx_OBJECT_OBJECT_INT",
        "RICH_COMPARE_xx_CBOOL_OBJECT_INT",
        "RICH_COMPARE_xx_NBOOL_OBJECT_INT",
        "RICH_COMPARE_xx_OBJECT_INT_OBJECT",
        "RICH_COMPARE_xx_CBOOL_INT_OBJECT",
        "RICH_COMPARE_xx_NBOOL_INT_OBJECT",
        "RICH_COMPARE_xx_OBJECT_LONG_LONG",
        "RICH_COMPARE_xx_CBOOL_LONG_LONG",
        "RICH_COMPARE_xx_NBOOL_LONG_LONG",
        "RICH_COMPARE_xx_OBJECT_OBJECT_LONG",
        "RICH_COMPARE_xx_CBOOL_OBJECT_LONG",
        "RICH_COMPARE_xx_NBOOL_OBJECT_LONG",
        "RICH_COMPARE_xx_OBJECT_LONG_OBJECT",
        "RICH_COMPARE_xx_CBOOL_LONG_OBJECT",
        "RICH_COMPARE_xx_NBOOL_LONG_OBJECT",
        "RICH_COMPARE_xx_OBJECT_FLOAT_FLOAT",
        "RICH_COMPARE_xx_CBOOL_FLOAT_FLOAT",
        "RICH_COMPARE_xx_NBOOL_FLOAT_FLOAT",
        "RICH_COMPARE_xx_OBJECT_OBJECT_FLOAT",
        "RICH_COMPARE_xx_CBOOL_OBJECT_FLOAT",
        "RICH_COMPARE_xx_NBOOL_OBJECT_FLOAT",
        "RICH_COMPARE_xx_OBJECT_FLOAT_OBJECT",
        "RICH_COMPARE_xx_CBOOL_FLOAT_OBJECT",
        "RICH_COMPARE_xx_NBOOL_FLOAT_OBJECT",
        "RICH_COMPARE_xx_OBJECT_TUPLE_TUPLE",
        "RICH_COMPARE_xx_CBOOL_TUPLE_TUPLE",
        "RICH_COMPARE_xx_NBOOL_TUPLE_TUPLE",
        "RICH_COMPARE_xx_OBJECT_OBJECT_TUPLE",
        "RICH_COMPARE_xx_CBOOL_OBJECT_TUPLE",
        "RICH_COMPARE_xx_NBOOL_OBJECT_TUPLE",
        "RICH_COMPARE_xx_OBJECT_TUPLE_OBJECT",
        "RICH_COMPARE_xx_CBOOL_TUPLE_OBJECT",
        "RICH_COMPARE_xx_NBOOL_TUPLE_OBJECT",
        "RICH_COMPARE_xx_OBJECT_LIST_LIST",
        "RICH_COMPARE_xx_CBOOL_LIST_LIST",
        "RICH_COMPARE_xx_NBOOL_LIST_LIST",
        "RICH_COMPARE_xx_OBJECT_OBJECT_LIST",
        "RICH_COMPARE_xx_CBOOL_OBJECT_LIST",
        "RICH_COMPARE_xx_NBOOL_OBJECT_LIST",
        "RICH_COMPARE_xx_OBJECT_LIST_OBJECT",
        "RICH_COMPARE_xx_CBOOL_LIST_OBJECT",
        "RICH_COMPARE_xx_NBOOL_LIST_OBJECT",
        #        "RICH_COMPARE_xx_CBOOL_OBJECT_LONG",
        #        "RICH_COMPARE_xx_CBOOL_OBJECT_UNICODE",
        #        "RICH_COMPARE_xx_CBOOL_LONG_OBJECT",
        #        "RICH_COMPARE_xx_CBOOL_UNICODE_OBJECT",
        #        "RICH_COMPARE_xx_CBOOL_LONG_LONG",
        #        "RICH_COMPARE_xx_CBOOL_UNICODE_UNICODE",
    )
)


def generateComparisonExpressionCode(to_name, expression, emit, context):
    left = expression.subnode_left
    right = expression.subnode_right

    comparator = expression.getComparator()

    type_name = "PyObject *"
    if comparator in ("Is", "IsNot"):
        if left.getTypeShape() is tshape_bool and right.getTypeShape() is tshape_bool:
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
    elif comparator in OperatorCodes.rich_comparison_codes:
        needs_check = expression.mayRaiseExceptionComparison()

        # TODO: This is probably not really worth it, but we used to do it.
        # if comparator == "Eq" and not context.mayRecurse():
        #     suffix = "_NORECURSE"
        # else:
        #     suffix = ""

        helper = pickCodeHelper(
            prefix="RICH_COMPARE_xx",
            suffix="",
            target_type=to_name.getCType(),
            left_shape=left.getTypeShape(),
            right_shape=expression.subnode_right.getTypeShape(),
            helpers=specialized_cmp_helpers_set,
            nonhelpers=(),
            source_ref=expression.source_ref,
        )

        # Lets patch this up here, instead of having one set per comparison operation.
        helper.helper_name = helper.helper_name.replace(
            "xx", OperatorCodes.rich_comparison_codes[comparator]
        )

        helper.emitHelperCall(
            to_name=to_name,
            arg_names=(left_name, right_name),
            ref_count=1,
            needs_check=needs_check,
            emit=emit,
            context=context,
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

    if isExperimental("function-base"):
        emit("%s = PyObject_IsInstance(%s, %s);" % (res_name, inst_name, cls_name))
    else:
        emit("%s = Nuitka_IsInstance(%s, %s);" % (res_name, inst_name, cls_name))

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
    cls_name = context.allocateTempName("issubclass_cls")

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
