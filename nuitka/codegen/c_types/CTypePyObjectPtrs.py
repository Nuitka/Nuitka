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
""" CType classes for PyObject *, PyObject **, and struct Nuitka_CellObject *

"""

from nuitka.__past__ import iterItems
from nuitka.codegen.ErrorCodes import getErrorExitBoolCode, getReleaseCode
from nuitka.codegen.templates.CodeTemplatesVariables import (
    template_del_local_intolerant,
    template_del_local_known,
    template_del_local_tolerant,
    template_del_shared_intolerant,
    template_del_shared_known,
    template_del_shared_tolerant,
    template_release_object_clear,
    template_release_object_unclear,
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
    template_write_shared_unclear_ref1,
)
from nuitka.Constants import isMutable

from .CTypeBases import CTypeBase


class CPythonPyObjectPtrBase(CTypeBase):
    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, in_place, emit, context
    ):
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

        emit(template % {"identifier": value_name, "tmp_name": tmp_name})

    @classmethod
    def emitAssignmentCodeToNuitkaIntOrLong(
        cls, to_name, value_name, needs_check, emit, context
    ):
        to_type = to_name.getCType()

        to_type.emitVariantAssignmentCode(
            int_name=to_name,
            value_name=value_name,
            int_value=None,
            emit=emit,
            context=context,
        )

    @classmethod
    def getTruthCheckCode(cls, value_name):
        return "CHECK_IF_TRUE(%s) == 1" % value_name

    @classmethod
    def emitTruthCheckCode(cls, to_name, value_name, emit):
        assert to_name.c_type == "int", to_name

        emit("%s = CHECK_IF_TRUE(%s);" % (to_name, value_name))

    @classmethod
    def getReleaseCode(cls, value_name, needs_check, emit):
        if needs_check:
            template = template_release_object_unclear
        else:
            template = template_release_object_clear

        emit(template % {"identifier": value_name})

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        emit(
            "%(to_name)s = (%(condition)s) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;"
            % {"to_name": to_name, "condition": condition}
        )

    @classmethod
    def emitAssignmentCodeToNuitkaBool(
        cls, to_name, value_name, needs_check, emit, context
    ):
        truth_name = context.allocateTempName("truth_name", "int")

        emit("%s = CHECK_IF_TRUE(%s);" % (truth_name, value_name))

        getErrorExitBoolCode(
            condition="%s == -1" % truth_name,
            needs_check=needs_check,
            emit=emit,
            context=context,
        )

        emit(
            "%s = %s == 0 ? NUITKA_BOOL_FALSE : NUITKA_BOOL_TRUE;"
            % (to_name, truth_name)
        )

    @classmethod
    def emitAssignmentCodeFromConstant(cls, to_name, constant, emit, context):
        # Many cases to deal with, pylint: disable=too-many-branches,too-many-statements

        if type(constant) is dict:
            if constant:
                for key, value in iterItems(constant):
                    # key cannot be mutable.
                    assert not isMutable(key)
                    if isMutable(value):
                        needs_deep = True
                        break
                else:
                    needs_deep = False

                if needs_deep:
                    code = "DEEP_COPY(%s)" % context.getConstantCode(constant)
                else:
                    code = "PyDict_Copy(%s)" % context.getConstantCode(constant)
            else:
                code = "PyDict_New()"

            ref_count = 1
        elif type(constant) is set:
            if constant:
                code = "PySet_New(%s)" % context.getConstantCode(constant)
            else:
                code = "PySet_New(NULL)"

            ref_count = 1
        elif type(constant) is list:
            if constant:
                for value in constant:
                    if isMutable(value):
                        needs_deep = True
                        break
                else:
                    needs_deep = False

                if needs_deep:
                    code = "DEEP_COPY(%s)" % context.getConstantCode(constant)
                else:
                    code = "LIST_COPY(%s)" % context.getConstantCode(constant)
            else:
                code = "PyList_New(0)"

            ref_count = 1
        elif type(constant) is tuple:
            for value in constant:
                if isMutable(value):
                    needs_deep = True
                    break
            else:
                needs_deep = False

            if needs_deep:
                code = "DEEP_COPY(%s)" % context.getConstantCode(constant)

                ref_count = 1
            else:
                code = context.getConstantCode(constant)

                ref_count = 0
        elif type(constant) is bytearray:
            code = "BYTEARRAY_COPY(%s)" % context.getConstantCode(constant)
            ref_count = 1
        else:
            code = context.getConstantCode(constant=constant)

            ref_count = 0

        if to_name.c_type == "PyObject *":
            value_name = to_name
        else:
            value_name = context.allocateTempName("constant_value")

        emit("%s = %s;" % (value_name, code))

        if to_name is not value_name:
            cls.emitAssignConversionCode(
                to_name=to_name,
                value_name=value_name,
                needs_check=False,
                emit=emit,
                context=context,
            )

            # Above is supposed to transfer ownership.
            if ref_count:
                getReleaseCode(value_name, emit, context)
        else:
            if ref_count:
                context.addCleanupTempName(value_name)


