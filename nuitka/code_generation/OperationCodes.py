#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for unary, binary, and in-place operations."""

from nuitka.nodes.shapes.StandardShapes import tshape_unknown

from .BinaryOperationHelperDefinitions import (
    getCodeNameForBinaryOperation,
    getNonSpecializedBinaryOperations,
    getSpecializedBinaryOperations,
)
from .c_types.CTypeBooleans import CTypeBool
from .c_types.CTypeNuitkaBooleans import CTypeNuitkaBoolEnum
from .c_types.CTypeNuitkaVoids import CTypeNuitkaVoidEnum
from .c_types.CTypePyObjectPointers import CTypePyObjectPtr
from .c_types.CTypeVoids import CTypeVoid
from .CodeHelpers import (
    doesExpressionWriteVariable,
    generateChildExpressionsCode,
    generateExpressionCode,
    promoteBorrowedValue,
    withBorrowedValueScope,
    withObjectCodeTemporaryAssignment,
)
from .CodeHelperSelection import selectCodeHelper
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCodes,
    getTakeReferenceCode,
)
from .ExpressionCTypeSelectionHelpers import decideExpressionCTypes


def generateOperationBinaryCode(to_name, expression, emit, context):
    with withBorrowedValueScope(context):
        _getBinaryOperationCode(
            to_name=to_name,
            operator=expression.getOperator(),
            inplace=expression.isInplaceSuspect(),
            needs_check=expression.mayRaiseExceptionOperation(),
            left=expression.subnode_left,
            right=expression.subnode_right,
            source_ref=expression.source_ref,
            emit=emit,
            context=context,
        )


