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
""" CType classes for nuitka_ilong, an struct to represent long values.

"""


from nuitka.codegen.templates.CodeTemplatesVariables import (
    template_release_object_clear,
    template_release_object_unclear,
)

from .CTypeBases import CTypeBase


class CTypeNuitkaIntOrLongStruct(CTypeBase):
    c_type = "nuitka_ilong"

    helper_code = "NILONG"

    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, in_place, emit, context
    ):
        assert not in_place

        if tmp_name.c_type == "nuitka_ilong":
            emit("%s = %s;" % (value_name, tmp_name))

            if ref_count:
                emit("/* REFCOUNT ? */")

        else:
            if tmp_name.c_type == "PyObject *":
                emit("%s.validity = NUITKA_ILONG_OBJECT_VALID;" % value_name)
                emit("%s.ilong_object = %s;" % (value_name, tmp_name))

                if ref_count:
                    emit("/* REFCOUNT ? */")
            else:
                assert False, repr(tmp_name)

    @classmethod
    def emitVariantAssignmentCode(cls, int_name, value_name, int_value, emit, context):
        # needs no context, pylint: disable=unused-argument
        if value_name is None:
            assert int_value is not None
            assert False  # TODO
        else:
            if int_value is None:
                emit("%s.validity = NUITKA_ILONG_OBJECT_VALID;" % int_name)
                emit("%s.ilong_object = %s;" % (int_name, value_name))
            else:
                emit("%s.validity = NUITKA_ILONG_BOTH_VALID;" % int_name)
                emit("%s.ilong_object = %s;" % (int_name, value_name))
                emit("%s.ilong_value = %s;" % (int_name, int_value))

    @classmethod
    def getTruthCheckCode(cls, value_name):
        return "%s != 0" % value_name

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # Nothing to do for this type, pylint: disable=unused-argument
        return value_name

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit):
        emit("assert(%s.validity != NUITKA_ILONG_UNASSIGNED);" % value_name)

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        if value_name.c_type == cls.c_type:
            emit("%s = %s;" % (to_name, value_name))
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
            return "{NUITKA_ILONG_UNASSIGNED, NULL, 0}"
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
    def getReleaseCode(cls, value_name, needs_check, emit):
        emit(
            "if ((%s.validity & NUITKA_ILONG_OBJECT_VALID) == NUITKA_ILONG_OBJECT_VALID) {"
            % value_name
        )

        # TODO: Have a slave C type that does it.

        if needs_check:
            template = template_release_object_unclear
        else:
            template = template_release_object_clear

        emit(template % {"identifier": "%s.ilong_object" % value_name})

        emit("}")

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):
        assert False, "TODO"

        if not needs_check:
            emit("%s = NUITKA_BOOL_UNASSIGNED;" % value_name)
        elif tolerant:
            emit("%s = NUITKA_BOOL_UNASSIGNED;" % value_name)
        else:
            emit("%s = %s == NUITKA_BOOL_UNASSIGNED;" % (to_name, value_name))
            emit("%s = NUITKA_BOOL_UNASSIGNED;" % value_name)

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        assert False, "TODO"

        emit(
            "%(to_name)s = (%(condition)s) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;"
            % {"to_name": to_name, "condition": condition}
        )