class CTypePyObjectPtr(CPythonPyObjectPtrBase):
    c_type = "PyObject *"

    helper_code = "OBJECT"

    @classmethod
    def getInitValue(cls, init_from):
        if init_from is None:
            return "NULL"
        else:
            return init_from

    @classmethod
    def getInitTestConditionCode(cls, value_name, inverted):
        return "%s %s NULL" % (value_name, "==" if inverted else "!=")

    @classmethod
    def emitReinitCode(cls, value_name, emit):
        emit("%s = NULL;" % value_name)

    @classmethod
    def getVariableArgDeclarationCode(cls, variable_code_name):
        return "PyObject *%s" % variable_code_name

    @classmethod
    def getVariableArgReferencePassingCode(cls, variable_code_name):
        return "&%s" % variable_code_name

    @classmethod
    def getCellObjectAssignmentCode(cls, target_cell_code, variable_code_name, emit):
        emit("%s = Nuitka_Cell_New0(%s);" % (target_cell_code, variable_code_name))

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):
        if not needs_check:
            emit(template_del_local_known % {"identifier": value_name})
        elif tolerant:
            emit(template_del_local_tolerant % {"identifier": value_name})
        else:
            emit(
                template_del_local_intolerant
                % {"identifier": value_name, "result": to_name}
            )

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        emit(
            "%(to_name)s = (%(condition)s) ? Py_True : Py_False;"
            % {"to_name": to_name, "condition": condition}
        )

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # Nothing to do for this type, pylint: disable=unused-argument
        return value_name

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit):
        emit("CHECK_OBJECT(%s);" % value_name)

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        # Nothing done for this type yet, pylint: disable=unused-argument
        if value_name.c_type == cls.c_type:
            emit("%s = %s;" % (to_name, value_name))
        elif value_name.c_type == "nuitka_bool":
            cls.emitAssignmentCodeFromBoolCondition(
                condition=value_name.getCType().getTruthCheckCode(value_name),
                to_name=to_name,
                emit=emit,
            )
        elif value_name.c_type == "nuitka_ilong":
            emit("ENFORCE_ILONG_OBJECT_VALUE(&%s);" % value_name)

            emit("%s = %s.ilong_object;" % (to_name, value_name))
        else:
            assert False, to_name.c_type

    @classmethod
    def getExceptionCheckCondition(cls, value_name):
        return "%s == NULL" % value_name

    @classmethod
    def getReleaseCode(cls, value_name, needs_check, emit):
        if needs_check:
            template = template_release_object_unclear
        else:
            template = template_release_object_clear

        emit(template % {"identifier": value_name})

    @classmethod
    def getTakeReferenceCode(cls, value_name, emit):
        """Take reference code for given object."""

        emit("Py_INCREF(%s);" % value_name)


class CTypePyObjectPtrPtr(CPythonPyObjectPtrBase):
    c_type = "PyObject **"

    @classmethod
    def getInitTestConditionCode(cls, value_name, inverted):
        return "*%s %s NULL" % (value_name, "==" if inverted else "!=")

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
        return VariableDeclaration("PyObject *", "*%s" % value_name, None, None)

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        emit(
            "*%(to_name)s = (%(condition)s) ? Py_True : Py_False;"
            % {"to_name": to_name, "condition": condition}
        )


class CTypeCellObject(CTypeBase):
    c_type = "struct Nuitka_CellObject *"

    @classmethod
    def getInitValue(cls, init_from):
        # TODO: Single out "init_from" only user, so it becomes sure that we
        # get a reference transferred here in these cases.
        if init_from is not None:
            return "Nuitka_Cell_New1(%s)" % init_from
        else:
            return "Nuitka_Cell_Empty()"

    @classmethod
    def getInitTestConditionCode(cls, value_name, inverted):
        return "%s->ob_ref %s NULL" % (value_name, "==" if inverted else "!=")

    @classmethod
    def getCellObjectAssignmentCode(cls, target_cell_code, variable_code_name, emit):
        emit("%s = %s;" % (target_cell_code, variable_code_name))

        emit("Py_INCREF(%s);" % (target_cell_code))

    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, in_place, emit, context
    ):
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

        emit(template % {"identifier": value_name, "tmp_name": tmp_name})

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # No code needed for this type, pylint: disable=unused-argument
        from ..VariableDeclarations import VariableDeclaration

        # Use the object pointed to.
        return VariableDeclaration(
            "PyObject *", "Nuitka_Cell_GET(%s)" % value_name, None, None
        )

    @classmethod
    def getVariableArgDeclarationCode(cls, variable_code_name):
        return "struct Nuitka_CellObject *%s" % variable_code_name

    @classmethod
    def getVariableArgReferencePassingCode(cls, variable_code_name):
        return variable_code_name

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        emit(
            "%(to_name)s->ob_ref = (%(condition)s) ? Py_True : Py_False;"
            % {"to_name": to_name, "condition": condition}
        )

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):
        if not needs_check:
            emit(template_del_shared_known % {"identifier": value_name})
        elif tolerant:
            emit(template_del_shared_tolerant % {"identifier": value_name})
        else:
            emit(
                template_del_shared_intolerant
                % {"identifier": value_name, "result": to_name}
            )

    @classmethod
    def getReleaseCode(cls, value_name, needs_check, emit):
        if needs_check:
            template = template_release_object_unclear
        else:
            template = template_release_object_clear

        emit(template % {"identifier": value_name})

    @classmethod
    def emitReinitCode(cls, value_name, emit):
        emit("%s = NULL;" % value_name)

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit):
        emit("CHECK_OBJECT(%s->ob_ref);" % value_name)

    @classmethod
    def emitReleaseAssertionCode(cls, value_name, emit):
        emit("CHECK_OBJECT(%s);" % value_name)
