#!/usr/bin/env python
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tool to automatically format source code in Nuitka style."""

import contextlib
import os
import shutil

from nuitka.format.BiomeFormatter import formatJsonFile
from nuitka.format.FileFormatting import (
    cleanupTrailingWhitespace,
    cleanupWindowsNewlines,
    formatC,
)
from nuitka.format.PythonFormatting import formatPython
from nuitka.format.YamlChecker import checkYamlSchema
from nuitka.format.YamlFormatter import formatYaml
from nuitka.tools.quality.Git import (
    getFileHashContent,
    putFileHashContent,
    updateFileIndex,
    updateGitFile,
)
from nuitka.tools.quality.ScanSources import isPythonFile
from nuitka.tools.release.Documentation import extra_rst_keywords
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.Execution import check_call, getExecutablePath
from nuitka.utils.FileOperations import (
    deleteFile,
    getFileContentByLine,
    getFileContents,
    getFilenameExtension,
    openTextFile,
    withPreserveFileMode,
    withTemporaryFile,
)
from nuitka.utils.PrivatePipSpace import (
    getMdformatBinaryPath,
    getRstfmtBinaryPath,
    withPrivatePipSitePackagesPathAdded,
)


def _shouldNotFormatCode(filename, effective_filename):
    """Check if a file should not be formatted."""
    # pylint: disable=too-many-return-statements

    parts = os.path.normpath(effective_filename).split(os.path.sep)

    if "inline_copy" in parts:
        if os.path.basename(effective_filename) == "scons.py":
            return False

        return True
    if "pybench" in parts:  # spell-checker: ignore pybench
        return True
    if "mercurial" in parts:
        return True
    if "tests" in parts and parts[parts.index("tests") + 1].startswith("CPython"):
        return True
    if "tests" in parts and "syntax" in parts:
        return True
    if ".dist/" in effective_filename:
        return True
    if os.path.basename(effective_filename) in ("incbin.h", "hedley.h"):
        return True

    if effective_filename.endswith(".py") and os.path.exists(filename):
        for line in getFileContentByLine(filename, encoding="utf8"):
            if "# encoding: nuitka-protection" in line:
                return True

            break

    return False


def _transferBOM(source_filename, target_filename):
    """Transfer Byte Order Mark (BOM) from source to target file."""
    with open(source_filename, "rb") as f:
        source_code = f.read()

    if source_code.startswith(b"\xef\xbb\xbf"):
        with open(target_filename, "rb") as f:
            source_code = f.read()

        if not source_code.startswith(b"\xef\xbb\xbf"):
            with open(target_filename, "wb") as f:
                f.write(b"\xef\xbb\xbf")
                f.write(source_code)


def cleanupMarkdownFmt(logger, filename, assume_yes_for_downloads):
    """Cleanup markdown formatting using mdformat.

    Args:
        filename: path to the file
        logger: logger to use
        assume_yes_for_downloads: bool
    """

    mdformat_path = getMdformatBinaryPath(
        logger=logger, assume_yes_for_downloads=assume_yes_for_downloads
    )

    if mdformat_path is None:
        if logger is not None:
            logger.warning("Need to accept mdformat download to format markdown files.")
        return

    with withPrivatePipSitePackagesPathAdded(logger=logger):
        check_call([mdformat_path, "--number", "--wrap=100", filename])


def cleanupRstFmt(logger, filename, effective_filename, assume_yes_for_downloads):
    """Cleanup reStructuredText formatting using rstfmt.

    Args:
        filename: path to the file
        effective_filename: filename to use for errors
        logger: logger to use
        assume_yes_for_downloads: bool
    """
    updated_contents = contents = getFileContents(filename, mode="rb")

    for keyword in extra_rst_keywords:
        updated_contents = updated_contents.replace(
            b".. %s::" % keyword, b".. raw:: %s" % keyword
        )

    if updated_contents != contents:
        with open(filename, "wb") as out_file:
            out_file.write(updated_contents)

    rstfmt_path = getRstfmtBinaryPath(
        logger=logger, assume_yes_for_downloads=assume_yes_for_downloads
    )

    if rstfmt_path is None:
        if logger is not None:
            logger.warning("Need to accept rstfmt download to format RST files.")
        return

    with withPrivatePipSitePackagesPathAdded(logger=logger):
        check_call([rstfmt_path, filename])

    cleanupWindowsNewlines(filename, effective_filename)

    contents = getFileContents(filename, mode="rb")

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


def cleanupPngImage(filename, logger):
    """Cleanup PNG image using optipng.

    Args:
        filename: path to the file
        logger: logger to use
    """
    _optipng_path = getExecutablePath("optipng")

    if _optipng_path:
        check_call([_optipng_path, "-o7", "-zm1-9", filename])
    elif logger is not None:
        logger.warning("Cannot find 'optipng' binary to compress PNG image")


def cleanupJpegImage(filename, logger):
    """Cleanup JPEG image using jpegoptim.

    Args:
        filename: path to the file
        logger: logger to use
    """
    # spell-checker: ignore jpegoptim
    _jpegoptim_path = getExecutablePath("jpegoptim")

    if _jpegoptim_path:
        check_call([_jpegoptim_path, filename])
    elif logger is not None:
        logger.warning("Cannot find 'jpegoptim' binary to compress JPEG image")


def formatText(
    logger,
    filename,
    effective_filename,
    ignore_yaml_diff=True,
    assume_yes_for_downloads=False,
):
    """Format text-like files (RST, MD, YAML, etc.).

    Args:
        filename: path to the file
        effective_filename: filename to use for errors
        logger: logger to use
        ignore_yaml_diff: bool - if YAML diffs should be ignored
        assume_yes_for_downloads: bool - if tools should be downloaded automatically
    """
    is_rst = effective_filename.endswith((".rst", ".inc"))
    is_md = (
        effective_filename.endswith(".md")
        or os.path.basename(effective_filename) == ".cursorrules"
    )
    is_package_config_yaml = effective_filename.endswith(".nuitka-package.config.yml")

    cleanupWindowsNewlines(filename, effective_filename)
    cleanupTrailingWhitespace(filename)
    cleanupWindowsNewlines(filename, effective_filename)

    if is_rst:
        cleanupRstFmt(
            logger=logger,
            filename=filename,
            effective_filename=effective_filename,
            assume_yes_for_downloads=assume_yes_for_downloads,
        )

    if is_md:
        cleanupMarkdownFmt(
            logger=logger,
            filename=filename,
            assume_yes_for_downloads=assume_yes_for_downloads,
        )

    if is_package_config_yaml:
        formatYaml(
            logger=logger,
            path=filename,
            assume_yes_for_downloads=assume_yes_for_downloads,
            ignore_diff=ignore_yaml_diff,
        )
        cleanupWindowsNewlines(filename, effective_filename)
        cleanupTrailingWhitespace(filename)
        checkYamlSchema(
            logger=logger,
            filename=filename,
            effective_filename=effective_filename,
            update=True,
        )
        formatYaml(
            logger=logger,
            path=filename,
            assume_yes_for_downloads=assume_yes_for_downloads,
            ignore_diff=ignore_yaml_diff,
        )
        cleanupWindowsNewlines(filename, effective_filename)
        cleanupTrailingWhitespace(filename)


def formatImage(filename, logger):
    """Format image files (PNG, JPEG).

    Args:
        filename: path to the file
        logger: logger to use
    """
    if filename.endswith(".png"):
        cleanupPngImage(filename, logger=logger)
    else:
        cleanupJpegImage(filename, logger=logger)


def formatJson(filename, assume_yes_for_downloads):
    """Format JSON files."""
    formatJsonFile(filename, assume_yes_for_downloads=assume_yes_for_downloads)
    cleanupTrailingWhitespace(filename)


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
    limit_md=False,
    limit_json=False,
    ignore_errors=False,
    ignore_yaml_diff=True,
    assume_yes_for_downloads=False,
):
    """Format source code with external tools.

    Args:
        filename: str - filename to work on
        git_stage: bool - indicate if this is to be done on staged content
        check_only: bool - indicate if only checking is to be done
        effective_filename: str - derive type of file from this name
        trace: bool - indicate if progress should be traced
        limit_yaml: bool - limit to YAML files
        limit_python: bool - limit to Python files
        limit_c: bool - limit to C files
        limit_rst: bool - limit to RST files
        limit_md: bool - limit to MD files
        limit_json: bool - limit to JSON files
        ignore_errors: bool - ignore errors during formatting
        ignore_yaml_diff: bool - ignore diffs in YAML files
        assume_yes_for_downloads: bool - assume yes for tool downloads

    Returns:
        bool: True if changes were made (or if check failed), False otherwise.
    """

    # pylint: disable=too-many-arguments,too-many-branches,too-many-locals,too-many-statements

    if effective_filename is None:
        effective_filename = filename

    if os.path.isdir(effective_filename):
        return False

    if git_stage:
        old_code = getFileHashContent(git_stage["dst_hash"])
    else:
        old_code = getFileContents(filename, "rb")

    changed = False

    with withTemporaryFile(
        mode="wb", delete=False, suffix=getFilenameExtension(filename)
    ) as output_file:
        tmp_filename = output_file.name
        output_file.write(old_code)
        output_file.close()

        is_c = effective_filename.endswith((".c", ".h"))
        is_cpp = effective_filename.endswith((".cpp", ".h"))
        is_json = effective_filename.endswith(".json")
        is_png = effective_filename.endswith(".png")
        is_jpeg = effective_filename.endswith((".jpeg", ".jpg"))

        is_python = not (
            is_c or is_cpp or is_json or is_png or is_jpeg
        ) and isPythonFile(filename=tmp_filename, effective_filename=effective_filename)

        if not (is_python or is_c or is_cpp or is_json or is_png or is_jpeg):
            # Text check
            is_txt = effective_filename.endswith(
                (
                    ".patch",
                    ".txt",
                    ".qml",
                    ".rst",
                    ".inc",
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
                    ".spec",
                    "-rpmlintrc",
                    # spell-checker: ignore rpmlintrc
                    "Containerfile",
                    ".containerfile",
                    ".containerfile.in",
                    ".1",
                    ".pth",
                )
            ) or os.path.basename(filename) in (
                "changelog",
                "compat",
                "control",
                "copyright",
                "lintian-overrides",
                ".cursorrules",
            )
        else:
            is_txt = False

        if limit_yaml or limit_python or limit_c or limit_rst or limit_md or limit_json:
            if (
                effective_filename.endswith(".nuitka-package.config.yml")
                and not limit_yaml
            ):
                is_python = is_c = is_cpp = is_txt = is_json = is_png = is_jpeg = False
            elif (is_c or is_cpp) and not limit_c:
                is_python = is_c = is_cpp = is_txt = is_json = is_png = is_jpeg = False
            elif is_python and not limit_python:
                is_python = is_c = is_cpp = is_txt = is_json = is_png = is_jpeg = False
            elif effective_filename.endswith((".rst", ".inc")) and not limit_rst:
                is_python = is_c = is_cpp = is_txt = is_json = is_png = is_jpeg = False
            elif (
                effective_filename.endswith(".md")
                or os.path.basename(effective_filename) == ".cursorrules"
            ) and not limit_md:
                is_python = is_c = is_cpp = is_txt = is_json = is_png = is_jpeg = False
            elif is_json and not limit_json:
                is_python = is_c = is_cpp = is_txt = is_json = is_png = is_jpeg = False

        if not (is_python or is_c or is_cpp or is_txt or is_json or is_png or is_jpeg):
            deleteFile(tmp_filename, must_exist=True)
            return False

        if is_python:
            if not _shouldNotFormatCode(
                filename=tmp_filename, effective_filename=effective_filename
            ):
                formatPython(
                    logger=tools_logger,
                    filename=tmp_filename,
                    effective_filename=effective_filename,
                    ignore_errors=ignore_errors,
                    assume_yes_for_downloads=assume_yes_for_downloads,
                )
        elif is_c or is_cpp:
            if not _shouldNotFormatCode(
                filename=tmp_filename, effective_filename=effective_filename
            ):
                formatC(
                    logger=tools_logger,
                    filename=tmp_filename,
                    effective_filename=effective_filename,
                    check_only=check_only,
                    assume_yes_for_downloads=assume_yes_for_downloads,
                    reject_message="Formatting C files needs 'clang-format'.",
                )
        elif is_txt:
            if not _shouldNotFormatCode(
                filename=tmp_filename, effective_filename=effective_filename
            ):
                formatText(
                    logger=tools_logger,
                    filename=tmp_filename,
                    effective_filename=effective_filename,
                    ignore_yaml_diff=ignore_yaml_diff,
                    assume_yes_for_downloads=assume_yes_for_downloads,
                )
        elif is_json:
            formatJson(tmp_filename, assume_yes_for_downloads=assume_yes_for_downloads)
        elif is_png or is_jpeg:
            formatImage(tmp_filename, logger=tools_logger)

        if is_python:
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
                        updateGitFile(
                            filename, git_stage["dst_hash"], new_hash_value, staged=True
                        )
                    else:
                        shutil.copy(tmp_filename, filename)

    deleteFile(tmp_filename, must_exist=True)

    return changed


@contextlib.contextmanager
def withFileOpenedAndAutoFormatted(filename, ignore_errors=False):
    """Context manager for opening a file and auto-formatting it on close.

    Args:
        filename: path to the file
        ignore_errors: bool - if errors should be ignored
    """

    tmp_filename = filename + ".tmp"

    try:
        with openTextFile(tmp_filename, "w") as output:
            yield output

        autoFormatFile(
            filename=tmp_filename,
            git_stage=False,
            effective_filename=filename,
            trace=False,
            ignore_errors=ignore_errors,
            assume_yes_for_downloads=True,
        )

        if os.name == "nt":
            autoFormatFile(
                filename=tmp_filename,
                git_stage=False,
                effective_filename=filename,
                trace=False,
                ignore_errors=ignore_errors,
                assume_yes_for_downloads=True,
            )

        if not os.path.exists(filename) or getFileContents(
            tmp_filename, mode="rb"
        ) != getFileContents(filename, mode="rb"):
            with withPreserveFileMode(filename):
                shutil.copy(tmp_filename, filename)
    finally:
        deleteFile(tmp_filename, must_exist=False)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
