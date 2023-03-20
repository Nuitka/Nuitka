#!/usr/bin/env python
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

""" Tool to automatically format source code in Nuitka style.

"""

import contextlib
import os
import re
import shutil
import subprocess
import sys

from nuitka.tools.quality.Git import (
    getFileHashContent,
    putFileHashContent,
    updateFileIndex,
    updateWorkingFile,
)
from nuitka.tools.quality.ScanSources import isPythonFile
from nuitka.tools.release.Documentation import extra_rst_keywords
from nuitka.Tracing import general, my_print, tools_logger
from nuitka.utils.Execution import (
    NuitkaCalledProcessError,
    check_call,
    check_output,
    getExecutablePath,
    getNullOutput,
    withEnvironmentPathAdded,
)
from nuitka.utils.FileOperations import (
    copyFile,
    getFileContentByLine,
    getFileContents,
    listDir,
    openTextFile,
    putTextFileContents,
    withPreserveFileMode,
    withTemporaryFile,
)
from nuitka.utils.Utils import isWin32OrPosixWindows

from .YamlFormatter import formatYaml

# black no longer supports Python 2 syntax, and sometimes removes import
# parts of syntax used in tests
BLACK_SKIP_LIST = [
    "tests/basics/ClassesTest.py",
    "tests/basics/ExecEvalTest.py",
    "tests/basics/HelloWorldTest_2.py",
    "tests/basics/OverflowFunctionsTest_2.py",
    "tests/basics/PrintingTest_2.py",
    "tests/benchmarks/binary-trees.py",
    "tests/benchmarks/comparisons/GeneratorFunctionVsGeneratorExpression.py",
    "tests/benchmarks/constructs/InplaceOperationUnicodeAdd_27.py",
    "tests/benchmarks/constructs/RichComparisonConditionStrings.py",
    "tests/programs/syntax_errors/IndentationErroring.py",
    "tests/syntax/ClosureDel_2.py",
    "tests/syntax/ExecWithNesting_2.py",
    "tests/syntax/IndentationError.py",
    "tests/syntax/StarImportExtra.py",
    "tests/syntax/SyntaxError.py",
    "tests/type_inference/Test1.py",
    "tests/type_inference/Test2.py",
    "tests/type_inference/Test3.py",
    "tests/type_inference/Test4.py",
    "tests/benchmarks/pystone.py",
]
BLACK_SKIP_LIST = [os.path.normpath(path) for path in BLACK_SKIP_LIST]


def cleanupWindowsNewlines(filename, effective_filename):
    """Remove Windows new-lines from a file.

    Simple enough to not depend on external binary and used by
    the doctest extractions of the CPython test suites.
    """

    with open(filename, "rb") as f:
        source_code = f.read()

    updated_code = source_code.replace(b"\r\n", b"\n")
    updated_code = updated_code.replace(b"\n\r", b"\n")

    # Smuggle consistency replacement in here.
    if "AutoFormat.py" not in effective_filename:
        updated_code = updated_code.replace(b'.decode("utf-8")', b'.decode("utf8")')
        updated_code = updated_code.replace(b'.encode("utf-8")', b'.encode("utf8")')

    if updated_code != source_code:
        with open(filename, "wb") as out_file:
            out_file.write(updated_code)


def _cleanupTrailingWhitespace(filename):
    """Remove trailing white spaces from a file."""
    source_lines = list(getFileContentByLine(filename, encoding="utf8"))

    clean_lines = [line.rstrip().replace("\t", "    ") for line in source_lines]

    while clean_lines and clean_lines[-1] == "":
        del clean_lines[-1]

    if clean_lines != source_lines or (clean_lines and clean_lines[-1] != ""):
        putTextFileContents(filename, contents=clean_lines, encoding="utf8")


def _getRequirementsContentsByLine():
    return getFileContentByLine(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "requirements-devel.txt"
        )
    )


def _getRequiredVersion(tool):
    for line in _getRequirementsContentsByLine():
        if line.startswith(tool + " =="):
            return line.split()[2]

    tools_logger.sysexit("Error, cannot find %r in requirements-devel.txt" % tool)


