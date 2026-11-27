#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for Python 2 'print' statements."""

from .PythonAPICodes import generateCAPIErrorCode


def generatePrintValueCode(statement, emit, context):
    destination = statement.subnode_dest
    value = statement.subnode_value

    if destination is not None:
        capi = "PRINT_ITEM_TO"
        arg_desc = (("print_dest", destination), ("print_value", value))
    else:
        capi = "PRINT_ITEM"
        arg_desc = (("print_value", value),)

    generateCAPIErrorCode(
        capi=capi,
        tstate=False,
        arg_desc=arg_desc,
        may_raise=statement.mayRaiseExceptionOperation(),
        source_ref=statement.getSourceReference(),
        emit=emit,
        context=context,
    )


def generatePrintNewlineCode(statement, emit, context):
    destination = statement.subnode_dest

    if destination is not None:
        capi = "PRINT_NEW_LINE_TO"
        arg_desc = (("print_dest", destination),)
    else:
        capi = "PRINT_NEW_LINE"
        arg_desc = ()

    generateCAPIErrorCode(
        capi=capi,
        tstate=False,
        arg_desc=arg_desc,
        may_raise=statement.mayRaiseExceptionOperation(),
        source_ref=statement.getSourceReference(),
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