def generateOperationNotCode(to_name, expression, emit, context):
    # TODO: We badly need to support target boolean C type here, or else an object is created from the argument.
    (arg_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    res_name = context.getIntResName()

    emit("%s = CHECK_IF_TRUE(%s);" % (res_name, arg_name))

    getErrorExitBoolCode(
        condition="%s == -1" % res_name,
        release_name=arg_name,
        needs_check=expression.subnode_operand.mayRaiseExceptionBool(BaseException),
        emit=emit,
        context=context,
    )

    to_name.getCType().emitAssignmentCodeFromBoolCondition(
        to_name=to_name, condition="%s == 0" % res_name, emit=emit
    )


def generateOperationUnaryCode(to_name, expression, emit, context):
    (arg_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    _getUnaryOperationCode(
        to_name=to_name,
        expression=expression,
        operator=expression.getOperator(),
        arg_name=arg_name,
        needs_check=expression.mayRaiseExceptionOperation(),
        emit=emit,
        context=context,
    )


def _getBinaryOperationCode(
    to_name, operator, inplace, left, right, needs_check, source_ref, emit, context
):
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    (
        _unknown_types,
        needs_argument_swap,
        left_shape,
        right_shape,
        left_c_type,
        right_c_type,
    ) = decideExpressionCTypes(
        left=left,
        right=right,
        may_swap_arguments=(
            "never"
            if inplace
            else (
                "number"
                if operator in ("Add", "Mult", "BitOr", "BitAnd", "BitXor")
                else "never"
            )
        ),
        context=context,
    )

    prefix = "%s_OPERATION_%s" % (
        "INPLACE" if operator[0] == "I" else "BINARY",
        getCodeNameForBinaryOperation(operator),
    )

    specialized_helpers_set = getSpecializedBinaryOperations(operator)
    non_specialized_helpers_set = getNonSpecializedBinaryOperations(operator)

    report_missing = True

    helper_type = target_type = None if operator[0] == "I" else to_name.getCType()

    if helper_type is not None:
        if needs_check and helper_type is not None:
            # Specialized helpers do not exist for "NVOID"; fall back to "NBOOL".
            if helper_type is CTypeNuitkaVoidEnum:
                helper_type = CTypeNuitkaBoolEnum
                report_missing = False
        else:
            # TODO: Use "CTypeBool" ("CBOOL") for non-raising void operations
            # once value-dependent raising is tracked.
            if helper_type is CTypeVoid:
                helper_type = CTypeNuitkaBoolEnum
                report_missing = False

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

    if helper_function is None and target_type is CTypeBool:
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

    if helper_function is None:
        left_c_type = CTypePyObjectPtr
        right_c_type = CTypePyObjectPtr

        helper_type, helper_function = selectCodeHelper(
            prefix=prefix,
            specialized_helpers_set=specialized_helpers_set,
            non_specialized_helpers_set=non_specialized_helpers_set,
            result_type=CTypePyObjectPtr if helper_type is not None else None,
            left_shape=tshape_unknown,
            right_shape=tshape_unknown,
            left_c_type=left_c_type,
            right_c_type=right_c_type,
            argument_swap=False,
            report_missing=True,
            source_ref=source_ref,
        )

        assert helper_function is not None, (left, right)

    left_name = context.allocateTempName(
        "%s_expr_left" % operator.lower(), type_name=left_c_type.c_type
    )
    right_name = context.allocateTempName(
        "%s_expr_right" % operator.lower(), type_name=right_c_type.c_type
    )

    inplace_owned_left = (
        inplace
        and left.isExpressionVariableRef()
        and doesExpressionWriteVariable(expression=right, variable=left.getVariable())
    )

    generateExpressionCode(
        to_name=left_name, expression=left, emit=emit, context=context
    )

    if not inplace:
        promoteBorrowedValue(
            value_name=left_name,
            later_expressions=(right,),
            emit=emit,
            context=context,
        )

    if inplace and left.isExpressionVariableRef():
        # The in-place code path transfers the variable reference into the
        # operation, protecting it here would conflict with that ownership.
        context.unregisterBorrowedValue(left_name)

        if inplace_owned_left and not context.needsCleanup(left_name):
            # The right value overwrites the variable, so the operation needs
            # its own reference to the left value.
            getTakeReferenceCode(left_name, emit)
            context.addCleanupTempName(left_name)

    generateExpressionCode(
        to_name=right_name, expression=right, emit=emit, context=context
    )

    if inplace or "INPLACE" in helper_function:
        assert not needs_argument_swap

        res_name = context.getBoolResName()

        if (
            not inplace_owned_left
            and left.isExpressionVariableRef()
            and left.getVariable().isModuleVariable()
        ):
            emit(
                "%s = %s = Py_NewRef(%s);"
                % (context.getInplaceLeftName(), left_name, left_name)
            )

        if (
            not left.isExpressionVariableRefOrTempVariableRef()
            and not context.needsCleanup(left_name)
        ):
            getTakeReferenceCode(left_name, emit)

        emit("%s = %s(&%s, %s);" % (res_name, helper_function, left_name, right_name))

        getErrorExitBoolCode(
            condition="%s == false" % res_name,
            release_names=(
                (right_name,) if inplace_owned_left else (left_name, right_name)
            ),
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        emit("%s = %s;" % (to_name, left_name))

        if inplace_owned_left:
            context.removeCleanupTempName(left_name)
            context.addCleanupTempName(to_name)
        elif not left.isExpressionVariableRefOrTempVariableRef():
            context.addCleanupTempName(to_name)
    else:
        if needs_argument_swap:
            arg1_name = right_name
            arg2_name = left_name
            arg1_c_type = right_c_type
            arg2_c_type = left_c_type
        else:
            arg1_name = left_name
            arg2_name = right_name
            arg1_c_type = left_c_type
            arg2_c_type = right_c_type

        if helper_type is not target_type:
            value_name = context.allocateTempName(
                to_name.code_name + "_" + helper_type.helper_code.lower(),
                type_name=helper_type.c_type,
                unique=to_name.code_name == "tmp_unused",
            )
        else:
            value_name = to_name

        if helper_type.isDualType():
            res_name = context.getBoolResName()

            # TODO: If possible, pass variable storage directly to avoid useless
            # copy.
            emit(
                "%s = %s(&%s, %s%s, %s%s);"
                % (
                    res_name,
                    helper_function,
                    value_name,
                    "&" if arg1_c_type.isDualType() else "",
                    arg1_name,
                    "&" if arg2_c_type.isDualType() else "",
                    arg2_name,
                )
            )

            getErrorExitBoolCode(
                condition="%s == false" % res_name,
                release_names=(left_name, right_name),
                needs_check=needs_check,
                emit=emit,
                context=context,
            )
        else:
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
                assert not needs_check, value_name.getCType()

                getReleaseCodes(
                    release_names=(left_name, right_name), emit=emit, context=context
                )

        # TODO: Depending on operation, we could not produce a reference, if result *must*
        # be boolean, but then we would have some helpers that do it, and some that do not
        # do it.
        if helper_type.hasReleaseCode():
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


unary_operator_codes = {
    "UAdd": ("PyNumber_Positive", 1),
    "USub": ("PyNumber_Negative", 1),
    "Invert": ("PyNumber_Invert", 1),
    "Repr": ("PyObject_Repr", 1),
    "Not": ("UNARY_NOT", 0),
}


def _getUnaryOperationCode(
    to_name, expression, operator, arg_name, needs_check, emit, context
):
    impl_helper, ref_count = unary_operator_codes[operator]

    helper = "UNARY_OPERATION"
    prefix_args = (impl_helper,)

    with withObjectCodeTemporaryAssignment(
        to_name, "op_%s_res" % operator.lower(), expression, emit, context
    ) as value_name:
        emit(
            "%s = %s(%s);"
            % (
                value_name,
                helper,
                ", ".join(str(arg_name) for arg_name in prefix_args + (arg_name,)),
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_name=arg_name,
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        if ref_count:
            context.addCleanupTempName(value_name)


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
