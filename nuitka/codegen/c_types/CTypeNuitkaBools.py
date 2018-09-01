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
""" CType classes for nuitka_bool, an enum to represent True, False, unassigned.

"""

from nuitka.codegen.ErrorCodes import (
    getAssertionCode,
    getLocalVariableReferenceErrorCode,
    getNameReferenceErrorCode
)

from .CTypeBases import CTypeBase


class CTypeNuitkaBoolEnum(CTypeBase):
    c_type = "nuitka_bool"

    @classmethod
    def getLocalVariableAssignCode(cls, variable_code_name, needs_release,
                                   tmp_name, ref_count, in_place):

        assert not in_place
        assert not ref_count

        if tmp_name.c_type == "nuitka_bool":
            return "%s = %s;" % (variable_code_name, tmp_name)

        if tmp_name.c_type == "PyObject *":
            test_code = "%s == Py_True" % tmp_name
        else:
            assert False, tmp_name

        return cls.getAssignmentCodeFromBoolCondition(
            to_name   = variable_code_name,
            condition = test_code
        )

    @classmethod
    def getLocalVariableInitTestCode(cls, variable_code_name):
        return "%s != NUITKA_BOOL_UNASSIGNED" % variable_code_name

    @classmethod
    def getTruthCheckCode(cls, value_name):
        return "%s == NUITKA_BOOL_TRUE" % value_name

    @classmethod
    def emitTruthCheckCode(cls, to_name, value_name, needs_check, emit, context):
        # Not using needs_check, pylint: disable=unused-argument
        emit(
            "%s = %s ? 1 : 0;" % (
                to_name,
                cls.getTruthCheckCode(value_name)
            )
        )

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # Nothing to do for this type, pylint: disable=unused-argument
        return value_name

    @classmethod
    def emitVariableValueCheckCode(cls, variable, value_name, emit, context):
        if variable.isModuleVariable():
            getNameReferenceErrorCode(
                variable_name = variable.getName(),
                condition     = "%s == NUITKA_BOOL_UNASSIGNED" % value_name,
                emit          = emit,
                context       = context
            )
        else:
            getLocalVariableReferenceErrorCode(
                variable  = variable,
                condition = "%s == NUITKA_BOOL_UNASSIGNED" % value_name,
                emit      = emit,
                context   = context
            )

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit, context):
        # Not using the context, pylint: disable=unused-argument
        emit(
            "assert( %s != NUITKA_BOOL_UNASSIGNED);" % value_name
        )

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        if value_name.c_type == cls.c_type:
            emit(
                "%s = %s;" % (
                    to_name,
                    value_name
                )
            )
        else:
            value_name.getCType().emitAssignmentCodeToNuitkaBool(
                to_name     = to_name,
                value_name  = value_name,
                needs_check = needs_check,
                emit        = emit,
                context     = context
            )

    @classmethod
    def getLocalVariableObjectAccessCode(cls, variable_code_name):
        return "%s == NUITKA_BOOL_TRUE ? Py_True : Py_False" % variable_code_name

    @classmethod
    def getInitValue(cls, init_from):
        if init_from is None:
            return "NUITKA_BOOL_UNASSIGNED"
        else:
            assert False, init_from
            return init_from

    @classmethod
    def getReleaseCode(cls, variable_code_name, needs_check, emit):
        # TODO: Allow optimization to not get here.
        pass

    @classmethod
    def getDeleteObjectCode(cls, variable_code_name, needs_check, tolerant,
                            variable, emit, context):
        if not needs_check:
            emit(
                "%s = NUITKA_BOOL_UNASSIGNED;" % variable_code_name
            )
        elif tolerant:
            emit(
                "%s = NUITKA_BOOL_UNASSIGNED;" % variable_code_name
            )
        else:
            res_name = context.getBoolResName()

            emit(
                "%s = %s == NUITKA_BOOL_UNASSIGNED;" % (
                    res_name,
                    variable_code_name,
                )
            )
            emit(
                "%s = NUITKA_BOOL_UNASSIGNED;" % variable_code_name
            )

            if variable.isLocalVariable():
                getLocalVariableReferenceErrorCode(
                    variable  = variable,
                    condition = "%s == false" % res_name,
                    emit      = emit,
                    context   = context
                )
            else:
                getAssertionCode(
                    check = "%s != false" % res_name,
                    emit  = emit
                )

    @classmethod
    def getAssignmentCodeFromBoolCondition(cls, to_name, condition):
        return "%(to_name)s = ( %(condition)s ) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;" % {
            "to_name" : to_name,
            "condition" : condition
        }
