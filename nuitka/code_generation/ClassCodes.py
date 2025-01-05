#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Codes for classes.

Most the class specific stuff is solved in re-formulation. Only the selection
of the metaclass remains as specific.
"""

from nuitka.PythonVersions import python_version

from .AttributeCodes import getAttributeLookupCode
from .CodeHelpers import (
    generateChildExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitCode, getReleaseCode


def generateSelectMetaclassCode(to_name, expression, emit, context):
    metaclass_name, bases_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    # This is used for Python3 only.
    assert python_version >= 0x300

    arg_names = [metaclass_name, bases_name]

    with withObjectCodeTemporaryAssignment(
        to_name, "metaclass_result", expression, emit, context
    ) as value_name:
        emit(
            "%s = SELECT_METACLASS(tstate, %s);"
            % (value_name, ", ".join(str(arg_name) for arg_name in arg_names))
        )

        getErrorExitCode(
            check_name=value_name, release_names=arg_names, emit=emit, context=context
        )

        context.addCleanupTempName(value_name)


def generateBuiltinSuper1Code(to_name, expression, emit, context):
    (type_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "super_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = BUILTIN_SUPER2(tstate, moduledict_%s, %s, NULL);"
            % (
                value_name,
                context.getModuleCodeName(),
                type_name if type_name is not None else "NULL",
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_name=type_name,
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def generateBuiltinSuperCode(to_name, expression, emit, context):
    type_name, object_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "super_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = BUILTIN_SUPER%d(tstate, moduledict_%s, %s, %s);"
            % (
                value_name,
                2 if expression.isExpressionBuiltinSuper2() else 0,
                context.getModuleCodeName(),
                type_name if type_name is not None else "NULL",
                object_name if object_name is not None else "NULL",
            )
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=(type_name, object_name),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


def generateTypeOperationPrepareCode(to_name, expression, emit, context):
    type_name, args_name, kwargs_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    prepare_func_name = context.allocateTempName("prepare_func")

    getAttributeLookupCode(
        to_name=prepare_func_name,
        source_name=type_name,
        attribute_name="__prepare__",
        # Types have it.
        needs_check=False,
        emit=emit,
        context=context,
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "prepare_value", expression, emit, context
    ) as value_name:
        emit(
            "%s = CALL_FUNCTION(tstate, %s, %s, %s);"
            % (
                value_name,
                prepare_func_name,
                "const_tuple_empty" if args_name is None else args_name,
                "NULL" if kwargs_name is None else kwargs_name,
            )
        )

        getReleaseCode(release_name=prepare_func_name, emit=emit, context=context)

        getErrorExitCode(
            check_name=value_name,
            release_names=(type_name, args_name, kwargs_name),
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(value_name)


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
