#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for match statement helpers."""

from .CodeHelpers import decideConversionCheckNeeded
from .PythonAPICodes import (
    CArg,
    generateCAPIObjectCode,
    makeArgDescFromExpression,
)


def generateMatchArgsCode(to_name, expression, emit, context):
    # TODO: Prefer "PyObject **" of course once we have that.
    keywords = expression.getKeywordArgs()

    if keywords:
        keywords_name = "&PyTuple_GET_ITEM(%s, 0)" % context.getConstantCode(
            constant=keywords
        )
    else:
        keywords_name = "NULL"

    generateCAPIObjectCode(
        to_name=to_name,
        capi="MATCH_CLASS_ARGS",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression)
        + (
            CArg(expression.getPositionalArgsCount()),
            CArg(keywords_name),
            CArg(len(keywords)),
        ),
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
