#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_int,
    tshape_long,
)
from nuitka.Options import isExperimental
from nuitka.PythonVersions import (
    isPythonValidCLongValue,
    isPythonValidDigitValue,
    python_version,
)

from . import OperatorCodes
from .c_types.CTypeCLongs import CTypeCLong, CTypeCLongDigit
from .c_types.CTypePyObjectPtrs import CTypePyObjectPtr
from .CodeHelpers import generateExpressionCode
from .CodeHelperSelection import selectCodeHelper
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes,
)

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
        "RICH_COMPARE_xx_OBJECT_INT_INT",
        "RICH_COMPARE_xx_CBOOL_INT_INT",
        "RICH_COMPARE_xx_NBOOL_INT_INT",
        "RICH_COMPARE_xx_OBJECT_INT_LONG",
        "RICH_COMPARE_xx_OBJECT_LONG_INT",
        # TODO: Make this work.
        # "RICH_COMPARE_xx_CBOOL_INT_LONG",
        # "RICH_COMPARE_xx_CBOOL_LONG_INT",
        # "RICH_COMPARE_xx_NBOOL_INT_LONG",
        # "RICH_COMPARE_xx_NBOOL_LONG_INT",
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
    )
)


def _pickIntIntComparisonShape(expression):
    # TODO: Enable once DIGIT and CLONG variants exist to mix with LONG and INT.
    if expression.isCompileTimeConstant() and isExperimental("comparison-c-types"):
        # On Python2, "INT_CLONG" is very fast as "CLONG" is the internal representation
        # of it, for Python3, it should be avoided, it usually is around 2**30.
        if python_version <= 0x300:
            c_type = CTypeCLong
        elif isPythonValidDigitValue(expression.getCompileTimeConstant()):
            c_type = CTypeCLongDigit
        elif isPythonValidCLongValue(expression.getCompileTimeConstant()):
            c_type = CTypeCLong
        else:
            c_type = CTypePyObjectPtr
    else:
        c_type = CTypePyObjectPtr

    return c_type


def getRichComparisonCode(
    to_name, comparator, left, right, needs_check, source_ref, emit, context
):
    # TODO: Move the value_name to a context generator, then this will be
    # a bit less.
    # This is detail rich stuff, pylint: disable=too-many-locals

    left_shape = left.getTypeShape()
    right_shape = right.getTypeShape()

    left_c_type = right_c_type = CTypePyObjectPtr

    if left_shape in (tshape_int, tshape_long):
        if right_shape in (tshape_int, tshape_long):
            left_c_type = _pickIntIntComparisonShape(right)
            right_c_type = _pickIntIntComparisonShape(right)

    # If a more specific C type was picked that "PyObject *" then we can use that to have the helper.
    target_type = to_name.getCType()

    helper_type, helper_function = selectCodeHelper(
        prefix="RICH_COMPARE_xx",
        specialized_helpers_set=specialized_cmp_helpers_set,
        nonspecialized=None,
        helper_type=target_type,
        left_shape=left_shape,
        right_shape=right_shape,
        left_c_type=left_c_type,
        right_c_type=right_c_type,
        source_ref=source_ref,
    )

    if helper_function is None:
        # Give up and warn about it.
        left_c_type = CTypePyObjectPtr
        right_c_type = CTypePyObjectPtr

        helper_type, helper_function = selectCodeHelper(
            prefix="RICH_COMPARE_xx",
            specialized_helpers_set=specialized_cmp_helpers_set,
            nonspecialized=None,
            helper_type=target_type,
            left_shape=tshape_unknown,
            right_shape=tshape_unknown,
            left_c_type=left_c_type,
            right_c_type=right_c_type,
            source_ref=source_ref,
        )

        assert helper_function is not None

    left_name = context.allocateTempName("cmp_expr_left", type_name=left_c_type.c_type)
    right_name = context.allocateTempName(
        "cmp_expr_right", type_name=right_c_type.c_type
    )

    # May not to convert return value now.
    if helper_type is not target_type:
        value_name = context.allocateTempName(
            to_name.code_name + "_" + helper_type.helper_code.lower(),
            type_name=helper_type.c_type,
            unique=to_name.code_name == "tmp_unused",
        )
    else:
        value_name = to_name

    generateExpressionCode(
        to_name=left_name, expression=left, emit=emit, context=context
    )
    generateExpressionCode(
        to_name=right_name, expression=right, emit=emit, context=context
    )

    emit(
        "%s = %s(%s, %s);"
        % (
            value_name,
            helper_function.replace(
                "xx", OperatorCodes.rich_comparison_codes[comparator]
            ),
            left_name,
            right_name,
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
        getReleaseCodes(
            release_names=(left_name, right_name), emit=emit, context=context
        )

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
