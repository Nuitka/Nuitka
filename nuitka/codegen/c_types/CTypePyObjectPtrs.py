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
""" CType classes for PyObject *, PyObject **, and struct Nuitka_CellObject *

"""


from nuitka.codegen.ErrorCodes import (
    getAssertionCode,
    getCheckObjectCode,
    getErrorExitBoolCode,
    getLocalVariableReferenceErrorCode,
    getNameReferenceErrorCode
)
from nuitka.codegen.templates.CodeTemplatesVariables import (
    template_del_local_intolerant,
    template_del_local_known,
    template_del_local_tolerant,
    template_del_shared_intolerant,
    template_del_shared_known,
    template_del_shared_tolerant,
    template_release_clear,
    template_release_unclear,
    template_write_local_clear_ref0,
    template_write_local_clear_ref1,
    template_write_local_empty_ref0,
    template_write_local_empty_ref1,
    template_write_local_inplace,
    template_write_local_unclear_ref0,
    template_write_local_unclear_ref1,
    template_write_shared_clear_ref0,
    template_write_shared_clear_ref1,
    template_write_shared_inplace,
    template_write_shared_unclear_ref0,
    template_write_shared_unclear_ref1
)

from .CTypeBases import CTypeBase


class CPythonPyObjectPtrBase(CTypeBase):
    @classmethod
    def getLocalVariableAssignCode(cls, variable_code_name, needs_release,
                                   tmp_name, ref_count, in_place):
        if in_place:
            # Releasing is not an issue here, local variable reference never
            # gave a reference, and the in-place code deals with possible
            # replacement/release.
            template = template_write_local_inplace
        else:
            if ref_count:
                if needs_release is False:
                    template = template_write_local_empty_ref0
                elif needs_release is True:
                    template = template_write_local_clear_ref0
                else:
                    template = template_write_local_unclear_ref0
            else:
                if needs_release is False:
                    template = template_write_local_empty_ref1
                elif needs_release is True:
                    template = template_write_local_clear_ref1
                else:
                    template = template_write_local_unclear_ref1

        return template % {
            "identifier" : variable_code_name,
            "tmp_name"   : tmp_name
        }

    @classmethod
    def getTruthCheckCode(cls, value_name):
        return "CHECK_IF_TRUE( %s )" % value_name

    @classmethod
    def emitTruthCheckCode(cls, to_name, value_name, needs_check, emit, context):
        emit(
            "%s = CHECK_IF_TRUE( %s );" % (
                to_name,
                value_name
            )
        )

        if needs_check:
            getErrorExitBoolCode(
                condition   = "%s == -1" % to_name,
                needs_check = needs_check,
                emit        = emit,
                context     = context
            )


    @classmethod
    def getReleaseCode(cls, variable_code_name, needs_check, emit):
        if needs_check:
            template = template_release_unclear
        else:
            template = template_release_clear

        emit(
            template % {
                "identifier" : variable_code_name
            }
        )

    @classmethod
    def getAssignmentCodeFromBoolCondition(cls, to_name, condition):
        return "%(to_name)s = ( %(condition)s ) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;" % {
            "to_name"   : to_name,
            "condition" : condition
        }


    @classmethod
    def emitAssignmentCodeToNuitkaBool(cls, to_name, value_name, needs_check, emit, context):
        if needs_check:
            truth_name = context.allocateTempName("truth_name", "int")

            emit(
                "%s = CHECK_IF_TRUE( %s );" % (
                    truth_name,
                    value_name
                )
            )

            getErrorExitBoolCode(
                condition   = "%s == -1" % truth_name,
                emit        = emit,
                context     = context,
                needs_check = True
            )

            emit(
                "%s = %s == 1 ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;" % (
                    to_name,
                    truth_name
                )
            )
        else:
            emit(
                cls.getAssignmentCodeFromBoolCondition(
                    to_name   = to_name,
                    condition = "%s == 1",
                )
            )


class CTypePyObjectPtr(CPythonPyObjectPtrBase):
    c_type = "PyObject *"

    @classmethod
    def getInitValue(cls, init_from):
        if init_from is None:
            return "NULL"
        else:
            return init_from

    @classmethod
    def getVariableArgDeclarationCode(cls, variable_code_name):
        return "PyObject *%s" % variable_code_name

    @classmethod
    def getVariableArgReferencePassingCode(cls, variable_code_name):
        return "&%s" % variable_code_name

    @classmethod
    def getLocalVariableObjectAccessCode(cls, variable_code_name):
        """ Code to access value as object.

        """
        return variable_code_name

    @classmethod
    def getLocalVariableInitTestCode(cls, variable_code_name):
        return "%s != NULL" % variable_code_name

    @classmethod
    def getCellObjectAssignmentCode(cls, target_cell_code, variable_code_name, emit):
        emit(
            "%s = PyCell_NEW0( %s );" % (
                target_cell_code,
                variable_code_name
            )
        )

    @classmethod
    def getDeleteObjectCode(cls, variable_code_name, needs_check, tolerant,
                            variable, emit, context):
        if not needs_check:
            emit(
                template_del_local_known % {
                    "identifier" : variable_code_name
                }
            )
        elif tolerant:
            emit(
                template_del_local_tolerant % {
                    "identifier" : variable_code_name
                }
            )
        else:
            res_name = context.getBoolResName()

            emit(
                template_del_local_intolerant % {
                    "identifier" : variable_code_name,
                    "result" : res_name
                }
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
        return "%(to_name)s = ( %(condition)s ) ? Py_True : Py_False;" % {
            "to_name" : to_name,
            "condition" : condition
        }

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # Nothing to do for this type, pylint: disable=unused-argument
        return value_name

    @classmethod
    def emitVariableValueCheckCode(cls, variable, value_name, emit, context):
        if variable.isModuleVariable():
            getNameReferenceErrorCode(
                variable_name = variable.getName(),
                condition     = "%s == NULL" % value_name,
                emit          = emit,
                context       = context
            )
        else:
            getLocalVariableReferenceErrorCode(
                variable  = variable,
                condition = "%s == NULL" % value_name,
                emit      = emit,
                context   = context
            )

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit, context):
        # Not using the context, pylint: disable=unused-argument
        getCheckObjectCode(
            check_name = value_name,
            emit       = emit
        )

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        # Nothing done for this type yet, pylint: disable=unused-argument
        if value_name.c_type == cls.c_type:
            emit(
                "%s = %s;" % (
                    to_name,
                    value_name
                )
            )
        elif value_name.c_type == "nuitka_bool":
            emit(
                cls.getAssignmentCodeFromBoolCondition(
                    condition = value_name.getCType().getTruthCheckCode(value_name),
                    to_name   = to_name
                )
            )
        else:
            assert False, to_name.c_type


