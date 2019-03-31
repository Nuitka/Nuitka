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
""" CType classes for void, a special value to represent discarding stuff.

Cannot be read from obviously. Also drops references immediately when trying
to assign to it.

"""

from .CTypeBases import CTypeBase

# This is going to not use arguments very commonly. For now disable
# the warning all around, specialize one done, pylint: disable=unused-argument


class CTypeVoid(CTypeBase):
    c_type = "void"

    @classmethod
    def emitTruthCheckCode(cls, to_name, value_name, needs_check, emit, context):
        assert False

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # Nothing to do for this type, pylint: disable=unused-argument
        assert False

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit, context):
        assert False

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        # We have no storage, the original user will cleanup after itself. This
        # is the main point of the whole type.
        from ..ErrorCodes import getReleaseCode

        getReleaseCode(value_name, emit, context)

    @classmethod
    def getInitValue(cls, init_from):
        assert False

    @classmethod
    def getReleaseCode(cls, variable_code_name, needs_check, emit):
        assert False

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):
        assert False

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        # We have no storage, the original user will cleanup after itself. This
        # is the main point of the whole type.
        pass
