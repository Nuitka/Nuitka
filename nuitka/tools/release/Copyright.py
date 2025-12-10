#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tools related to management of copyright headers and footers."""

import ast
import os

from nuitka.tools.quality.ScanSources import isPythonFile
from nuitka.utils.FileOperations import (
    getFileContentByLine,
    getFileContents,
    openTextFile,
)
from nuitka.Version import getNuitkaVersionYear

copyright_year = getNuitkaVersionYear()

# spell-checker: ignore Batakrishna,Jorj,Kierzkowski,Pawe,Sahu,Teske

copyright_holder = {
    "nuitka/plugins/standard/TkinterPlugin.py": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "nuitka/plugins/standard/NumpyPlugin.py": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "nuitka/plugins/standard/GeventPlugin.py": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "nuitka/plugins/standard/TensorflowPlugin.py": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "nuitka/plugins/standard/SklearnPlugin.py": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "nuitka/plugins/standard/PbrPlugin.py": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "nuitka/plugins/standard/TorchPlugin.py": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "nuitka/plugins/standard/EventletPlugin.py": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "nuitka/plugins/standard//OptionsNannyPlugin.py": "Fire-Cube <ben7@gmx.ch>",
    "nuitka/plugins/standard/PlaywrightPlugin.py": "Kevin Rodriguez <mailto:turcioskevinr@gmail.com>",
    "tests/standalone/SocketUsing.py": "Pawe\u0142 Kierzkowski, mailto:<pk.pawelo@gmail.com>",
    "nuitka/nodes/BuiltinAnyNodes.py": "Batakrishna Sahu, mailto:<Batakrishna.Sahu@suiit.ac.in>",
    "nuitka/nodes/BuiltinAllNodes.py": "Batakrishna Sahu, mailto:<Batakrishna.Sahu@suiit.ac.in>",
    "nuitka/nodes/IterationHandles.py": "Batakrishna Sahu, mailto:<Batakrishna.Sahu@suiit.ac.in>",
    "doc/custom.css": "Batakrishna Sahu, mailto:<Batakrishna.Sahu@suiit.ac.in>",
    "doc/py-file.bat": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "doc/py-file.sh": "Jorj McKie, mailto:<jorj.x.mckie@outlook.de>",
    "tests/PyPI-pytest/run_all.py": "Tommy Li, mailto:<tommyli3318@gmail.com>",
    "tests/distutils/nested_namespaces/a/b/pkg/__init__.py": "Jan Teske, mailto:<jteske@posteo.net>",
    "tests/distutils/nested_namespaces/setup.py": "Jan Teske, mailto:<jteske@posteo.net>",
    "nuitka/tools/quality/auto_format/YamlFormatter.py": "Fire-Cube <ben7@gmx.ch>",
}

# Files that have no suffix, but should be commented anyway, spell-checker: ignore restlint
_plain_files = (
    "Python",
    "compare_with_cpython",
    "compare_with_xml",
    "check-nuitka-with-pylint",
    "check-nuitka-with-pylint3",
    "measure-construct-performance",
    "check-nuitka-with-restlint",
    "check-nuitka-with-yamllint",
    "check-nuitka-with-codespell",
    "check-reference-counts",
    "autoformat-nuitka-source",
    "nuitka-linux-container",
    "generate-specialized-c-code",
    "generate-specialized-python-code",
    "sort-nuitka-import-statements",
    "find_sxs_modules",
    "find-module",
    "nuitka",
    ".sourcery.yaml",
    "nuitka-watch",
    "nuitka-run",
    "nuitka2",
    "nuitka2-run",
    "nuitka-decrypt",
    "run-tests",
    "run-inside-nuitka-container",
    "custom.css",
    "pre-commit",
    "Containerfile",
    "requirements.txt",
    "requirements-commercial.txt",
    "commercial.nuitka-package.config.yml",
    "runner",
)


def isPlainFileWithCopyright(filename):
    return os.path.basename(filename) in _plain_files


def getCopyrightClaim(filename, claim):
    r = [
        (
            "    Copyright %s, %s"
            % (
                copyright_year,
                copyright_holder.get(
                    filename.replace(os.path.sep, "/"),
                    "Kay Hayen, mailto:kay.hayen@gmail.com",
                ),
            )
        ).encode("utf8"),
        b"",
    ] + claim

    return r


