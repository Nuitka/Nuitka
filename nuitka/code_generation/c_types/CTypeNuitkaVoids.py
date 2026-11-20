#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""CType enum class for void, a special value to represent discarding stuff.

Cannot be read from obviously. Also drops references immediately when trying
to assign to it, but allows to check for exception.
"""

from nuitka.code_generation.ErrorCodes import getReleaseCode
from nuitka.States import states

from .CTypeBases import CTypeBase, CTypeNotReferenceCountedMixin

# pylint: disable=unused-argument


class CTypeNuitkaVoidEnum(CTypeNotReferenceCountedMixin, CTypeBase):
    c_type = "nuitka_void"

    helper_code = "NVOID"

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        assert False

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit):
        emit("assert(%s == NUITKA_VOID_OK);" % value_name)

    @classmethod
    def emitReInitCode(cls, value_name, emit):
        emit("%s = NUITKA_VOID_OK;" % value_name)

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        # Discard the value immediately since 'nuitka_void' has no value storage.
        getReleaseCode(value_name, emit, context)

        # Debug mode assertions check 'NUITKA_VOID_OK', while non-debug avoids
        # unused-assignment warnings on an unread variable.
        if states.is_debug:
            emit("%s = NUITKA_VOID_OK;" % to_name)

    @classmethod
    def emitAssignmentCodeFromConstant(
        cls, to_name, constant, may_escape, emit, context
    ):
        assert constant is None

        if states.is_debug:
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
        if states.is_debug:
            emit("%s = NUITKA_VOID_OK;" % to_name)

    @classmethod
    def emitAssignInplaceNegatedValueCode(cls, to_name, needs_check, emit, context):
        if states.is_debug:
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