class CTypePyObjectPtrPtr(CPythonPyObjectPtrBase):
    c_type = "PyObject **"

    @classmethod
    def getVariableArgDeclarationCode(cls, variable_code_name):
        return "PyObject **%s" % variable_code_name

    @classmethod
    def getVariableArgReferencePassingCode(cls, variable_code_name):
        return variable_code_name

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # No code needed for this type, pylint: disable=unused-argument
        from ..VariableDeclarations import VariableDeclaration

        # Use the object pointed to.
        return VariableDeclaration(
            "PyObject *",
            "*%s" % value_name,
            None,
            None
        )

    @classmethod
    def getLocalVariableObjectAccessCode(cls, variable_code_name):
        return "*%s" % variable_code_name

    @classmethod
    def getLocalVariableInitTestCode(cls, variable_code_name):
        return "*%s != NULL" % variable_code_name

    @classmethod
    def getAssignmentCodeFromBoolCondition(cls, to_name, condition):
        return "*%(to_name)s = ( %(condition)s ) ? Py_True : Py_False;" % {
            "to_name" : to_name,
            "condition" : condition
        }


class CTypeCellObject(CTypeBase):
    c_type = "struct Nuitka_CellObject *"

    @classmethod
    def getInitValue(cls, init_from):
        # TODO: Single out "init_from" only user, so it becomes sure that we
        # get a reference transferred here in these cases.
        if init_from is not None:
            return "PyCell_NEW1( %s )" % init_from
        else:
            return "PyCell_EMPTY()"

    @classmethod
    def getCellObjectAssignmentCode(cls, target_cell_code, variable_code_name, emit):
        emit(
            "%s = %s;" % (
                target_cell_code,
                variable_code_name
            )
        )

        emit(
            "Py_INCREF( %s );" % (
                target_cell_code
            )
        )

    @classmethod
    def getLocalVariableAssignCode(cls, variable_code_name, needs_release,
                                   tmp_name, ref_count, in_place):
        if in_place:
            # Releasing is not an issue here, local variable reference never
            # gave a reference, and the in-place code deals with possible
            # replacement/release.
            template = template_write_shared_inplace

        else:
            if ref_count:
                if needs_release is False:
                    template = template_write_shared_clear_ref0
                else:
                    template = template_write_shared_unclear_ref0
            else:
                if needs_release is False:
                    template = template_write_shared_clear_ref1
                else:
                    template = template_write_shared_unclear_ref1

        return template % {
            "identifier" : variable_code_name,
            "tmp_name"   : tmp_name
        }

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # No code needed for this type, pylint: disable=unused-argument
        from ..VariableDeclarations import VariableDeclaration

        # Use the object pointed to.
        return VariableDeclaration(
            "PyObject *",
            "PyCell_GET( %s )" % value_name,
            None,
            None
        )

    @classmethod
    def getVariableArgDeclarationCode(cls, variable_code_name):
        return "struct Nuitka_CellObject *%s" % variable_code_name

    @classmethod
    def getVariableArgReferencePassingCode(cls, variable_code_name):
        return variable_code_name

    @classmethod
    def getLocalVariableObjectAccessCode(cls,variable_code_name):
        return "%s->ob_ref" % variable_code_name

    @classmethod
    def getLocalVariableInitTestCode(cls, variable_code_name):
        return "%s->ob_ref != NULL" % variable_code_name

    @classmethod
    def getAssignmentCodeFromBoolCondition(cls, to_name, condition):
        return "%(to_name)s->ob_ref = ( %(condition)s ) ? Py_True : Py_False;" % {
            "to_name" : to_name,
            "condition" : condition
        }

    @classmethod
    def getDeleteObjectCode(cls, variable_code_name, needs_check, tolerant,
                            variable, emit, context):
        if not needs_check:
            emit(
                template_del_shared_known % {
                    "identifier" : variable_code_name
                }
            )
        elif tolerant:
            emit(
                template_del_shared_tolerant % {
                    "identifier" : variable_code_name
                }
            )
        else:
            res_name = context.getBoolResName()

            emit(
                template_del_shared_intolerant % {
                    "identifier" : variable_code_name,
                    "result" : res_name
                }
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
    def getReleaseCode(cls, variable_code_name, needs_check, emit):
        if needs_check:
            template = template_release_unclear
        else:
            template = template_release_clear

        emit(
            template % {
                "identifier" : variable_code_name
            }
        )
