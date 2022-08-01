#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Read/write source code from files.

Reading is tremendously more complex than one might think, due to encoding
issues and version differences of Python versions.
"""

import os
import re
import sys

from nuitka import Options, SourceCodeReferences
from nuitka.__past__ import unicode
from nuitka.plugins.Plugins import Plugins
from nuitka.PythonVersions import python_version, python_version_str
from nuitka.Tracing import general, my_print
from nuitka.utils.FileOperations import putTextFileContents
from nuitka.utils.Shebang import getShebangFromSource, parseShebang
from nuitka.utils.Utils import isWin32OrPosixWindows

from .SyntaxErrors import raiseSyntaxError

_fstrings_installed = False


def _installFutureFStrings():
    """Install fake UTF8 handle just as future-fstrings does.

    This unbreaks at least
    """

    # Singleton, pylint: disable=global-statement
    global _fstrings_installed

    if _fstrings_installed:
        return

    # TODO: Not supporting anything before that.
    if python_version >= 0x360:
        import codecs

        # Play trick for of "future_strings" PyPI package support. It's not needed,
        # but some people use it even on newer Python.
        try:
            codecs.lookup("future-fstrings")
        except LookupError:
            import encodings

            utf8 = encodings.search_function("utf8")
            codec_map = {"future-fstrings": utf8, "future_fstrings": utf8}
            codecs.register(codec_map.get)
    else:
        try:
            import future_fstrings
        except ImportError:
            pass
        else:
            future_fstrings.register()

    _fstrings_installed = True


def _readSourceCodeFromFilename3(source_filename):
    # Only using this for Python3, for Python2 it's too buggy.
    import tokenize

    _installFutureFStrings()

    with tokenize.open(source_filename) as source_file:
        return source_file.read()


def _detectEncoding2(source_file):
    # Detect the encoding.
    encoding = "ascii"

    line1 = source_file.readline()

    if line1.startswith(b"\xef\xbb\xbf"):
        # BOM marker makes it clear.
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
    _installFutureFStrings()

    # Detect the encoding, we do not know it, pylint: disable=unspecified-encoding
    with open(source_filename, "rU") as source_file:
        encoding = _detectEncoding2(source_file)

        source_code = source_file.read()

        # Try and detect SyntaxError from missing or wrong encodings.
        if type(source_code) is not unicode and encoding == "ascii":
            try:
                _source_code = source_code.decode(encoding)
            except UnicodeDecodeError as e:
                lines = source_code.split("\n")
                so_far = 0

                for count, line in enumerate(lines):
                    so_far += len(line) + 1

                    if so_far > e.args[2]:
                        break
                else:
                    # Cannot happen, decode error implies non-empty.
                    count = -1

                wrong_byte = re.search(
                    "byte 0x([a-f0-9]{2}) in position", str(e)
                ).group(1)

                raiseSyntaxError(
                    """\
Non-ASCII character '\\x%s' in file %s on line %d, but no encoding declared; \
see http://python.org/dev/peps/pep-0263/ for details"""
                    % (wrong_byte, source_filename, count + 1),
                    SourceCodeReferences.fromFilename(source_filename).atLineNumber(
                        count + 1
                    ),
                    display_line=False,
                )

    return source_code


def readSourceCodeFromFilename(module_name, source_filename):
    if python_version < 0x300:
        source_code = _readSourceCodeFromFilename2(source_filename)
    else:
        source_code = _readSourceCodeFromFilename3(source_filename)

    # Allow plugins to mess with source code. Test code calls this
    # without a module and doesn't want changes from plugins.
    if module_name is not None:
        source_code_modified = Plugins.onModuleSourceCode(module_name, source_code)
    else:
        source_code_modified = source_code

    if Options.shallShowSourceModifications() and source_code_modified != source_code:
        import difflib

        diff = difflib.unified_diff(
            source_code.splitlines(),
            source_code_modified.splitlines(),
            "original",
            "modified",
            "",
            "",
            n=3,
        )

        result = list(diff)

        if result:
            for line in result:
                my_print(line, end="\n" if not line.startswith("---") else "")

    return source_code_modified


def checkPythonVersionFromCode(source_code):
    # There is a lot of cases to consider, pylint: disable=too-many-branches

    shebang = getShebangFromSource(source_code)

    if shebang is not None:
        binary, _args = parseShebang(shebang)

        if not isWin32OrPosixWindows():
            try:
                if os.path.samefile(sys.executable, binary):
                    return True
            except OSError:  # Might not exist
                pass

        basename = os.path.basename(binary)

        # Not sure if we should do that.
        if basename == "python":
            result = python_version < 0x300
        elif basename == "python3":
            result = python_version >= 0x300
        elif basename == "python2":
            result = python_version < 0x300
        elif basename == "python2.7":
            result = python_version < 0x300
        elif basename == "python2.6":
            result = python_version < 0x270
        elif basename == "python3.2":
            result = 0x330 > python_version >= 0x300
        elif basename == "python3.3":
            result = 0x340 > python_version >= 0x330
        elif basename == "python3.4":
            result = 0x350 > python_version >= 0x340
        elif basename == "python3.5":
            result = 0x360 > python_version >= 0x350
        elif basename == "python3.6":
            result = 0x370 > python_version >= 0x360
        elif basename == "python3.7":
            result = 0x380 > python_version >= 0x370
        elif basename == "python3.8":
            result = 0x390 > python_version >= 0x380
        elif basename == "python3.9":
            result = 0x3A0 > python_version >= 0x390
        elif basename == "python3.10":
            result = 0x3B0 > python_version >= 0x3A0
        else:
            result = None

        if result is False:
            general.sysexit(
                """\
The program you compiled wants to be run with: %s.

Nuitka is currently running with Python version '%s', which seems to not
match that. Nuitka cannot guess the Python version of your source code. You
therefore might want to specify: '%s -m nuitka'.

That will make use the correct Python version for Nuitka.
"""
                % (shebang, python_version_str, binary)
            )


def readSourceLine(source_ref):
    import linecache

    return linecache.getline(
        filename=source_ref.getFilename(), lineno=source_ref.getLineNumber()
    )


def writeSourceCode(filename, source_code):
    # Prevent accidental overwriting. When this happens the collision detection
    # or something else has failed.
    assert not os.path.isfile(filename), filename

    putTextFileContents(filename=filename, contents=source_code, encoding="latin1")
