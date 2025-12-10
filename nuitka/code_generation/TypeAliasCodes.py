#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for type alias statement helpers."""

from .CodeHelpers import (
    generateChildExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitCode
from .TupleCodes import getTupleCreationCode


def generateTypeAliasCode(to_name, expression, emit, context):
    type_params_name = context.allocateTempName("type_params_value")
    getTupleCreationCode(
        to_name=type_params_name,
        elements=expression.subnode_type_params,
        emit=emit,
        context=context,
    )

    compute_value_name = generateChildExpressionCode(
        expression=expression.subnode_value, emit=emit, context=context
    )

    type_alias_name = expression.subnode_name.getVariableName()

    with withObjectCodeTemporaryAssignment(
        to_name, "type_alias_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = MAKE_TYPE_ALIAS(%s, %s, %s, %s);"
            % (
                value_name,
                context.getConstantCode(constant=type_alias_name),
                type_params_name,
                compute_value_name,
                context.getConstantCode(constant=context.getModuleName().asString()),
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=(type_alias_name, compute_value_name, type_params_name),
            emit=emit,
            context=context,
            needs_check=expression.mayRaiseExceptionOperation(),
        )

        context.addCleanupTempName(value_name)


def generateTypeVarCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "type_var_value", expression, emit, context
    ) as value_name:
        if expression.isExpressionTypeVariable():
            # TypeVar
            helper_function = "MAKE_TYPE_VAR"
        elif expression.isExpressionTypeVariableTuple():
            # TypeVarTuple
            helper_function = "MAKE_TYPE_VAR_TUPLE"
        else:
            # ParamSpec
            assert expression.isExpressionParameterSpecification()
            helper_function = "MAKE_PARAM_SPEC"

        emit(
            "%s = %s(tstate, %s);"
            % (
                value_name,
                helper_function,
                context.getConstantCode(constant=expression.name),
            )
        )

        getErrorExitCode(
            check_name=value_name,
            emit=emit,
            context=context,
            needs_check=False,
        )

        context.addCleanupTempName(value_name)


def generateTypeGenericCode(to_name, expression, emit, context):
    type_params_value = generateChildExpressionCode(
        expression=expression.subnode_type_params, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "type_params_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = MAKE_TYPE_GENERIC(tstate, %s);"
            % (
                value_name,
                type_params_value,
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_name=type_params_value,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
