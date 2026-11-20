#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""CType classes for 'nuitka_ilong', a struct to represent long values."""

from nuitka.code_generation.templates.CodeTemplatesVariables import (
    template_release_object_clear,
    template_release_object_unclear,
)

from ..ErrorCodes import getTakeReferenceCode
from .CTypeBases import CTypeBase


class CTypeNuitkaIntOrLongStruct(CTypeBase):
    c_type = "nuitka_ilong"

    helper_code = "NILONG"

    @classmethod
    def holdsObjectReference(cls):
        # Optionally holds a PyObject * for the integer value.
        return True

    @classmethod
    def isDualType(cls):
        return True

    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, inplace, emit, context
    ):
        if not inplace:
            if not ref_count:
                getTakeReferenceCode(tmp_name, emit)

            if needs_release is not False:
                emit("RELEASE_NILONG_VALUE(&%s);" % value_name)

        if tmp_name.c_type == "nuitka_ilong":
            emit("%s = %s;" % (value_name, tmp_name))
        else:
            if tmp_name.c_type == "PyObject *":
                emit("SET_NILONG_OBJECT_VALUE(&%s, %s);" % (value_name, tmp_name))
            else:
                assert False, repr(tmp_name)

        if not inplace and ref_count:
            context.removeCleanupTempName(tmp_name)

    @classmethod
    def emitVariantAssignmentCode(
        cls, to_name, ilong_value_name, int_value, emit, context
    ):
        if ilong_value_name is None:
            assert int_value is not None
            emit("SET_NILONG_C_VALUE(&%s, %s);" % (to_name, int_value))
        else:
            if int_value is None:
                emit("SET_NILONG_OBJECT_VALUE(&%s, %s);" % (to_name, ilong_value_name))
            else:
                emit(
                    "SET_NILONG_OBJECT_AND_C_VALUE(&%s, %s, %s );"
                    % (to_name, ilong_value_name, int_value)
                )

            context.transferCleanupTempName(ilong_value_name, to_name)

    @classmethod
    def getTruthCheckCode(cls, value_name):
        return "IS_NILONG_TRUE(&%s)" % value_name

    @classmethod
    def emitAssignmentCodeToNuitkaBool(
        cls, to_name, value_name, needs_check, emit, context
    ):
        # Truth checks on exact integers cannot fail, pylint: disable=unused-argument
        to_name.getCType().emitAssignmentCodeFromBoolCondition(
            to_name=to_name,
            condition=cls.getTruthCheckCode(value_name),
            emit=emit,
        )

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # pylint: disable=unused-argument
        return value_name

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit):
        emit("assert(%s.validity != NUITKA_ILONG_UNASSIGNED);" % value_name)

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        if value_name.c_type == cls.c_type:
            emit("%s = %s;" % (to_name, value_name))

            context.transferCleanupTempName(value_name, to_name)
        else:
            value_name.getCType().emitAssignmentCodeToNuitkaIntOrLong(
                to_name=to_name,
                value_name=value_name,
                needs_check=needs_check,
                emit=emit,
                context=context,
            )

    @classmethod
    def getInitValue(cls, init_from):
        if init_from is None:
            # TODO: In debug mode, use more crash prone maybe.
            return "NUITKA_ILONG_UNASSIGNED_VALUE"
        else:
            assert False, init_from
            return init_from

    @classmethod
    def getInitTestConditionCode(cls, value_name, inverted):
        return "%s.validity %s NUITKA_ILONG_UNASSIGNED" % (
            value_name,
            "==" if inverted else "!=",
        )

    @classmethod
    def hasReleaseCode(cls):
        return True

    @classmethod
    def getReleaseCode(cls, value_name, needs_check, emit):
        emit(
            "if ((%s.validity & NUITKA_ILONG_OBJECT_VALID) == NUITKA_ILONG_OBJECT_VALID) {"
            % value_name
        )

        # TODO: Have a derived C type that does it.

        if needs_check:
            template = template_release_object_unclear
        else:
            template = template_release_object_clear

        emit(template % {"identifier": "%s.python_value" % value_name})

        emit("}")

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):
        if not needs_check:
            emit("RELEASE_NILONG_VALUE(&%s);" % value_name)
        elif tolerant:
            emit("RELEASE_NILONG_VALUE(&%s);" % value_name)
        else:
            emit("%s = %s.validity != NUITKA_ILONG_UNASSIGNED;" % (to_name, value_name))
            emit("RELEASE_NILONG_VALUE(&%s);" % value_name)

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        emit(
            "SET_NILONG_C_VALUE(&%(to_name)s, (%(condition)s) ? 1 : 0);"
            % {"to_name": to_name, "condition": condition}
        )

    @classmethod
    def emitAssignmentCodeFromConstant(
        cls, to_name, constant, may_escape, emit, context
    ):
        # Immutable integer constants can be shared even if they escape.
        # pylint: disable=unused-argument

        assert type(constant) is int, repr(constant)

        cls.emitVariantAssignmentCode(
            to_name=to_name,
            ilong_value_name=context.getConstantCode(constant=constant),
            int_value=constant,
            emit=emit,
            context=context,
        )

    @classmethod
    def getTakeReferenceCode(cls, value_name, emit):
        emit("INCREF_NILONG_VALUE(&%s);" % value_name)

    @classmethod
    def emitReInitCode(cls, value_name, emit):
        emit("%s.validity = NUITKA_ILONG_UNASSIGNED;" % value_name)

    @classmethod
    def hasErrorIndicator(cls):
        return True

    @classmethod
    def getExceptionCheckCondition(cls, value_name):
        return "%s.validity == NUITKA_ILONG_EXCEPTION" % value_name


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