def _checkRequiredVersion(tool, tool_call):
    required_version = _getRequiredVersion(tool)

    for line in _getRequirementsContentsByLine():
        if line.startswith(tool + " =="):
            required_version = line.split()[2]
            break
    else:
        tools_logger.sysexit("Error, cannot find %r in requirements-devel.txt" % tool)

    tool_call = list(tool_call) + ["--version"]

    try:
        version_output = check_output(tool_call)
    except NuitkaCalledProcessError as e:
        return False, "failed to execute: %s" % e.stderr

    if str is not bytes:
        version_output = version_output.decode("utf8")

    for line in version_output.splitlines():
        line = line.strip()

        if line.startswith(("black, ", "python -m black,", "__main__.py, ")):
            if "(" in line:
                line = line[: line.rfind("(")].strip()

            actual_version = line.split()[-1]
            break
        if line.startswith("VERSION "):
            actual_version = line.split()[-1]
            break
        if line.startswith("rstfmt "):
            actual_version = line.split()[-1]
            break

    else:
        tools_logger.sysexit(
            "Error, couldn't determine version output of '%s' ('%s')"
            % (tool, " ".join(tool_call))
        )

    message = "Version of '%s' via '%s' is required to be %r and not %r." % (
        tool,
        " ".join(tool_call),
        required_version,
        actual_version,
    )

    return required_version == actual_version, message


def _cleanupPyLintComments(filename, effective_filename):
    try:
        new_code = old_code = getFileContents(filename, encoding="utf8")
    except UnicodeDecodeError:
        my_print("Problem with file %s not having UTF8 encoding." % effective_filename)
        raise

    def replacer(part):
        def changePyLintTagName(pylint_token):
            # Save line length for this until isort is better at long lines.
            if pylint_token == "useless-suppression":
                return "I0021"
            else:
                return pylint_token

        return part.group(1) + ",".join(
            sorted(
                set(
                    changePyLintTagName(token)
                    for token in part.group(2).split(",")
                    if token
                )
            )
        )

    new_code = re.sub(r"(pylint\: disable=)\s*(.*)", replacer, new_code, flags=re.M)

    if new_code != old_code:
        putTextFileContents(filename, new_code, encoding="utf8")


def _cleanupImportRelative(filename, effective_filename):
    """Make imports of Nuitka package when possible."""

    # Avoid doing it for "__main__" packages, because for those the Visual Code
    # IDE doesn't like it and it may not run
    if os.path.basename(effective_filename) == "__main__.py":
        return

    package_name = os.path.dirname(effective_filename).replace(os.path.sep, ".")

    # Make imports local if possible.
    if not package_name.startswith("nuitka."):
        return

    source_code = getFileContents(filename, encoding="utf8")
    updated_code = re.sub(
        r"from %s import" % package_name, "from . import", source_code
    )
    updated_code = re.sub(r"from %s\." % package_name, "from .", source_code)

    if source_code != updated_code:
        putTextFileContents(filename, contents=updated_code, encoding="utf8")


_binary_calls = {}


def _getPythonBinaryCall(binary_name):
    if binary_name not in _binary_calls:
        messages = []

        # Try running Python installation.
        try:
            __import__(binary_name)
        except ImportError:
            pass
        else:
            call = [sys.executable, "-m", binary_name]

            ok, message = _checkRequiredVersion(binary_name, call)

            if ok:
                _binary_calls[binary_name] = call
                return _binary_calls[binary_name]
            else:
                messages.append(message)

        with withEnvironmentPathAdded(
            "PATH", os.path.join(sys.prefix, "Scripts"), os.path.join(sys.prefix, "bin")
        ):
            binary_path = getExecutablePath(binary_name)

        if binary_path:
            call = [binary_path]

            ok, message = _checkRequiredVersion(binary_name, call)

            if ok:
                _binary_calls[binary_name] = call
                return _binary_calls[binary_name]
            else:
                messages.append(message)

        if messages:
            my_print("ERROR")
        for message in messages:
            my_print(message, style="red")

        tools_logger.sysexit(
            "Error, cannot find '%s' version %r, not installed or wrong version for this Python?"
            % (binary_name, _getRequiredVersion(binary_name))
        )

    return _binary_calls[binary_name]


