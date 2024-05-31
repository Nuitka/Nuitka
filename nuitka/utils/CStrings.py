#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" C string encoding

This contains the code to create string literals for C to represent the given
values.
"""

import codecs
import re

from nuitka.__past__ import to_byte, unicode


def _identifierEncode(c):
    """Nuitka handler to encode unicode to ASCII identifiers for C compiler."""
    return "$%02x$" % ord(c.object[c.end - 1]), c.end


codecs.register_error("c_identifier", _identifierEncode)


def _encodePythonStringToC(value):
    """Encode a string, so that it gives a C string literal.

    This doesn't handle limits.
    """
    assert type(value) is bytes, type(value)

    result = ""
    octal = False

    for c in value:
        if str is bytes:
            cv = ord(c)
        else:
            cv = c

        if c in b'\\\t\r\n"?':
            result += r"\%03o" % cv

            octal = True
        elif 32 <= cv <= 127:
            if octal and c in b"0123456789":
                result += '" "'

            result += chr(cv)

            octal = False
        else:
            result += r"\%o" % cv

            octal = True

    result = result.replace('" "\\', "\\")

    return '"%s"' % result


def encodePythonUnicodeToC(value):
    """Encode a string, so that it gives a wide C string literal."""
    assert type(value) is unicode, type(value)

    result = ""
    last_was_hex = False

    for c in value:
        cv = ord(c)

        if c == "\\":
            result += "\\\\"
            last_was_hex = False
        elif 34 < cv < 128:
            if last_was_hex:
                result += '" L"'

            result += c
            last_was_hex = False
        else:
            result += r"\x%04x" % cv
            last_was_hex = True

    return 'L"%s"' % result


def encodePythonStringToC(value):
    """Encode bytes, so that it gives a C string literal."""

    # Not all compilers allow arbitrary large C strings, therefore split it up
    # into chunks. That changes nothing to the meanings, but is easier on the
    # parser. Currently only MSVC is known to have this issue, but the
    # workaround can be used universally.

    result = _encodePythonStringToC(value[:16000])
    value = value[16000:]

    while value:
        result += " "
        result += _encodePythonStringToC(value[:16000])
        value = value[16000:]

    return result


def decodeCStringToPython(value):
    assert value.startswith('"')
    value = value[1:-1]

    result = b""

    while value:
        if value[0] == "\\":
            value = value[1:]
            if value[0] == "\\":
                result += b"\\"
                continue

            if value[0].isdigit():
                assert value[1].isdigit(), value
                assert value[2].isdigit(), value

                octal_number = int(value[2]) + int(value[1]) * 8 + int(value[0]) * 64
                value = value[3:]

                result += to_byte(octal_number)
                continue

            assert False, value[0]

        result += value[0].encode("ascii")
        value = value[1:]

    return result


def encodePythonIdentifierToC(value):
    """Encode an identifier from a given Python string."""

    # Python identifiers allow almost of characters except a very
    # few, much more than C identifiers support. This attempts to
    # be bi-directional, so we can reverse it.

    def r(match):
        c = match.group()

        if c == ".":
            return "$"
        else:
            return "$$%d$" % ord(c)

    return re.sub("[^a-zA-Z0-9_]", r, value)


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