def _formatComments(filename, comments):
    # All cases in one, pylint: disable=too-many-branches

    assert all(type(comment) is bytes for comment in comments), comments
    assert not any(b"\n" in comment for comment in comments), comments

    if not comments:
        return comments

    if filename.endswith(".css"):
        comments.insert(0, b"/" + b"*" * 70)
        comments.append(b"/" + b"*" * 70)
    elif filename.endswith(
        (
            ".py",
            ".sh",
            ".scons",
            ".template",
            ".yml",
            ".cfg",
            ".toml",
            ".containerfile",
        )
    ) or isPlainFileWithCopyright(filename):
        comments = [
            (b"# %s" % comment if comment != b"" else b"#") for comment in comments
        ]
    elif filename.endswith(".puml"):
        comments = [
            (b"' %s" % comment if comment != b"" else b"'") for comment in comments
        ]
    elif filename.endswith((".c", ".cpp", ".h", ".S", ".qml")):
        comments = [
            (b"// %s" % comment if comment != b"" else b"//") for comment in comments
        ]
    elif filename.endswith((".cmd", ".bat")):
        comments = [
            (b"rem %s" % comment if comment != b"" else b"rem") for comment in comments
        ]
    elif filename.endswith(".j2"):
        comments = [(b"{# %-76s #}" % comment) for comment in comments]
    elif (
        filename.endswith(".txt")
        and "tests/commercial" in filename
        or "LICENSE" in filename
    ):
        comments = []
    elif filename.endswith(".rst"):
        comments = []
    elif filename.endswith(".md"):
        comments = []
    elif filename.endswith(".json"):
        comments = []
    elif filename.endswith(".svg"):
        comments = []
    elif filename.endswith(".png"):
        comments = []
    elif filename.endswith(".zip"):
        comments = []
    else:
        assert False, filename

    return comments


def attachLeadingComment(filename, effective_filename, comments, replacements=()):
    # Many details and complicated algorithm, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    old_lines = getFileContents(filename, mode="rb").splitlines()

    if old_lines and old_lines[0].startswith(b"\xef\xbb\xbf"):
        old_lines[0] = old_lines[0][3:]
        bom = True
    else:
        bom = False

    if comments and os.path.basename(effective_filename) != os.path.basename(__file__):
        assert b'Part of "Nuitka"' not in b"".join(old_lines), filename

    if comments and comments[1] == b"" and any(line.strip() for line in old_lines):
        pre_comments = comments[:1]
        pre_comments[0] += b" find license text at end of file"
        post_comments = comments[2:]

        while post_comments[-1].strip() in (b"", b"#"):
            del post_comments[-1]
    else:
        pre_comments = comments
        post_comments = []

        if not any(line.strip() for line in old_lines):
            while pre_comments[-1].strip() in (b"", b"#"):
                del pre_comments[-1]

    del comments

    pre_comments = _formatComments(effective_filename, pre_comments)
    post_comments = _formatComments(effective_filename, post_comments)

    is_python = isPythonFile(filename=filename, effective_filename=effective_filename)

    # Do what black will do otherwise
    if pre_comments:
        if is_python:
            pre_comments.append(b"")

    if post_comments:
        post_comments.insert(0, b"")

        if is_python:
            for line in reversed(old_lines):
                if line.startswith((b"def ", b"class ")):
                    bottom_function = True
                    break
                if line.strip() and not chr(line[0]).isalnum():
                    bottom_function = False
                    break
            else:
                bottom_function = False

            if not bottom_function:
                try:
                    last_node = ast.parse(b"\n".join(old_lines)).body[-1]
                except (SyntaxError, IndexError):
                    pass
                else:
                    if type(last_node) is ast.If:
                        # ast API, spell-checker: ignore orelse
                        last_node = (
                            last_node.orelse[-1]
                            if last_node.orelse
                            else last_node.body[-1]
                        )

                    bottom_function = type(last_node) in (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                    )

            if bottom_function:
                post_comments.insert(0, b"")

    if old_lines and (
        old_lines[0].startswith(b"#!")
        or old_lines[0].startswith(b"# -*-")
        or old_lines[0].startswith(b"@echo")
        or old_lines[0].startswith(b"# coding:")
        or old_lines[0].startswith(b"# encoding:")
    ):
        old_lines_head = old_lines[0:1]
        old_lines = old_lines[1:]
    else:
        old_lines_head = []

    if pre_comments:
        while old_lines and old_lines[0].strip() in (b"", b"#"):
            del old_lines[0]
        old_lines.insert(0, b"")

    lines = old_lines_head + pre_comments + old_lines + post_comments

    if bom:
        lines[0] = b"\xef\xbb\xbf" + lines[0]

    def replace(line):
        for src, dest in replacements:
            line = line.replace(src, dest)

        return line

    lines = [replace(line) for line in lines]

    if is_python:
        while lines and not lines[-1].strip():
            del lines[-1]

    new_line = b"\r\n" if effective_filename.endswith(".cmd") else b"\n"

    with openTextFile(filename, "wb") as output:
        output.writelines(line + new_line for line in lines)


_copyright_claim_standard = []


def getLicenseTextStandard():
    if not _copyright_claim_standard:
        inside = False

        for line in getFileContentByLine(
            os.path.join(os.path.dirname(__file__), "../../../debian/copyright")
        ):
            if line.startswith("License:"):
                inside = True
                continue

            if not inside:
                continue

            if not line.startswith(" "):
                break

            line = line[1:]

            if line == ".":
                line = ""
            else:
                line = "    " + line

            if "On Debian GNU/Linux systems" in line:
                break

            _copyright_claim_standard.append(line.encode("utf8"))

        while not _copyright_claim_standard[-1].strip():
            del _copyright_claim_standard[-1]

    return _copyright_claim_standard


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
