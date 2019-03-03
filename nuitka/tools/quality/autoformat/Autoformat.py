#!/usr/bin/env python
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

""" Tool to automatically format source code in Nuitka style.

"""

import os
import re
import shutil
import subprocess
import sys

from nuitka.Tracing import my_print
from nuitka.utils.Execution import getExecutablePath
from nuitka.utils.FileOperations import getFileContents
from nuitka.utils.Shebang import getShebangFromFile
from nuitka.utils.Utils import getOS


def _cleanupWindowsNewlines(filename):
    """ Remove Windows new-lines from a file.

        Simple enough to not depend on external binary.
    """

    with open(filename, "rb") as f:
        source_code = f.read()

    updated_code = source_code.replace(b"\r\n", b"\n")
    updated_code = updated_code.replace(b"\n\r", b"\n")

    if updated_code != source_code:
        with open(filename, "wb") as out_file:
            out_file.write(updated_code)


def _cleanupTrailingWhitespace(filename):
    """ Remove trailing white spaces from a file.

    """
    with open(filename, "r") as f:
        source_lines = [line for line in f]

    clean_lines = [line.rstrip() for line in source_lines]

    if clean_lines != source_lines:
        with open(filename, "w") as out_file:
            out_file.write("\n".join(clean_lines) + "\n")


def _updateCommentNode(comment_node):
    if "pylint:" in str(comment_node.value):

        def replacer(part):
            def renamer(pylint_token):
                # pylint: disable=too-many-branches,too-many-return-statements
                if pylint_token == "E0602":
                    return "undefined-variable"
                elif pylint_token in ("E0401", "F0401"):
                    return "import-error"
                elif pylint_token == "E1102":
                    return "not-callable"
                elif pylint_token == "E1133":
                    return "  not-an-iterable"
                elif pylint_token == "E1128":
                    return "assignment-from-none"
                # Save line length for this until isort is better at long lines.
                elif pylint_token == "useless-suppression":
                    return "I0021"
                #                     elif pylint_token == "I0021":
                #                        return "useless-suppression"
                elif pylint_token == "R0911":
                    return "too-many-return-statements"
                elif pylint_token == "R0201":
                    return "no-self-use"
                elif pylint_token == "R0902":
                    return "too-many-instance-attributes"
                elif pylint_token == "R0912":
                    return "too-many-branches"
                elif pylint_token == "R0914":
                    return "too-many-locals"
                elif pylint_token == "R0915":
                    return "too-many-statements"
                elif pylint_token == "W0123":
                    return "eval-used"
                elif pylint_token == "W0603":
                    return "global-statement"
                elif pylint_token == "W0613":
                    return "unused-argument"
                elif pylint_token == "W0622":
                    return "redefined-builtin"
                elif pylint_token == "W0703":
                    return "broad-except"
                else:
                    return pylint_token

            return part.group(1) + ",".join(
                sorted(renamer(token) for token in part.group(2).split(","))
            )

        new_value = re.sub(
            r"(pylint\: disable=)(.*)", replacer, str(comment_node.value), flags=re.M
        )
        comment_node.value = new_value


def _cleanupPyLintComments(filename, abort):
    from baron.parser import (  # pylint: disable=I0021,import-error,no-name-in-module
        ParsingError,  # @UnresolvedImport
    )
    from redbaron import (  # pylint: disable=I0021,import-error,no-name-in-module
        RedBaron,  # @UnresolvedImport
    )

    old_code = getFileContents(filename)

    try:
        red = RedBaron(old_code)
        # red = RedBaron(old_code.rstrip()+'\n')
    except ParsingError:
        if abort:
            raise

        my_print("PARSING ERROR.")
        return 2

    for node in red.find_all("CommentNode"):
        try:
            _updateCommentNode(node)
        except Exception:
            my_print("Problem with", node)
            node.help(deep=True, with_formatting=True)
            raise

    new_code = red.dumps()

    if new_code != old_code:
        new_name = filename + ".new"

        with open(new_name, "w") as source_code:
            source_code.write(red.dumps())

        # There is no way to safely replace a file on Windows, but lets try on Linux
        # at least.
        old_stat = os.stat(filename)

        try:
            os.rename(new_name, filename)
        except OSError:
            shutil.copyfile(new_name, filename)
            os.unlink(new_name)

        os.chmod(filename, old_stat.st_mode)


def _cleanupImportRelative(filename):
    package_name = os.path.dirname(filename)

    # Make imports local if possible.
    if package_name.startswith("nuitka" + os.path.sep):
        package_name = package_name.replace(os.path.sep, ".")

        source_code = getFileContents(filename)
        updated_code = re.sub(
            r"from %s import" % package_name, "from . import", source_code
        )
        updated_code = re.sub(r"from %s\." % package_name, "from .", source_code)

        if source_code != updated_code:
            with open(filename, "w") as out_file:
                out_file.write(updated_code)


_binary_calls = {}


def _getPythonBinaryCall(binary_name):
    if binary_name not in _binary_calls:
        # Try running Python installation.
        try:
            __import__(binary_name)
            _binary_calls[binary_name] = [sys.executable, "-m", binary_name]

            return _binary_calls[binary_name]
        except ImportError:
            pass

        binary_path = getExecutablePath(binary_name)

        if binary_path:
            _binary_calls[binary_name] = [binary_path]
            return _binary_calls[binary_name]

        sys.exit("Error, cannot find %s, not installed for this Python?" % binary_name)

    return _binary_calls[binary_name]


def _cleanupImportSortOrder(filename):
    isort_call = _getPythonBinaryCall("isort")

    with open(os.devnull, "w") as devnull:
        subprocess.check_call(
            isort_call
            + [
                "-q",  # quiet, but stdout is still garbage
                "-ot",  # Order imports by type in addition to alphabetically
                "-m3",  # "vert-hanging"
                "-up",  # Prefer braces () over \ for line continuation.
                "-tc",  # Trailing commas
                "-ns",  # Do not ignore those:
                "__init__.py",
                filename,
            ],
            stdout=devnull,
        )


def autoformat(filename, abort=False):
    my_print("Consider", filename, end=": ")

    old_code = getFileContents(filename)

    is_python = False
    if filename.endswith((".py", ".pyw")):
        is_python = True
    else:
        shebang = getShebangFromFile(filename)

        if shebang is not None and shebang.startswith("python"):
            shebang = True

    if is_python:
        _cleanupPyLintComments(filename, abort)

        _cleanupImportSortOrder(filename)

    _cleanupTrailingWhitespace(filename)

    if is_python:
        black_call = _getPythonBinaryCall("black")

        subprocess.call(black_call + ["-q", filename])

    if getOS() == "Windows":
        _cleanupWindowsNewlines(filename)

    changed = False
    if old_code != getFileContents(filename):
        my_print("Updated.")
        changed = True
    else:
        my_print("OK.")

    return changed