def _cleanupImportSortOrder(filename, effective_filename):
    _cleanupImportRelative(filename, effective_filename)

    isort_call = _getPythonBinaryCall("isort")

    contents = getFileContents(filename, encoding="utf8")

    start_index = None
    if "\n# isort:start" in contents:
        parts = contents.splitlines()

        start_index = parts.index("# isort:start")
        contents = "\n".join(parts[start_index + 1 :]) + "\n"

        putTextFileContents(filename, contents=contents, encoding="utf8")

    check_call(
        isort_call
        + [
            "-q",  # quiet, but stdout is still garbage
            "--overwrite-in-place",  # avoid using another temp file, this is already on one.
            "--order-by-type",  # Order imports by type in addition to alphabetically
            "--multi-line=VERTICAL_HANGING_INDENT",
            "--trailing-comma",
            "--project=nuitka",  # make sure nuitka is first party package in import sorting.
            "--float-to-top",  # move imports to start
            "--thirdparty=SCons",
            filename,
        ],
        stdout=getNullOutput(),
    )

    cleanupWindowsNewlines(filename, effective_filename)

    if start_index is not None:
        contents = getFileContents(filename, encoding="utf8")

        contents = "\n".join(parts[: start_index + 1]) + "\n\n" + contents.lstrip("\n")

        putTextFileContents(filename, contents=contents, encoding="utf8")


def _cleanupRstFmt(filename, effective_filename):
    updated_contents = contents = getFileContents(filename, mode="rb")

    for keyword in extra_rst_keywords:
        updated_contents = updated_contents.replace(
            b".. %s::" % keyword, b".. raw:: %s" % keyword
        )

    if updated_contents != contents:
        with open(filename, "wb") as out_file:
            out_file.write(updated_contents)

    rstfmt_call = _getPythonBinaryCall("rstfmt")

    check_call(
        rstfmt_call
        + [
            filename,
        ],
        #        stdout=devnull,
    )

    cleanupWindowsNewlines(filename, effective_filename)

    contents = getFileContents(filename, mode="rb")

    # Enforce choice between "bash" and "sh" for code directive. Use bash as
    # more people will know it.
    updated_contents = contents.replace(b".. code:: sh\n", b".. code:: bash\n")

    for keyword in extra_rst_keywords:
        updated_contents = updated_contents.replace(
            b".. raw:: %s" % keyword, b".. %s::" % keyword
        )

    lines = []
    inside = False
    needs_empty = False

    for line in updated_contents.splitlines():
        if line.startswith(b"-"):
            if inside and needs_empty:
                lines.append(b"")

            inside = True
            needs_empty = True
            lines.append(line)
        elif inside and line == b"":
            needs_empty = False
            lines.append(line)
        elif inside and line.startswith(b"  "):
            needs_empty = True
            lines.append(line)
        else:
            inside = False
            lines.append(line)

    updated_contents = b"\n".join(lines) + b"\n"

    if updated_contents != contents:
        with open(filename, "wb") as out_file:
            out_file.write(updated_contents)


warned_clang_format = False
_clang_format_path = None


