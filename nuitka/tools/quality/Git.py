#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
import subprocess

from nuitka.containers.oset import OrderedSet
from nuitka.utils.Execution import check_call, check_output, getNullInput


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
    result = OrderedSet()

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


def getFileHashContent(object_hash):
    return check_output(["git", "cat-file", "-p", object_hash])


def putFileHashContent(filename):
    new_hash = check_output(
        ["git", "hash-object", "-w", "--stdin"], stdin=open(filename)
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
    patch = check_output(["git", "diff", orig_object_hash, new_object_hash])

    path = path.replace(os.path.sep, "/")

    # Substitute object hashes in patch header with path to working tree file
    patch_b = patch.replace(orig_object_hash.encode(), path.encode()).replace(
        new_object_hash.encode(), path.encode()
    )

    apply_patch = subprocess.Popen(
        ["git", "apply", "-"],
        stdin=getNullInput(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _output, _err = apply_patch.communicate(input=patch_b)

    # TODO: In case of failure, do we need to abort?

    return apply_patch.returncode != 0
