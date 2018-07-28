#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Read source code from files.

This is tremendously more complex than one might think, due to encoding issues
and version differences of Python versions.
"""

import os
import re
import sys

from nuitka import Options, SourceCodeReferences
from nuitka.__past__ import unicode  # pylint: disable=I0021,redefined-builtin
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version, python_version_str
from nuitka.utils.Shebang import getShebangFromSource, parseShebang
from nuitka.utils.Utils import getOS

from .SyntaxErrors import raiseSyntaxError


def _readSourceCodeFromFilename3(source_filename):
    # Only using this for Python3, for Python2 it's too buggy.
    import tokenize

    with tokenize.open(source_filename) as source_file:   # @UndefinedVariable
        return source_file.read()


def _detectEncoding2(source_file):
    # Detect the encoding.
    encoding = "ascii"

    line1 = source_file.readline()

    if line1.startswith(b'\xef\xbb\xbf'):
        encoding = "utf-8"
    else:
        line1_match = re.search(b"coding[:=]\\s*([-\\w.]+)", line1)

        if line1_match:
            encoding = line1_match.group(1)
        else:
            line2 = source_file.readline()

            line2_match = re.search(b"coding[:=]\\s*([-\\w.]+)", line2)

            if line2_match:
                encoding = line2_match.group(1)

    source_file.seek(0)

    return encoding


def _readSourceCodeFromFilename2(source_filename):
    # Detect the encoding.
    with open(source_filename, "rU") as source_file:
        encoding = _detectEncoding2(source_file)

        source_code = source_file.read()

        # Try and detect SyntaxError from missing or wrong encodings.
        if type(source_code) is not unicode and encoding == "ascii":
            try:
                _source_code = source_code.decode(encoding)
            except UnicodeDecodeError as e:
                lines = source_code.split('\n')
                so_far = 0

                for count, line in enumerate(lines):
                    so_far += len(line) + 1

                    if so_far > e.args[2]:
                        break
                else:
                    # Cannot happen, decode error implies non-empty.
                    count = -1

                wrong_byte = re.search(
                    "byte 0x([a-f0-9]{2}) in position",
                    str(e)
                ).group(1)

                raiseSyntaxError(
                    """\
Non-ASCII character '\\x%s' in file %s on line %d, but no encoding declared; \
see http://python.org/dev/peps/pep-0263/ for details""" % (
                        wrong_byte,
                        source_filename,
                        count+1,
                    ),
                    SourceCodeReferences.fromFilename(source_filename).atLineNumber(
                        count+1
                    ),
                    display_line = False
                )

    return source_code


def readSourceCodeFromFilename(module_name, source_filename):
    if python_version < 300:
        source_code = _readSourceCodeFromFilename2(source_filename)
    else:
        source_code = _readSourceCodeFromFilename3(source_filename)

    # Allow plug-ins to mess with source code.
    source_code = Plugins.onModuleSourceCode(module_name, source_code)

    return source_code


def checkPythonVersionFromCode(source_code):
    # There is a lot of cases to consider, pylint: disable=too-many-branches

    shebang = getShebangFromSource(source_code)

    if shebang is not None:
        binary, _args = parseShebang(shebang)

        if getOS() != "Windows":
            try:
                if os.path.samefile(sys.executable, binary):
                    return True
            except OSError: # Might not exist
                pass

        basename = os.path.basename(binary)

        # Not sure if we should do that.
        if basename == "python":
            result = python_version < 300
        elif basename == "python3":
            result = python_version > 300
        elif basename == "python2":
            result = python_version < 300
        elif basename == "python2.7":
            result = python_version < 300
        elif basename == "python2.6":
            result = python_version < 270
        elif basename == "python3.2":
            result = 330 > python_version >= 300
        elif basename == "python3.3":
            result = 340 > python_version >= 330
        elif basename == "python3.4":
            result = 350 > python_version >= 340
        elif basename == "python3.5":
            result = 360 > python_version >= 350
        elif basename == "python3.6":
            result = 370 > python_version >= 360
        else:
            result = None

        if result is False and Options.getIntendedPythonVersion() is None:
            sys.exit("""\
The program you compiled wants to be run with: %s.

Nuitka is currently running with Python version '%s', which seems to not
match that. Nuitka cannot guess the Python version of your source code. You
therefore might want to specify: '%s -m nuitka'.

That will make use the correct Python version for Nuitka.
""" % (shebang, python_version_str, binary)
            )


def readSourceLine(source_ref):
    import linecache
    return linecache.getline(
        filename = source_ref.getFilename(),
        lineno   = source_ref.getLineNumber()
    )
