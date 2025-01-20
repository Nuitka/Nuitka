#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" C labels, small helpers.

Much things are handled with "goto" statements in the generated code, error
exits, finally blocks, etc. this provides just the means to emit a label or
the goto statement itself.
"""

from nuitka.utils.CStrings import encodePythonStringToC


def getGotoCode(label, emit):
    assert label is not None

    emit("goto %s;" % label)


def getLabelCode(label, emit):
    assert label is not None

    emit("%s:;" % label)


def getBranchingCode(condition, emit, context):
    true_target = context.getTrueBranchTarget()
    false_target = context.getFalseBranchTarget()

    if true_target is not None and false_target is None:
        emit("if (%s) goto %s;" % (condition, true_target))
    elif true_target is None and false_target is not None:
        emit("if (!(%s)) goto %s;" % (condition, false_target))
    else:
        assert true_target is not None and false_target is not None

        emit(
            """\
if (%s) {
    goto %s;
} else {
    goto %s;
}"""
            % (condition, true_target, false_target)
        )


def getStatementTrace(source_desc, statement_repr):
    return 'NUITKA_PRINT_TRACE("Execute: " %s);' % (
        encodePythonStringToC(source_desc + b" " + statement_repr),
    )


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
