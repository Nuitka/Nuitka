#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Integer related codes, long and int."""

from nuitka.PythonVersions import python_version

from .CodeHelpers import decideConversionCheckNeeded
from .PythonAPICodes import generateCAPIObjectCode, makeArgDescFromExpression


def generateBuiltinLong1Code(to_name, expression, emit, context):
    assert python_version < 0x300

    # TODO: Have dedicated helper that inlines.
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PyNumber_Long",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinLong2Code(to_name, expression, emit, context):
    assert python_version < 0x300

    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_LONG2",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinInt1Code(to_name, expression, emit, context):
    # TODO: Have dedicated helper that inlines.
    generateCAPIObjectCode(
        to_name=to_name,
        capi="PyNumber_Int",
        tstate=False,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinInt2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="BUILTIN_INT2",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


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
