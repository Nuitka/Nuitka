#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.code_generation.ErrorCodes import getReleaseCode

from .CTypeBases import CTypeBase, CTypeNotReferenceCountedMixin


class CTypeNuitkaBoolEnum(CTypeNotReferenceCountedMixin, CTypeBase):
    c_type = "nuitka_bool"

    helper_code = "NBOOL"

    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, inplace, emit, context
    ):
        assert not inplace

        if tmp_name.c_type == "nuitka_bool":
            emit("%s = %s;" % (value_name, tmp_name))
        else:
            if tmp_name.c_type == "PyObject *":
                test_code = "%s == Py_True" % tmp_name
            else:
                assert False, tmp_name

            cls.emitAssignmentCodeFromBoolCondition(
                to_name=value_name, condition=test_code, emit=emit
            )

            # TODO: Refcount and context needs release are redundant.
            if ref_count:
                getReleaseCode(tmp_name, emit, context)

    @classmethod
    def emitAssignmentCodeToNuitkaIntOrLong(
        cls, to_name, value_name, needs_check, emit, context
    ):
        assert False, to_name

    @classmethod
    def getTruthCheckCode(cls, value_name):
        return "%s == NUITKA_BOOL_TRUE" % value_name

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # Nothing to do for this type, pylint: disable=unused-argument
        return value_name

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit):
        emit("assert(%s != NUITKA_BOOL_UNASSIGNED);" % value_name)

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        if value_name.c_type == cls.c_type:
            emit("%s = %s;" % (to_name, value_name))
        else:
            value_name.getCType().emitAssignmentCodeToNuitkaBool(
                to_name=to_name,
                value_name=value_name,
                needs_check=needs_check,
                emit=emit,
                context=context,
            )

            getReleaseCode(value_name, emit, context)

    @classmethod
    def emitAssignmentCodeFromConstant(
        cls, to_name, constant, may_escape, emit, context
    ):
        # No context needed, pylint: disable=unused-argument
        emit(
            "%s = %s;"
            % (to_name, "NUITKA_BOOL_TRUE" if constant else "NUITKA_BOOL_FALSE")
        )

    @classmethod
    def getInitValue(cls, init_from):
        if init_from is None:
            return "NUITKA_BOOL_UNASSIGNED"
        else:
            assert False, init_from
            return init_from

    @classmethod
    def getInitTestConditionCode(cls, value_name, inverted):
        return "%s %s NUITKA_BOOL_UNASSIGNED" % (value_name, "==" if inverted else "!=")

    @classmethod
    def emitReinitCode(cls, value_name, emit):
        emit("%s = NUITKA_BOOL_UNASSIGNED;" % value_name)

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):
        if not needs_check:
            emit("%s = NUITKA_BOOL_UNASSIGNED;" % value_name)
        elif tolerant:
            emit("%s = NUITKA_BOOL_UNASSIGNED;" % value_name)
        else:
            emit("%s = %s != NUITKA_BOOL_UNASSIGNED;" % (to_name, value_name))
            emit("%s = NUITKA_BOOL_UNASSIGNED;" % value_name)

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        emit(
            "%(to_name)s = (%(condition)s) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;"
            % {"to_name": to_name, "condition": condition}
        )

    @classmethod
    def emitAssignInplaceNegatedValueCode(cls, to_name, needs_check, emit, context):
        # Half way, virtual method: pylint: disable=unused-argument
        cls.emitValueAssertionCode(to_name, emit=emit)
        emit("assert(%s != NUITKA_BOOL_EXCEPTION);" % to_name)

        cls.emitAssignmentCodeFromBoolCondition(
            to_name=to_name, condition="%s == NUITKA_BOOL_FALSE" % to_name, emit=emit
        )

    @classmethod
    def getExceptionCheckCondition(cls, value_name):
        return "%s == NUITKA_BOOL_EXCEPTION" % value_name

    @classmethod
    def hasErrorIndicator(cls):
        return True
