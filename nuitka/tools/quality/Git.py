#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Functions to handle git staged content.

Inspired from https://raw.githubusercontent.com/hallettj/git-format-staged/master/git-format-staged
Original author: Jesse Hallett <jesse@sitr.us>

spell-checker: ignore Hallett,unpushed
"""

import os
import re

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.format.FileFormatting import cleanupWindowsNewlines
from nuitka.tools.Basics import goHome
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.CStrings import decodeCStringToPython
from nuitka.utils.Execution import (
    NuitkaCalledProcessError,
    check_call,
    check_output,
    executeProcess,
)
from nuitka.utils.FileOperations import openTextFile


# Parse output from `git diff-index`
def _parseIndexDiffLine(line):
    """Parse output from `git diff-index` into a dictionary."""
    pattern = re.compile(
        r"^:(\d+) (\d+) ([a-f0-9]+) ([a-f0-9]+) ([A-Z])(\d+)?\t([^\t]+)(?:\t([^\t]+))?$"
    )

    zeroed_pat = re.compile("^0+$")

    # Returns the argument unless the argument is a string of zeroes, in which case
    # returns `None`
    def unless_zeroed(s):
        return s if not zeroed_pat.match(s) else None

    match = pattern.match(line)
    if not match:
        raise ValueError("Failed to parse diff-index line: " + line)

    def parseGitPath(value):
        if value is None:
            return None

        if value.startswith('"'):
            return decodeCStringToPython(value).decode("utf8")

        return value

    return {
        "src_mode": unless_zeroed(match.group(1)),
        "dst_mode": unless_zeroed(match.group(2)),
        "src_hash": unless_zeroed(match.group(3)),
        "dst_hash": unless_zeroed(match.group(4)),
        "status": match.group(5),
        "score": int(match.group(6)) if match.group(6) else None,
        "src_path": parseGitPath(match.group(7)),
        "dst_path": parseGitPath(match.group(8)),
    }


def getCheckoutFileChangeDesc(staged):
    """Get descriptions of changed files in the checkout.

    Args:
        staged: bool - if True, look at staged changes (--cached),
                       otherwise look at unstaged changes.
    """
    # Only file additions and modifications
    command = ["git", "diff-index", "--diff-filter=AM", "--no-renames"]

    if staged:
        command.append("--cached")

    command.append("HEAD")

    output = check_output(command)

    for line in output.splitlines():
        if str is not bytes:
            line = line.decode("utf8")

        yield _parseIndexDiffLine(line)


def getModifiedPaths():
    """Get a list of all modified paths in the repository."""
    result = set()

    output = check_output(["git", "diff", "--name-only"])

    for line in output.splitlines():
        if str is not bytes:
            line = line.decode("utf8")

        result.add(line)

    output = check_output(["git", "diff", "--cached", "--name-only"])

    for line in output.splitlines():
        if str is not bytes:
            line = line.decode("utf8")

        result.add(line)

    return tuple(sorted(filename for filename in result if os.path.exists(filename)))


def getRemoteURL(remote_name):
    """Get the URL of a git remote."""
    output = check_output(["git", "remote", "get-url", remote_name])

    if str is not bytes:
        output = output.decode("utf8")

    return output.strip()


def getCurrentBranchName():
    """Get the name of the current git branch."""
    try:
        output = check_output(["git", "branch", "--show-current"])
    except NuitkaCalledProcessError:
        output = check_output(["git", "symbolic-ref", "--short", "HEAD"])

    if str is not bytes:
        output = output.decode("utf8")

    return output.strip()


def getNotPushedPaths():
    """Get a list of modified paths that have not been pushed to upstream."""
    result = set()

    try:
        output = check_output(["git", "diff", "--stat", "--name-only", "@{upstream}"])
    except NuitkaCalledProcessError:
        return result

    for line in output.splitlines():
        if str is not bytes:
            line = line.decode("utf8")

        # Removed files appear too, but are useless to talk about.
        if not os.path.exists(line):
            continue

        result.add(line)

    return tuple(sorted(result))


def getFileHashContent(object_hash):
    """Get the content of a git object from its hash."""
    return check_output(["git", "cat-file", "-p", object_hash])


def putFileHashContent(filename):
    """Add a file's content to the git object database and return its hash."""
    with openTextFile(filename, "r") as input_file:
        new_hash = check_output(
            ["git", "hash-object", "-w", "--stdin"], stdin=input_file
        )

    if str is not bytes:
        new_hash = new_hash.decode("utf8")

    assert new_hash
    return new_hash.rstrip()


def updateFileIndex(diff_entry, new_object_hash):
    """Update the git index with a new hash for a file."""
    # spell-checker: ignore cacheinfo
    check_call(
        [
            "git",
            "update-index",
            "--cacheinfo",
            "%s,%s,%s"
            % (diff_entry["dst_mode"], new_object_hash, diff_entry["src_path"]),
        ]
    )


def updateGitFile(path, orig_object_hash, new_object_hash, staged):
    """Apply a patch to a file in the git repository.

    Args:
        path: str - path to the file
        orig_object_hash: str - original hash of the file
        new_object_hash: str - new hash of the file
        staged: bool - if True, apply as a staged change
    """
    patch = check_output(
        ["git", "diff", "--no-color", orig_object_hash, new_object_hash]
    )

    git_path = path.replace(os.path.sep, "/").encode("utf8")

    def updateLine(line):
        if line.startswith(b"diff --git"):
            line = b"diff --git a/%s b/%s" % (git_path, git_path)
        elif line.startswith(b"--- a/"):
            line = b"--- a/" + git_path
        elif line.startswith(b"+++ b/"):
            line = b"+++ b/" + git_path

        return line

    # Substitute object hashes in patch header with path to working tree file
    patch = b"\n".join(updateLine(line) for line in patch.splitlines()) + b"\n"

    command = ["git", "apply"]

    if not staged:
        command.append("--cached")

    command.append("-")

    # Apply the patch.
    output, err, exit_code = executeProcess(
        command,
        stdin=patch,
    )

    if exit_code != 0 and os.name == "nt":
        cleanupWindowsNewlines(path, path)

        output, err, exit_code = executeProcess(
            ["git", "apply", "-"],
            stdin=patch,
        )

    success = exit_code == 0

    if not success:
        # TODO: In case of failure, do we need to abort, or what do we do.

        if output:
            my_print(output, style="yellow")
        if err:
            my_print(err, style="yellow")

    return success


def addGitArguments(parser, verb="Analyze"):
    parser.add_option(
        "--diff",
        action="store_true",
        dest="diff",
        default=False,
        help="""\
%s the changed files in git checkout. Default is %%default."""
        % verb,
    )

    parser.add_option(
        "--un-pushed",
        "--unpushed",
        action="store_true",
        dest="un_pushed",
        default=False,
        help="""\
%s the changed files in git not yet pushed. Default is %%default."""
        % verb,
    )


def getGitPaths(options, positional_args, default_positional_args):
    if options.diff or options.un_pushed:
        if positional_args:
            tools_logger.sysexit(
                "Error, no filenames argument allowed in git diff mode."
            )

        goHome()

        result = OrderedSet()
        if options.diff:
            result.update(getModifiedPaths())

        if options.un_pushed:
            result.update(getNotPushedPaths())
    else:
        result = positional_args

        if not result:
            goHome()
            result = default_positional_args

    return result


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
