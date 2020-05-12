#!/usr/bin/env python
#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
import subprocess
import sys
from logging import warning

from nuitka.tools.quality.Git import (
    getFileHashContent,
    putFileHashContent,
    updateFileIndex,
    updateWorkingFile,
)
from nuitka.Tracing import my_print
from nuitka.utils.Execution import (
    check_call,
    getExecutablePath,
    withEnvironmentPathAdded,
)
from nuitka.utils.FileOperations import (
    getFileContents,
    renameFile,
    withPreserveFileMode,
)
from nuitka.utils.Shebang import getShebangFromFile
from nuitka.utils.Utils import getOS


def cleanupWindowsNewlines(filename):
    """ Remove Windows new-lines from a file.

        Simple enough to not depend on external binary and used by
        the doctest extractions of the CPython test suites.
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
        source_lines = list(f)

    clean_lines = [line.rstrip().replace("\t", "    ") for line in source_lines]

    while clean_lines and clean_lines[-1] == "":
        del clean_lines[-1]

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
                sorted(renamer(token) for token in part.group(2).split(",") if token)
            )

        new_value = str(comment_node.value).replace("pylint:disable", "pylint: disable")
        new_value = re.sub(r"(pylint\: disable=)(.*)", replacer, new_value, flags=re.M)

        comment_node.value = new_value


def _cleanupPyLintComments(filename, abort):
    from redbaron import (  # pylint: disable=I0021,import-error,no-name-in-module
        RedBaron,
    )

    old_code = getFileContents(filename)

    # Baron does assertions too, and all kinds of strange errors, pylint: disable=broad-except

    try:
        red = RedBaron(old_code)
    except Exception:
        if abort:
            raise

        return

    for node in red.find_all("CommentNode"):
        try:
            _updateCommentNode(node)
        except Exception:
            my_print("Problem with", node)
            node.help(deep=True, with_formatting=True)
            raise

    new_code = red.dumps()

    if new_code != old_code:
        with open(filename, "w") as source_code:
            source_code.write(red.dumps())


def _cleanupImportRelative(filename):
    """ Make imports of Nuitka package when possible.

    """

    # Avoid doing it for "__main__" packages, because for those the Visual Code
    # IDE doesn't like it and it may not run
    if os.path.basename(filename) == "__main__.py.tmp":
        return

    package_name = os.path.dirname(filename).replace(os.path.sep, ".")

    # Make imports local if possible.
    if not package_name.startswith("nuitka."):
        return

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
    _cleanupImportRelative(filename)

    isort_call = _getPythonBinaryCall("isort")

    contents = getFileContents(filename)

    start_index = None
    if "\n# isort:start" in contents:
        parts = contents.splitlines()

        start_index = parts.index("# isort:start")
        contents = "\n".join(parts[start_index + 1 :])

        with open(filename, "w") as out_file:
            out_file.write(contents)

    with open(os.devnull, "w") as devnull:
        check_call(
            isort_call
            + [
                "-q",  # quiet, but stdout is still garbage
                "-ot",  # Order imports by type in addition to alphabetically
                "-m3",  # "vert-hanging"
                "-up",  # Prefer braces () over \ for line continuation.
                "-tc",  # Trailing commas
                "-p",  # make sure nuitka is first party package in import sorting.
                "nuitka",
                "-ns",  # Do not ignore those:
                "__init__.py",
                filename,
            ],
            stdout=devnull,
        )

    if start_index is not None:
        contents = getFileContents(filename)

        contents = "\n".join(parts[: start_index + 1]) + "\n" + contents

        with open(filename, "w") as out_file:
            out_file.write(contents)


warned_clang_format = False


def _cleanupClangFormat(filename):
    """ Call clang-format on a given filename to format C code.

    Args:
        filename: What file to re-format.
    """

    # Using global here, as this is really a singleton, in
    # the form of a module, pylint: disable=global-statement
    global warned_clang_format

    clang_format_path = getExecutablePath("clang-format-8") or getExecutablePath(
        "clang-format-7"
    )

    # Extra ball on Windows, check default installations paths in MSVC and LLVM too.
    if not clang_format_path and getOS() == "Windows":
        with withEnvironmentPathAdded(
            "PATH",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\Llvm\bin",
            r"C:\Program Files\LLVM\bin",
        ):
            clang_format_path = getExecutablePath("clang-format")

    if clang_format_path:
        subprocess.call(
            [
                clang_format_path,
                "-i",
                "-style={BasedOnStyle: llvm, IndentWidth: 4, ColumnLimit: 120}",
                filename,
            ]
        )
    else:
        if not warned_clang_format:

            warning("Need to install LLVM for C files format.")
            warned_clang_format = True


def _shouldNotFormatCode(filename):
    parts = os.path.abspath(filename).split(os.path.sep)

    if "inline_copy" in parts:
        return True
    elif "tests" in parts and not "basics" in parts and "programs" not in parts:
        return parts[-1] not in (
            "run_all.py",
            "compile_itself.py",
            "update_doctest_generated.py",
            "compile_itself.py",
            "compile_python_modules.py",
            "compile_extension_modules.py",
        )
    else:
        return False


def _isPythonFile(filename):
    if filename.endswith((".py", ".pyw", ".scons")):
        return True
    else:
        shebang = getShebangFromFile(filename)

        if shebang is not None:
            shebang = shebang[2:].lstrip()
            if shebang.startswith("/usr/bin/env"):
                shebang = shebang[12:].lstrip()

            if shebang.startswith("python"):
                return True

    return False


def _transferBOM(source_filename, target_filename):
    with open(source_filename, "rb") as f:
        source_code = f.read()

    if source_code.startswith(b"\xef\xbb\xbf"):
        with open(target_filename, "rb") as f:
            source_code = f.read()

        if not source_code.startswith(b"\xef\xbb\xbf"):
            with open(target_filename, "wb") as f:
                f.write(b"\xef\xbb\xbf")
                f.write(source_code)


def autoformat(filename, git_stage, abort, effective_filename=None):
    """ Format source code with external tools

    Args:
        filename: filename to work on
        git_stage: indicate if this is to be done on staged content
        abort: error exit in case a tool shows a problem
        effective_filename: derive type of file from this name

    Notes:
        The effective filename can be used in case this is already a
        temporary filename intended to replace another.

    Returns:
        None
    """

    # This does a lot of distinctions, pylint: disable=too-many-branches,too-many-statements

    if effective_filename is None:
        effective_filename = filename

    if os.path.isdir(effective_filename):
        return

    filename = os.path.normpath(filename)
    effective_filename = os.path.normpath(effective_filename)

    my_print("Consider", filename, end=": ")

    is_python = _isPythonFile(effective_filename)

    is_c = effective_filename.endswith((".c", ".h"))

    is_txt = effective_filename.endswith(
        (
            ".patch",
            ".txt",
            ".rst",
            ".sh",
            ".in",
            ".md",
            ".yml",
            ".stylesheet",
            ".j2",
            ".gitignore",
            ".json",
            ".spec",
            "-rpmlintrc",
        )
    ) or os.path.basename(filename) in (
        "changelog",
        "compat",
        "control",
        "lintian-overrides",
    )

    # Some parts of Nuitka must not be re-formatted with black or clang-format
    # as they have different intentions.
    if not (is_python or is_c or is_txt):
        my_print("Ignored file type.")
        return

    # Work on a temporary copy
    tmp_filename = filename + ".tmp"

    if git_stage:
        old_code = getFileHashContent(git_stage["dst_hash"])
    else:
        old_code = getFileContents(filename, "rb")

    with open(tmp_filename, "wb") as output_file:
        output_file.write(old_code)

    try:
        if is_python:
            cleanupWindowsNewlines(tmp_filename)

            if not _shouldNotFormatCode(effective_filename):
                _cleanupImportSortOrder(tmp_filename)
                _cleanupPyLintComments(tmp_filename, abort)

                black_call = _getPythonBinaryCall("black")

                subprocess.call(black_call + ["-q", "--fast", tmp_filename])
                cleanupWindowsNewlines(tmp_filename)

        elif is_c:
            cleanupWindowsNewlines(tmp_filename)
            _cleanupClangFormat(filename)
            cleanupWindowsNewlines(tmp_filename)
        elif is_txt:
            cleanupWindowsNewlines(tmp_filename)
            _cleanupTrailingWhitespace(tmp_filename)
            cleanupWindowsNewlines(tmp_filename)

        _transferBOM(filename, tmp_filename)

        changed = False
        if old_code != getFileContents(tmp_filename, "rb"):
            my_print("Updated.")

            with withPreserveFileMode(filename):
                if git_stage:
                    new_hash_value = putFileHashContent(tmp_filename)
                    updateFileIndex(git_stage, new_hash_value)
                    updateWorkingFile(filename, git_stage["dst_hash"], new_hash_value)
                else:
                    renameFile(tmp_filename, filename)

            changed = True
        else:
            my_print("OK.")

        return changed
    finally:
        if os.path.exists(tmp_filename):
            os.unlink(tmp_filename)
