#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Functions to handle git staged content.

Inspired from https://raw.githubusercontent.com/hallettj/git-format-staged/master/git-format-staged
Original author: Jesse Hallett <jesse@sitr.us>

spell-checker: ignore Hallett,unpushed
"""

import os
import re
import subprocess

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
from nuitka.utils.Utils import decoratorRetries


def _getGitCommandOutput(command, stdin=None):
    """Get the output of a git command as text.

    Args:
        command: list of command arguments, including the 'git' executable.
        stdin: optional file object to connect to the standard input.

    Returns:
        Output of the command decoded to text.
    """
    output = check_output(command, stdin=stdin)

    if str is not bytes:
        output = output.decode("utf8")

    return output


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

    for line in _getGitCommandOutput(command).splitlines():
        yield _parseIndexDiffLine(line)


def getModifiedPaths():
    """Get a list of all modified paths in the repository."""
    result = set()

    for command in (
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
    ):
        result.update(_getGitCommandOutput(command).splitlines())

    return tuple(sorted(filename for filename in result if os.path.exists(filename)))


def getRemoteURL(remote_name):
    """Get the URL of a git remote."""
    return _getGitCommandOutput(["git", "remote", "get-url", remote_name]).strip()


def getCurrentBranchName():
    """Get the name of the current git branch."""
    try:
        return _getGitCommandOutput(["git", "branch", "--show-current"]).strip()
    except NuitkaCalledProcessError:
        return _getGitCommandOutput(["git", "symbolic-ref", "--short", "HEAD"]).strip()


def getDefaultBranchName():
    """Get the name of the default branch of the repository.

    Notes:
        The remote default branch is preferred over local branch names, as it
        is the reference that pushes are made against.

    Returns:
        Name of the default branch, or 'None' if none was found.
    """
    try:
        return _getGitCommandOutput(
            ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"]
        ).strip()
    except NuitkaCalledProcessError:
        pass

    for branch_name in ("origin/develop", "origin/main", "develop", "main"):
        try:
            _getGitCommandOutput(["git", "rev-parse", "--verify", branch_name])
        except NuitkaCalledProcessError:
            continue
        else:
            return branch_name

    return None


def _getChangedPathsForRef(git_ref):
    """Get the changed paths of `git diff` against a git reference."""
    result = set()

    for line in _getGitCommandOutput(
        [
            "git",
            "diff",
            "--stat",
            "--name-only",
            "--ignore-submodules=all",
            git_ref,
        ]
    ).splitlines():
        # Removed files appear too, but are useless to talk about.
        if not os.path.exists(line):
            continue

        result.add(line)

    return tuple(sorted(result))


def getNotPushedPaths():
    """Get a list of modified paths that have not been pushed to upstream."""
    try:
        return _getChangedPathsForRef("@{upstream}")
    except NuitkaCalledProcessError:
        # Local branches without an upstream, e.g. branches that were never
        # pushed, are compared against the default branch instead, starting
        # at the merge base, so that changes only made there are not included.
        default_branch_name = getDefaultBranchName()

        if default_branch_name is None:
            return ()

        try:
            merge_base = _getGitCommandOutput(
                ["git", "merge-base", "HEAD", default_branch_name]
            )
        except NuitkaCalledProcessError:
            return ()

        branch_name = getCurrentBranchName()

        if branch_name:
            tools_logger.info(
                "No upstream branch configured for '%s', comparing against '%s'."
                % (branch_name, default_branch_name)
            )
        else:
            tools_logger.info(
                "No upstream branch configured, comparing against '%s'."
                % default_branch_name
            )

        return _getChangedPathsForRef(merge_base.strip())


def getFileHashContent(object_hash):
    """Get the content of a git object from its hash."""
    return check_output(["git", "cat-file", "-p", object_hash])


def putFileHashContent(filename):
    """Add a file's content to the git object database and return its hash."""
    with openTextFile(filename, "r") as input_file:
        new_hash = _getGitCommandOutput(
            ["git", "hash-object", "-w", "--stdin"], stdin=input_file
        )

    assert new_hash
    return new_hash.rstrip()


@decoratorRetries(
    logger=tools_logger,
    purpose="update git index",
    consequence="Autostaging of compilation report may not take effect.",
    attempts=3,
    exception_type=(OSError, subprocess.CalledProcessError),
    sleep_time=1,
)
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
    process_result = executeProcess(
        command,
        stdin=patch,
    )

    if process_result.exit_code != 0 and os.name == "nt":
        cleanupWindowsNewlines(path, path)

        process_result = executeProcess(
            ["git", "apply", "-"],
            stdin=patch,
        )

    success = process_result.exit_code == 0

    if not success:
        if process_result.stdout:
            my_print(process_result.stdout, style="yellow")
        if process_result.stderr:
            my_print(process_result.stderr, style="yellow")

        return tools_logger.sysexit(
            "Patch failed to apply for %r:\n\n%r\n%s" % (path, patch, "-" * 40)
        )

    return success


def addGitArguments(parser, verb="Analyze"):
    parser.add_option(
        "--diff",
        action="store_true",
        dest="diff",
        default=False,
        help="""\
%s the changed files in git checkout. Default is %%default.""" % verb,
    )

    parser.add_option(
        "--un-pushed",
        "--unpushed",
        action="store_true",
        dest="un_pushed",
        default=False,
        help="""\
%s the changed files in git not yet pushed, or for branches without an
upstream, the changed files compared to the default branch.
Default is %%default.""" % verb,
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
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
