#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
    template_release_clear,
    template_release_unclear,
)

from .CTypeBases import CTypeBase


class CTypeNuitkaIntOrLongStruct(CTypeBase):
    c_type = "nuitka_ilong"

    @classmethod
    def emitVariableAssignCode(
        cls, value_name, needs_release, tmp_name, ref_count, in_place, emit, context
    ):
        assert not in_place

        if tmp_name.c_type == "nuitka_bool":
            assert False

            emit("%s = %s;" % (value_name, tmp_name))
        else:
            if tmp_name.c_type == "PyObject *":
                emit("%s.validity = NUITKA_ILONG_OBJECT_VALID;" % value_name)

                emit("%s.ilong_object = %s;" % (value_name, tmp_name))

                if ref_count:
                    emit("/* REFCOUNT ? */")
            else:
                assert False, tmp_name

    @classmethod
    def getLocalVariableInitTestCode(cls, value_name, inverted):
        assert False, "TODO"

        return "%s %s NUITKA_BOOL_UNASSIGNED" % (value_name, "==" if inverted else "!=")

    @classmethod
    def getTruthCheckCode(cls, value_name):
        assert False, "TODO"

        return "%s == NUITKA_BOOL_TRUE" % value_name

    @classmethod
    def emitTruthCheckCode(cls, to_name, value_name, needs_check, emit, context):
        # pylint: disable=unused-argument
        assert False, "TODO"

        emit("%s = %s ? 1 : 0;" % (to_name, cls.getTruthCheckCode(value_name)))

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # Nothing to do for this type, pylint: disable=unused-argument
        return value_name

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit, context):
        # Not using the context, pylint: disable=unused-argument
        emit("assert(%s.validity != NUITKA_ILONG_UNASSIGNED);" % value_name)

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        assert False, "TODO"

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

    @classmethod
    def getInitValue(cls, init_from):
        if init_from is None:
            # TODO: In debug mode, use more crash prone maybe.
            return "{NUITKA_ILONG_UNASSIGNED, NULL, 0}"
        else:
            assert False, init_from
            return init_from

    @classmethod
    def getReleaseCode(cls, variable_code_name, needs_check, emit):
        emit(
            "if ((%s.validity & NUITKA_ILONG_OBJECT_VALID) == NUITKA_ILONG_OBJECT_VALID) {"
            % variable_code_name
        )

        if needs_check:
            template = template_release_unclear
        else:
            template = template_release_clear

        emit(template % {"identifier": "%s.ilong_object" % variable_code_name})

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
            "%(to_name)s = ( %(condition)s ) ? NUITKA_BOOL_TRUE : NUITKA_BOOL_FALSE;"
            % {"to_name": to_name, "condition": condition}
        )
