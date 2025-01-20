#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" CType enum class for void, a special value to represent discarding stuff.

Cannot be read from obviously. Also drops references immediately when trying
to assign to it, but allows to check for exception.
"""

from nuitka import Options
from nuitka.code_generation.ErrorCodes import getReleaseCode

from .CTypeBases import CTypeBase, CTypeNotReferenceCountedMixin

# This is going to not use arguments very commonly. For now disable
# the warning all around, specialize one done, pylint: disable=unused-argument


class CTypeNuitkaVoidEnum(CTypeNotReferenceCountedMixin, CTypeBase):
    c_type = "nuitka_void"

    # Return value only obviously.
    helper_code = "NVOID"

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # Nothing to do for this type, pylint: disable=unused-argument
        assert False

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit):
        emit("assert(%s == NUITKA_VOID_OK);" % value_name)

    @classmethod
    def emitReInitCode(cls, value_name, emit):
        emit("%s = NUITKA_VOID_OK;" % value_name)

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        # We have no storage, the original user will cleanup after itself. This
        # is the main point of the whole type.
        getReleaseCode(value_name, emit, context)

        # The only possible value, and in this case never read, but the compiler hates
        # it being defined which is hard for us to know ahead of time.
        if Options.is_debug:
            emit("%s = NUITKA_VOID_OK;" % to_name)

    @classmethod
    def emitAssignmentCodeFromConstant(
        cls, to_name, constant, may_escape, emit, context
    ):
        # Everything else expresses missed compiled time optimization.
        assert constant is None

        # The only possible value, and in this case never read, but the compiler hates
        # it being defined which is hard for us to know ahead of time.
        if Options.is_debug:
            emit("%s = NUITKA_VOID_OK;" % to_name)

    @classmethod
    def getInitValue(cls, init_from):
        assert False

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):
        assert False

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        # The only possible value, and in this case never read, but the compiler hates
        # it being defined which is hard for us to know ahead of time.
        if Options.is_debug:
            emit("%s = NUITKA_VOID_OK;" % to_name)

    @classmethod
    def emitAssignInplaceNegatedValueCode(cls, to_name, needs_check, emit, context):
        # The only possible value, and in this case never read, but the compiler hates
        # it being defined which is hard for us to know ahead of time.
        if Options.is_debug:
            emit("%s = NUITKA_VOID_OK;" % to_name)

    @classmethod
    def getExceptionCheckCondition(cls, value_name):
        return "%s == NUITKA_VOID_EXCEPTION" % value_name

    @classmethod
    def hasErrorIndicator(cls):
        return True


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
