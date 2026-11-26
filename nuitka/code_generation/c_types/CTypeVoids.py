#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""CType classes for C void, this cannot represent unassigned, nor indicate exception."""

from nuitka.code_generation.ErrorCodes import getReleaseCode

from .CTypeBases import CTypeBase, CTypeNotReferenceCountedMixin


class CTypeVoid(CTypeNotReferenceCountedMixin, CTypeBase):
    c_type = "bool"

    helper_code = "CVOID"

    @classmethod
    def emitValueAccessCode(cls, value_name, emit, context):
        # pylint: disable=unused-argument
        assert False

    @classmethod
    def emitValueAssertionCode(cls, value_name, emit):
        pass

    @classmethod
    def emitAssignConversionCode(cls, to_name, value_name, needs_check, emit, context):
        getReleaseCode(value_name, emit, context)

    @classmethod
    def emitAssignInplaceNegatedValueCode(cls, to_name, needs_check, emit, context):
        pass

    @classmethod
    def emitAssignmentCodeFromConstant(
        cls, to_name, constant, may_escape, emit, context
    ):
        # pylint: disable=unused-argument
        assert False

    @classmethod
    def getInitValue(cls, init_from):
        return "<not_possible>"

    @classmethod
    def getInitTestConditionCode(cls, value_name, inverted):
        return "<not_possible>"

    @classmethod
    def getDeleteObjectCode(
        cls, to_name, value_name, needs_check, tolerant, emit, context
    ):
        assert False

    @classmethod
    def emitAssignmentCodeFromBoolCondition(cls, to_name, condition, emit):
        assert False

    @classmethod
    def getExceptionCheckCondition(cls, value_name):
        # pylint: disable=unused-argument
        assert False

    @classmethod
    def hasErrorIndicator(cls):
        return False

    @classmethod
    def getTruthCheckCode(cls, value_name):
        # pylint: disable=unused-argument
        assert False


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
