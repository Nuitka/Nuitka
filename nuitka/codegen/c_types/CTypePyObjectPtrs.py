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
    getLocalVariableReferenceErrorCode
)
from nuitka.codegen.templates.CodeTemplatesVariables import (
    template_del_local_intolerant,
    template_del_local_known,
    template_del_local_tolerant,
    template_del_shared_intolerant,
    template_del_shared_known,
    template_del_shared_tolerant,
    template_read_local,
    template_read_shared_unclear,
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
    def getVariableObjectAccessCode(cls, to_name, needs_check, variable_code_name,
                                    variable, emit, context):
        template = template_read_local

        emit(
            template % {
                "tmp_name"   : to_name,
                "identifier" : cls.getLocalVariableObjectAccessCode(variable_code_name)
            }
        )

        if needs_check:
            getLocalVariableReferenceErrorCode(
                variable  = variable,
                condition = "%s == NULL" % to_name,
                emit      = emit,
                context   = context
            )
        else:
            getCheckObjectCode(
                check_name = to_name,
                emit       = emit
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
        return '&' + variable_code_name

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


class CTypePyObjectPtrPtr(CPythonPyObjectPtrBase):
    c_type = "PyObject **"

    @classmethod
    def getVariableArgDeclarationCode(cls, variable_code_name):
        return "PyObject **%s" % variable_code_name

    @classmethod
    def getVariableArgReferencePassingCode(cls, variable_code_name):
        return variable_code_name

    @classmethod
    def getLocalVariableObjectAccessCode(cls, variable_code_name):
        return '*' + variable_code_name

    @classmethod
    def getLocalVariableInitTestCode(cls, variable_code_name):
        return "*%s != NULL" % variable_code_name


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
    def getVariableObjectAccessCode(cls, to_name, needs_check, variable_code_name,
                                    variable, emit, context):
        template = template_read_shared_unclear

        emit(
            template % {
                "tmp_name"   : to_name,
                "identifier" : variable_code_name
            }
        )

        if needs_check:
            getLocalVariableReferenceErrorCode(
                variable  = variable,
                condition = "%s == NULL" % to_name,
                emit      = emit,
                context   = context
            )
        else:
            getCheckObjectCode(
                check_name = to_name,
                emit       = emit
            )

    @classmethod
    def getVariableArgDeclarationCode(cls, variable_code_name):
        return "struct Nuitka_CellObject *%s" % variable_code_name

    @classmethod
    def getVariableArgReferencePassingCode(cls, variable_code_name):
        return variable_code_name

    @classmethod
    def getLocalVariableObjectAccessCode(cls,variable_code_name):
        return variable_code_name + "->ob_ref"

    @classmethod
    def getLocalVariableInitTestCode(cls, variable_code_name):
        return "%s->ob_ref != NULL" % variable_code_name

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
