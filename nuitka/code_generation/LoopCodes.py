#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Loop codes.

Code generation for loops, breaking them, or continuing them. In Nuitka, there
are no for-loops or while-loops at this point. They have been re-formulated in
a simpler loop without a condition, and statements there-in that break under
certain conditions.

See Developer Manual for how the CPython loops are mapped to these nodes.
"""

from .CodeHelpers import generateStatementSequenceCode
from .ErrorCodes import getErrorExitBoolCode
from .ExceptionCodes import getExceptionUnpublishedReleaseCode
from .LabelCodes import getGotoCode, getLabelCode


def generateLoopBreakCode(statement, emit, context):
    # Functions used for generation all accept statement, but this one does
    # not use it. pylint: disable=unused-argument

    getExceptionUnpublishedReleaseCode(emit, context)

    releasePendingReturnValueCode(emit, context)

    break_target = context.getLoopBreakTarget()
    getGotoCode(break_target, emit)


def generateLoopContinueCode(statement, emit, context):
    # Functions used for generation all accept statement, but this one does
    # not use it. pylint: disable=unused-argument

    getExceptionUnpublishedReleaseCode(emit, context)

    releasePendingReturnValueCode(emit, context)

    continue_target = context.getLoopContinueTarget()
    getGotoCode(continue_target, emit)


def releasePendingReturnValueCode(emit, context):
    # A "break" or "continue" inside a "finally" block can abandon a "return"
    # that is being handled, and then the return value must be released, as it
    # is only passed to the caller when the "return" completes. The return
    # release mode tells us that we are inside such a return handler.
    if context.getReturnReleaseMode() and context.hasTempName("return_value"):
        return_value_name = context.getReturnValueName()

        # TODO: Can we not have Py_XCLEAR or something like that.
        emit("Py_XDECREF(%s);" % return_value_name)
        emit("%s = NULL;" % return_value_name)


def generateLoopCode(statement, emit, context):
    loop_start_label = context.allocateLabel("loop_start")

    if not statement.isStatementAborting():
        loop_end_label = context.allocateLabel("loop_end")
    else:
        loop_end_label = None

    getLabelCode(loop_start_label, emit)

    old_loop_break = context.setLoopBreakTarget(loop_end_label)
    old_loop_continue = context.setLoopContinueTarget(loop_start_label)

    generateStatementSequenceCode(
        statement_sequence=statement.subnode_loop_body,
        allow_none=True,
        emit=emit,
        context=context,
    )

    context.setLoopBreakTarget(old_loop_break)
    context.setLoopContinueTarget(old_loop_continue)

    # Note: We are using the wrong line here, but it's an exception, it's unclear what line it would be anyway.
    with context.withCurrentSourceCodeReference(statement.getSourceReference()):
        getErrorExitBoolCode(
            condition="CONSIDER_THREADING(tstate) == false", emit=emit, context=context
        )

    getGotoCode(loop_start_label, emit)

    if loop_end_label is not None:
        getLabelCode(loop_end_label, emit)


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
