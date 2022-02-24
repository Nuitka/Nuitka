#!/usr/bin/python
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

""" Make version bump for Nuitka. """

import sys
from optparse import OptionParser

from nuitka.tools.Basics import goHome
from nuitka.tools.release.Debian import updateDebianChangelog
from nuitka.tools.release.Release import getBranchName
from nuitka.Tracing import my_print
from nuitka.utils.FileOperations import openTextFile


def getBumpedVersion(mode, old_version):
    if mode == "prerelease":
        if "rc" in old_version:
            parts = old_version.split("rc")

            new_version = "rc".join([parts[0], str(int(parts[1]) + 1)])
        else:
            old_version = ".".join(old_version.split(".")[:3])
            parts = old_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)

            new_version = ".".join(parts) + "rc1"
    elif mode == "release":
        if "rc" in old_version:
            old_version = old_version[: old_version.find("rc")]
            was_pre = True
        else:
            was_pre = False

        new_version = ".".join(old_version.split(".")[:3])

        if not was_pre:
            parts = new_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)

            new_version = ".".join(parts)
    elif mode == "hotfix":
        assert "pre" not in old_version and "rc" not in old_version

        parts = old_version.split(".")

        if len(parts) == 2:
            parts.append("1")
        else:
            parts[-1] = str(int(parts[-1]) + 1)

        new_version = ".".join(parts)

    else:
        sys.exit("Error, unknown mode '%s'." % mode)

    return new_version


def main():
    parser = OptionParser()

    parser.add_option(
        "--mode",
        action="store",
        dest="mode",
        default=None,
        help="""\
The mode of update, prerelease, hotfix, release, auto (default auto determines from branch).""",
    )

    options, positional_args = parser.parse_args()

    if positional_args:
        parser.print_help()

        sys.exit("\nError, no positional argument allowed.")

    # Go its own directory, to have it easy with path knowledge.
    goHome()

    with openTextFile("nuitka/Version.py", "r") as f:
        option_lines = f.readlines()

    (version_line,) = [line for line in option_lines if line.startswith("Nuitka V")]

    old_version = version_line[8:].rstrip()

    mode = options.mode
    branch_name = getBranchName()

    if mode is None:
        if branch_name.startswith("hotfix/"):
            mode = "hotfix"
        elif branch_name == "main" or branch_name.startswith("release/"):
            mode = "release"
        elif branch_name == "develop":
            mode = "prerelease"
        else:
            sys.exit("Error, cannot detect mode from branch name '%s'." % branch_name)

    new_version = getBumpedVersion(mode, old_version)
    my_print("Bumped %s '%s' -> '%s'." % (mode, old_version, new_version))

    with openTextFile("nuitka/Version.py", "w") as options_file:
        for line in option_lines:
            if line.startswith("Nuitka V"):
                line = "Nuitka V" + new_version + "\n"

            options_file.write(line)

    # Debian is currently in not freeze, change to "experimental" once that changes.
    updateDebianChangelog(old_version, new_version, "unstable")