def _getClangFormatPath():
    # Using global here, as this is really a singleton, in
    # the form of a module, pylint: disable=global-statement
    global warned_clang_format, _clang_format_path

    # Do not try a second time.
    if warned_clang_format:
        return None

    # Search Visual Code C++ extension for LLVM path.
    for candidate in ".vscode", ".vscode-server":
        vs_code_extension_path = os.path.expanduser("~/%s/extensions" % candidate)

        if not _clang_format_path and os.path.exists(vs_code_extension_path):
            for extension_path, extension_filename in listDir(vs_code_extension_path):
                if extension_filename.startswith("ms-vscode.cpptools-"):
                    with withEnvironmentPathAdded(
                        "PATH",
                        os.path.join(extension_path, "LLVM/bin"),
                    ):
                        _clang_format_path = getExecutablePath("clang-format")

                    break

    # Extra ball on Windows, check default installations paths in MSVC and LLVM too.
    if not _clang_format_path and isWin32OrPosixWindows():
        with withEnvironmentPathAdded(
            "PATH",
            r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\bin",
            r"C:\Program Files\LLVM\bin",
        ):
            _clang_format_path = getExecutablePath("clang-format")

    if not _clang_format_path:
        _clang_format_path = (
            getExecutablePath("clang-format-16")
            or getExecutablePath("clang-format-15")
            or getExecutablePath("clang-format-14")
            or getExecutablePath("clang-format-13")
            or getExecutablePath("clang-format-12")
            or getExecutablePath("clang-format-12")
            or getExecutablePath("clang-format")
        )

    if _clang_format_path:
        try:
            version_output = check_output([_clang_format_path, "--version"])

            try:
                clang_version = int(version_output.split(b"version ")[1].split(b".")[0])
            except (ValueError, IndexError, TypeError):
                general.sysexit(
                    "Failure to parse this '%s --version' output: %s"
                    % (_clang_format_path, version_output),
                )

            if clang_version < 12:
                general.warning(
                    """\
You need to install clang-format version 12 or higher. Easiest is to have Visual Code with
the recommended extensions installed under your user, as that will then be used by default.
"""
                )
        except NuitkaCalledProcessError as e:
            general.warning(
                "failed to execute clang-format version check: %s" % e.stderr
            )
            _clang_format_path = None

    if not _clang_format_path and not warned_clang_format:
        general.warning("Need to install LLVM for C files format.")
        warned_clang_format = True

    return _clang_format_path


def _cleanupClangFormat(filename):
    """Call clang-format on a given filename to format C code.

    Args:
        filename: What file to re-format.
    """

    clang_format_path = _getClangFormatPath()

    if clang_format_path:
        subprocess.call(
            [
                clang_format_path,
                "-i",
                "-style={BasedOnStyle: llvm, IndentWidth: 4, ColumnLimit: 120}",
                filename,
            ]
        )


def _shouldNotFormatCode(filename):
    # return driven with more cases than necessary to group things
    # pylint:disable=too-many-return-statements

    parts = os.path.normpath(filename).split(os.path.sep)

    if "inline_copy" in parts:
        # Our Scons runner should be formatted.
        if os.path.basename(filename) == "scons.py":
            return False

        return True
    if "pybench" in parts:
        return True
    if "mercurial" in parts:
        return True
    if "tests" in parts and parts[parts.index("tests") + 1].startswith("CPython"):
        return True
    if ".dist/" in filename:
        return True
    if parts[-1] in ("incbin.h", "hedley.h"):
        return True

    if filename.endswith(".py"):
        for line in getFileContentByLine(filename):
            if "# encoding: nuitka-protection" in line:
                return True

            break

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


