#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Tuple codes

"""

from .ConstantCodes import getConstantAccess
from .Helpers import generateExpressionCode
from .PythonAPICodes import generateCAPIObjectCode


def _areConstants(expressions):
    for expression in expressions:
        if not expression.isExpressionConstantRef():
            return False

        if expression.isMutable():
            return False
    return True


def generateTupleCreationCode(to_name, expression, emit, context):
    return getTupleCreationCode(
        to_name  = to_name,
        elements = expression.getElements(),
        emit     = emit,
        context  = context
    )


def getTupleCreationCode(to_name, elements, emit, context):
    if _areConstants(elements):
        getConstantAccess(
            to_name  = to_name,
            constant = tuple(
                element.getConstant() for element in elements
            ),
            emit     = emit,
            context  = context
        )
    else:
        emit(
            "%s = PyTuple_New( %d );" % (
                to_name,
                len(elements)
            )
        )

        context.addCleanupTempName(to_name)

        element_name = context.allocateTempName("tuple_element")

        for count, element in enumerate(elements):
            generateExpressionCode(
                to_name    = element_name,
                expression = element,
                emit       = emit,
                context    = context
            )

            if not context.needsCleanup(element_name):
                emit("Py_INCREF( %s );" % element_name)
            else:
                context.removeCleanupTempName(element_name)

            emit(
                "PyTuple_SET_ITEM( %s, %d, %s );" % (
                    to_name,
                    count,
                    element_name
                )
            )


def generateBuiltinTupleCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "PySequence_Tuple",
        arg_desc   = (
            ("tuple_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )
