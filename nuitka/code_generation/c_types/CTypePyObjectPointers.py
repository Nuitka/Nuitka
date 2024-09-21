#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" CType classes for PyObject *, PyObject **, and struct Nuitka_CellObject *

"""

from nuitka.__past__ import iterItems, xrange
from nuitka.code_generation.ErrorCodes import (
    getErrorExitBoolCode,
    getReleaseCode,
)
from nuitka.code_generation.templates.CodeTemplatesVariables import (
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
from nuitka.Constants import getConstantValueGuide, isMutable

from .CTypeBases import CTypeBase

# Need to run "bin/generate-specialized-c-code" when changing these values.
make_list_constant_direct_threshold = 4
make_list_constant_hinted_threshold = 13


class CPythonPyObjectPtrBase(CTypeBase):
    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, inplace, emit, context
    ):
        if inplace:
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

            if ref_count:
                context.removeCleanupTempName(tmp_name)

        emit(template % {"identifier": value_name, "tmp_name": tmp_name})

    @classmethod
    def emitAssignmentCodeToNuitkaIntOrLong(
        cls, to_name, value_name, needs_check, emit, context
    ):
        to_type = to_name.getCType()

        to_type.emitVariantAssignmentCode(
            to_name=to_name,
            ilong_value_name=value_name,
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
    def hasReleaseCode(cls):
        return True

    @classmethod
    def getReleaseCode(cls, value_name, needs_check, emit):
        if needs_check:
            template = template_release_object_unclear
        else:
            template = template_release_object_clear

        emit(template % {"identifier": value_name})

    @classmethod
    def emitAssignInplaceNegatedValueCode(cls, to_name, needs_check, emit, context):
        # Half way, virtual method: pylint: disable=unused-argument

        update_code = "%(to_name)s = (%(truth_check)s) ? Py_False : Py_True" % {
            "truth_check": cls.getTruthCheckCode(to_name),
            "to_name": to_name,
        }

        if context.needsCleanup(to_name):
            # The release here can only work for this class, needs more work to be able
            # to deal with CTypePyObjectPtrPtr and CTypeCellObject.

            assert cls is CTypePyObjectPtr

            emit(
                """\
{
    %(tmp_decl)s = %(to_name)s;
    %(update_code)s;
    Py_INCREF(%(to_name)s);
    Py_DECREF(old);
}
"""
                % {
                    "tmp_decl": cls.getVariableArgDeclarationCode("old"),
                    "update_code": update_code,
                    "to_name": to_name,
                }
            )
        else:
            emit("%s;" % update_code)

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
    def emitAssignmentCodeFromConstant(
        cls, to_name, constant, may_escape, emit, context
    ):
        # Many cases to deal with, pylint: disable=too-many-branches,too-many-statements

        if type(constant) is dict:
            if not may_escape:
                code = context.getConstantCode(constant)
                ref_count = 0
            elif constant:
                for key, value in iterItems(constant):
                    # key cannot be mutable.
                    assert not isMutable(key)
                    if isMutable(value):
                        needs_deep = True
                        break
                else:
                    needs_deep = False

                if needs_deep:
                    code = "DEEP_COPY_DICT(tstate, %s)" % context.getConstantCode(
                        constant, deep_check=False
                    )
                    ref_count = 1
                else:
                    code = "DICT_COPY(tstate, %s)" % context.getConstantCode(
                        constant, deep_check=False
                    )
                    ref_count = 1
            else:
                code = "MAKE_DICT_EMPTY(tstate)"
                ref_count = 1
        elif type(constant) is set:
            if not may_escape:
                code = context.getConstantCode(constant)
                ref_count = 0
            elif constant:
                code = "PySet_New(%s)" % context.getConstantCode(constant)
                ref_count = 1
            else:
                code = "PySet_New(NULL)"
                ref_count = 1
        elif type(constant) is list:
            if not may_escape:
                code = context.getConstantCode(constant)
                ref_count = 0
            elif constant:
                for value in constant:
                    if isMutable(value):
                        needs_deep = True
                        break
                else:
                    needs_deep = False

                if needs_deep:
                    code = 'DEEP_COPY_LIST_GUIDED(tstate, %s, "%s")' % (
                        context.getConstantCode(constant, deep_check=False),
                        getConstantValueGuide(constant, elements_only=True),
                    )
                    ref_count = 1
                else:
                    constant_size = len(constant)

                    if constant_size > 1 and all(
                        constant[i] is constant[0] for i in xrange(1, len(constant))
                    ):
                        code = "MAKE_LIST_REPEATED(tstate, %s, %s)" % (
                            constant_size,
                            context.getConstantCode(constant[0], deep_check=False),
                        )
                    elif constant_size < make_list_constant_direct_threshold:
                        code = "MAKE_LIST%d(tstate, %s)" % (
                            constant_size,
                            ",".join(
                                context.getConstantCode(constant[i], deep_check=False)
                                for i in xrange(constant_size)
                            ),
                        )
                    elif constant_size < make_list_constant_hinted_threshold:
                        code = "MAKE_LIST%d(tstate, %s)" % (
                            constant_size,
                            context.getConstantCode(constant, deep_check=False),
                        )
                    else:
                        code = "LIST_COPY(tstate, %s)" % context.getConstantCode(
                            constant, deep_check=False
                        )
                    ref_count = 1
            else:
                # TODO: For the zero elements list, maybe have a dedicated function, which
                # avoids a bit of tests, not sure we want LTO do this.
                code = "MAKE_LIST_EMPTY(tstate, 0)"
                ref_count = 1
        elif type(constant) is tuple:
            needs_deep = False

            if may_escape:
                for value in constant:
                    if isMutable(value):
                        needs_deep = True
                        break
            if needs_deep:
                code = 'DEEP_COPY_TUPLE_GUIDED(tstate, %s, "%s")' % (
                    context.getConstantCode(constant, deep_check=False),
                    getConstantValueGuide(constant, elements_only=True),
                )
                ref_count = 1
            else:
                code = context.getConstantCode(constant)
                ref_count = 0
        elif type(constant) is bytearray:
            if may_escape:
                code = "BYTEARRAY_COPY(tstate, %s)" % context.getConstantCode(constant)
                ref_count = 1
            else:
                code = context.getConstantCode(constant)
                ref_count = 0
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
    def emitReInitCode(cls, value_name, emit):
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
        if value_name.c_type == cls.c_type:
            emit("%s = %s;" % (to_name, value_name))

            context.transferCleanupTempName(value_name, to_name)
        elif value_name.c_type in ("nuitka_bool", "bool"):
            cls.emitAssignmentCodeFromBoolCondition(
                condition=value_name.getCType().getTruthCheckCode(value_name),
                to_name=to_name,
                emit=emit,
            )
        elif value_name.c_type == "nuitka_ilong":
            emit("ENFORCE_NILONG_OBJECT_VALUE(&%s);" % value_name)

            emit("%s = %s.python_value;" % (to_name, value_name))

            context.transferCleanupTempName(value_name, to_name)
        else:
            assert False, to_name.c_type

    @classmethod
    def getExceptionCheckCondition(cls, value_name):
        return "%s == NULL" % value_name

    @classmethod
    def hasErrorIndicator(cls):
        return True

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
            return "Nuitka_Cell_NewEmpty()"

    @classmethod
    def getInitTestConditionCode(cls, value_name, inverted):
        return "%s->ob_ref %s NULL" % (value_name, "==" if inverted else "!=")

    @classmethod
    def getCellObjectAssignmentCode(cls, target_cell_code, variable_code_name, emit):
        emit("%s = %s;" % (target_cell_code, variable_code_name))

        emit("Py_INCREF(%s);" % (target_cell_code))

    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, inplace, emit, context
    ):
        if inplace:
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

                if ref_count:
                    context.removeCleanupTempName(tmp_name)
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
    def emitReInitCode(cls, value_name, emit):
        emit("%s = NULL;" % value_name)

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit):
        emit("CHECK_OBJECT(%s->ob_ref);" % value_name)

    @classmethod
    def emitReleaseAssertionCode(cls, value_name, emit):
        emit("CHECK_OBJECT(%s);" % value_name)


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