def autoFormatFile(
    filename,
    git_stage,
    check_only=False,
    effective_filename=None,
    trace=True,
    limit_yaml=False,
    limit_python=False,
    limit_c=False,
    limit_rst=False,
    ignore_errors=False,
):
    """Format source code with external tools

    Args:
        filename: str - filename to work on
        git_stage: bool - indicate if this is to be done on staged content
        abort: bool - error exit in case a tool shows a problem
        effective_filename: str - derive type of file from this name

    Notes:
        The effective filename can be used in case this is already a
        temporary filename intended to replace another.

    Returns:
        None
    """

    # This does a lot of distinctions
    # pylint: disable=too-many-branches,too-many-locals,too-many-return-statements,too-many-statements

    if effective_filename is None:
        effective_filename = filename

    if os.path.isdir(effective_filename):
        return

    filename = os.path.normpath(filename)
    effective_filename = os.path.normpath(effective_filename)

    is_python = isPythonFile(filename, effective_filename)

    is_c = effective_filename.endswith((".c", ".h"))
    is_cpp = effective_filename.endswith((".cpp", ".h"))

    is_txt = effective_filename.endswith(
        (
            ".patch",
            ".txt",
            ".qml",
            ".rst",
            ".sh",
            ".in",
            ".md",
            ".toml",
            ".asciidoc",
            ".nuspec",
            ".yml",
            ".stylesheet",
            ".j2",
            ".gitignore",
            ".gitattributes",
            ".gitmodules",
            ".json",
            ".spec",
            "-rpmlintrc",
            "Containerfile",
        )
    ) or os.path.basename(filename) in (
        "changelog",
        "compat",
        "control",
        "copyright",
        "lintian-overrides",
    )

    is_rst = effective_filename.endswith(".rst")
    is_package_config_yaml = effective_filename.endswith(".nuitka-package.config.yml")

    # Some parts of Nuitka must not be re-formatted with black or clang-format
    # as they have different intentions.
    if not (is_python or is_c or is_cpp or is_txt or is_rst):
        my_print("Ignored file type.")
        return

    if limit_yaml or limit_python or limit_c or limit_rst:
        if is_package_config_yaml and not limit_yaml:
            return

        if (is_c or is_cpp) and not limit_c:
            return

        if is_python and not limit_python:
            return

        if is_rst and not limit_rst:
            return

    # Work on a temporary copy
    tmp_filename = filename + ".tmp"

    if git_stage:
        old_code = getFileHashContent(git_stage["dst_hash"])
    else:
        old_code = getFileContents(filename, "rb")

    with withTemporaryFile(mode="wb", delete=False) as output_file:
        tmp_filename = output_file.name
        output_file.write(old_code)
        output_file.close()

        if is_python:
            cleanupWindowsNewlines(tmp_filename, effective_filename)

            if not _shouldNotFormatCode(effective_filename):
                _cleanupImportSortOrder(tmp_filename, effective_filename)
                _cleanupPyLintComments(tmp_filename, effective_filename)

                if effective_filename not in BLACK_SKIP_LIST:
                    black_call = _getPythonBinaryCall("black")

                    try:
                        check_call(black_call + ["-q", "--fast", tmp_filename])
                    except Exception:  # Catch all the things, pylint: disable=broad-except
                        tools_logger.warning(
                            "Problem formatting for '%s'." % effective_filename
                        )

                        if not ignore_errors:
                            raise

                cleanupWindowsNewlines(tmp_filename, effective_filename)

        elif is_c or is_cpp:
            if not _shouldNotFormatCode(effective_filename):
                cleanupWindowsNewlines(tmp_filename, effective_filename)
                _cleanupClangFormat(tmp_filename)
                cleanupWindowsNewlines(tmp_filename, effective_filename)
        elif is_txt:
            if not _shouldNotFormatCode(effective_filename):
                cleanupWindowsNewlines(tmp_filename, effective_filename)
                _cleanupTrailingWhitespace(tmp_filename)
                cleanupWindowsNewlines(tmp_filename, effective_filename)

                if is_rst:
                    _cleanupRstFmt(tmp_filename, effective_filename)

                if is_package_config_yaml:
                    formatYaml(tmp_filename)
                    cleanupWindowsNewlines(tmp_filename, effective_filename)
                    _cleanupTrailingWhitespace(tmp_filename)

        _transferBOM(filename, tmp_filename)

    changed = old_code != getFileContents(tmp_filename, "rb")

    if changed:
        if check_only:
            my_print("%s: FAIL." % filename, style="red")
        else:
            if trace:
                my_print("Updated %s." % filename)

            with withPreserveFileMode(filename):
                if git_stage:
                    new_hash_value = putFileHashContent(tmp_filename)
                    updateFileIndex(git_stage, new_hash_value)
                    updateWorkingFile(filename, git_stage["dst_hash"], new_hash_value)
                else:
                    copyFile(tmp_filename, filename)

    return changed


@contextlib.contextmanager
def withFileOpenedAndAutoFormatted(filename, ignore_errors=False):
    my_print("Auto-format '%s' ..." % filename)

    tmp_filename = filename + ".tmp"
    with openTextFile(tmp_filename, "w") as output:
        yield output

    autoFormatFile(
        filename=tmp_filename,
        git_stage=None,
        effective_filename=filename,
        trace=False,
        ignore_errors=ignore_errors,
    )

    # TODO: No idea why, but this helps. Would be nice to become able to remove it though.
    if os.name == "nt":
        autoFormatFile(
            filename=tmp_filename,
            git_stage=None,
            effective_filename=filename,
            trace=False,
            ignore_errors=ignore_errors,
        )

    shutil.copy(tmp_filename, filename)
    os.unlink(tmp_filename)
