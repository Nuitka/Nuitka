#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Codes for classes.

Most the class specific stuff is solved in re-formulation. Only the selection
of the metaclass remains as specific.
"""

from nuitka.PythonVersions import python_version

from .CodeHelpers import generateChildExpressionsCode
from .ErrorCodes import getErrorExitCode
from .PythonAPICodes import generateCAPIObjectCode0


def generateSelectMetaclassCode(to_name, expression, emit, context):
    metaclass_name, bases_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    # This is used for Python3 only.
    assert python_version >= 300

    args = [
        metaclass_name,
        bases_name
    ]


    emit(
        "%s = SELECT_METACLASS( %s );" % (
            to_name,
            ", ".join(args)
        )
    )

    getErrorExitCode(
        check_name    = to_name,
        release_names = args,
        emit          = emit,
        context       = context
    )

    context.addCleanupTempName(to_name)


def generateBuiltinSuperCode(to_name, expression, emit, context):
    type_name, object_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit(
        "%s = BUILTIN_SUPER( %s, %s );" % (
            to_name,
            type_name if type_name is not None else "NULL",
            object_name if object_name is not None else "NULL"
        )
    )

    getErrorExitCode(
        check_name    = to_name,
        release_names = (type_name, object_name),
        emit          = emit,
        context       = context
    )

    context.addCleanupTempName(to_name)


def generateBuiltinIsinstanceCode(to_name, expression, emit, context):
    generateCAPIObjectCode0(
        to_name    = to_name,
        capi       = "BUILTIN_ISINSTANCE",
        arg_desc   = (
            ("isinstance_inst", expression.getInstance()),
            ("isinstance_cls", expression.getCls()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )
