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
""" Handling of syntax errors.

Format SyntaxError/IndentationError exception for output, as well as
raise it for the given source code reference.
"""


def formatOutput(e):
    if len(e.args) > 1:
        reason, (filename, lineno, colno, message) = e.args

        if message is None and colno is not None:
            colno = None

        if lineno is not None and lineno == 0:
            lineno = 1
    else:
        reason, = e.args

        filename = None
        lineno = None
        colno = None
        message = None

    # On CPython3.4 at least, this attribute appears to override reason for
    # SyntaxErrors at least.
    if hasattr(e, "msg"):
        reason = e.msg

    if colno is not None:
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


def raiseSyntaxError(reason, source_ref, display_file=True, display_line=True):
    col_offset = source_ref.getColumnNumber()

    def readSource():
        # Cyclic dependency.
        from .SourceReading import readSourceLine

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

        raise SyntaxError(
            reason,
            (
                source_ref.getFilename(),
                source_ref.getLineNumber(),
                col_offset,
                source_line,
            ),
        )

    raise SyntaxError(reason, (None, None, None, None))
