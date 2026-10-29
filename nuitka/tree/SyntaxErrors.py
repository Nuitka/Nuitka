#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Handling of syntax errors.

Format SyntaxError/IndentationError exception for output, as well as
raise it for the given source code reference.
"""

import ast

from nuitka.PythonVersions import (
    getErrorMessageDebugAssignment,
    getErrorMessageDebugDeletion,
    python_version,
)


def formatOutput(e):
    if len(e.args) > 1:
        if len(e.args[1]) == 4:
            reason, (filename, lineno, colno, message) = e.args
        else:
            reason, (filename, lineno, colno, message, _lineno2, _colno2) = e.args

        if message is None and colno is not None:
            colno = None

        if lineno is not None and lineno == 0:
            lineno = 1
    else:
        (reason,) = e.args

        filename = None
        lineno = None
        colno = None
        message = None

    # On CPython3.4 at least, this attribute appears to override reason for
    # SyntaxErrors at least.
    if hasattr(e, "msg"):
        reason = e.msg

    if colno is not None and (
        e.__class__ is not IndentationError or python_version < 0x390
    ):
        colno = colno - len(message) + len(message.lstrip())

        return """\
  File "%s", line %d
    %s
    %s^
%s: %s""" % (
            filename,
            lineno,
            message.strip(),
            " " * (colno - 1) if colno is not None else "",
            e.__class__.__name__,
            reason,
        )
    elif message is not None:
        return """\
  File "%s", line %d
    %s
%s: %s""" % (
            filename,
            lineno,
            message.strip(),
            e.__class__.__name__,
            reason,
        )
    elif filename is not None:
        return """\
  File "%s", line %s
%s: %s""" % (
            filename,
            lineno,
            e.__class__.__name__,
            reason,
        )
    else:
        return """\
%s: %s""" % (
            e.__class__.__name__,
            reason,
        )


def checkDebugNameAssignment(name, source_ref):
    """Raise a SyntaxError if the given name is '__debug__'."""

    if name == "__debug__":
        raiseSyntaxError(getErrorMessageDebugAssignment(), source_ref)


def checkDebugNameTarget(node, source_ref):
    """Raise a SyntaxError if the given assignment target is '__debug__'."""

    if type(node) is str:
        checkDebugNameAssignment(name=node, source_ref=source_ref)
        return

    if node.__class__ is ast.Name:
        name = node.id
    elif node.__class__ is ast.Attribute:
        if python_version < 0x270:
            return

        name = node.attr
    else:
        return

    if node.ctx.__class__ is ast.Store:
        checkDebugNameAssignment(name=name, source_ref=source_ref)
    elif node.ctx.__class__ is ast.Del and name == "__debug__":
        deletion_reason = getErrorMessageDebugDeletion()

        if deletion_reason is not None:
            raiseSyntaxError(deletion_reason, source_ref)


def checkExceptStarHandlerBody(body, source_ref, check_return):
    """Raise a SyntaxError for 'return', 'break', and 'continue' in an 'except*'.

    Notes:
        These statements must not escape an 'except*' block, but are allowed
        within a nested loop body for the latter two, and within nested
        function and class scopes for all of them. The 'return' check is
        disabled outside of function scopes, where it is not the error that
        CPython reports.
    """

    def raiseEscape(node):
        raiseSyntaxError(
            "'break', 'continue' and 'return' cannot appear in an except* block",
            source_ref.atLineNumber(node.lineno).atColumnNumber(node.col_offset),
        )

    def checkNode(node, in_loop):
        node_class = node.__class__

        # These have their own scope, escaping them is not escaping the
        # "except*" block.
        if node_class in (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.Lambda,
            ast.ClassDef,
        ):
            return

        if node_class is ast.Return:
            if check_return:
                raiseEscape(node)
        elif node_class in (ast.Break, ast.Continue):
            if not in_loop:
                raiseEscape(node)
        elif node_class in (ast.For, ast.AsyncFor, ast.While):
            if node_class is ast.While:
                checkNode(node.test, in_loop)
            else:
                # The loop target and iterable are not part of the loop body,
                # but cannot contain these statements either.
                checkNode(node.target, in_loop)
                checkNode(node.iter, in_loop)

            for child in node.body:
                checkNode(child, True)

            # A "break" or "continue" in the "else" block refers to an outer
            # loop, or is invalid otherwise.
            for child in node.orelse:
                checkNode(child, in_loop)
        else:
            for child in ast.iter_child_nodes(node):
                checkNode(child, in_loop)

    for child in body:
        checkNode(child, False)


def raiseSyntaxError(reason, source_ref, display_file=True, display_line=True):
    col_offset = source_ref.getColumnNumber()

    def readSource():
        # Cyclic dependency.
        from .SourceHandling import readSourceLine

        return readSourceLine(source_ref)

    # Special case being asked to display.
    if display_file and display_line:
        source_line = readSource()

        raise SyntaxError(
            reason,
            (
                source_ref.getFilename(),
                source_ref.getLineNumber(),
                col_offset,
                source_line,
            ),
        )

    # Special case given source reference.
    if source_ref is not None:
        if display_line:
            source_line = readSource()
        else:
            source_line = None

        exc = SyntaxError(
            reason,
            (
                source_ref.getFilename(),
                source_ref.getLineNumber(),
                col_offset,
                source_line,
            ),
        )

    exc = SyntaxError(reason, (None, None, None, None))

    exc.generated_by_nuitka = True

    raise exc


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
