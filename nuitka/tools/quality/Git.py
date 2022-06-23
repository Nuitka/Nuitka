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
""" Functions to handle git staged content.

Inspired from https://raw.githubusercontent.com/hallettj/git-format-staged/master/git-format-staged

Original author: Jesse Hallett <jesse@sitr.us>

"""


import os
import re

from nuitka.Tracing import my_print
from nuitka.utils.Execution import (
    NuitkaCalledProcessError,
    check_call,
    check_output,
    executeProcess,
)
from nuitka.utils.FileOperations import openTextFile


# Parse output from `git diff-index`
def _parseIndexDiffLine(line):
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

    return {
        "src_mode": unless_zeroed(match.group(1)),
        "dst_mode": unless_zeroed(match.group(2)),
        "src_hash": unless_zeroed(match.group(3)),
        "dst_hash": unless_zeroed(match.group(4)),
        "status": match.group(5),
        "score": int(match.group(6)) if match.group(6) else None,
        "src_path": match.group(7),
        "dst_path": match.group(8),
    }


def getStagedFileChangeDesc():
    # Only file additions and modifications
    output = check_output(
        ["git", "diff-index", "--cached", "--diff-filter=AM", "--no-renames", "HEAD"]
    )

    for line in output.splitlines():
        if str is not bytes:
            line = line.decode("utf8")

        yield _parseIndexDiffLine(line)


def getModifiedPaths():
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

    return tuple(sorted(result))


def getUnpushedPaths():
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
    return check_output(["git", "cat-file", "-p", object_hash])


def putFileHashContent(filename):
    with openTextFile(filename, "r") as input_file:
        new_hash = check_output(
            ["git", "hash-object", "-w", "--stdin"], stdin=input_file
        )

    if str is not bytes:
        new_hash = new_hash.decode("utf8")

    assert new_hash
    return new_hash.rstrip()


def updateFileIndex(diff_entry, new_object_hash):
    check_call(
        [
            "git",
            "update-index",
            "--cacheinfo",
            "%s,%s,%s"
            % (diff_entry["dst_mode"], new_object_hash, diff_entry["src_path"]),
        ]
    )


def updateWorkingFile(path, orig_object_hash, new_object_hash):
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

    # Apply the patch.
    output, err, exit_code = executeProcess(
        ["git", "apply", "-"],
        stdin=patch,
    )

    # Windows extra ball, new files have new lines that make the patch fail.
    if exit_code != 0 and os.name == "nt":
        from .auto_format.AutoFormat import cleanupWindowsNewlines

        cleanupWindowsNewlines(path)

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
