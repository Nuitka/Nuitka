#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Release tools related to Debian packaging.

"""

import os
import sys

from nuitka.utils.Execution import check_call, getNullInput
from nuitka.utils.FileOperations import (
    copyFile,
    getFileContentByLine,
    getFileContents,
    listDir,
    openTextFile,
)


def _callDebchange(*args):
    # spell-checker: ignore debchange
    args = ["debchange"] + list(args)

    os.environ["EDITOR"] = ""

    with getNullInput() as null_input:
        check_call(args, stdin=null_input)


_discarded_last_entry = False


def _discardDebianChangelogLastEntry():
    # Kind of weak, but we do not keep track if we do a lot of things,
    # for every program run this is only done once to simplify code,
    # but it's not reusable therefore.
    # pylint: disable=global-statement
    global _discarded_last_entry

    if _discarded_last_entry:
        return
    changelog_lines = getFileContents("debian/changelog").splitlines()

    with openTextFile("debian/changelog", "w") as output:
        first = True
        for line in changelog_lines[1:]:
            if line.startswith("nuitka") and first:
                first = False

            if not first:
                output.write(line + "\n")

    _discarded_last_entry = True


def updateDebianChangelog(old_version, new_version, distribution):
    debian_version = new_version.replace("rc", "~rc") + "+ds-1"

    if old_version == new_version:
        _discardDebianChangelogLastEntry()

    os.environ["DEBEMAIL"] = "Kay Hayen <kay.hayen@gmail.com>"

    if "rc" in new_version:
        if "rc" in old_version:
            # Initial final release after pre-releases.
            _discardDebianChangelogLastEntry()

        message = "New upstream pre-release."
    else:
        if "rc" in old_version:
            # Initial final release after pre-releases.
            _discardDebianChangelogLastEntry()

            message = "New upstream release."
        else:
            # Initial final release after pre-releases.

            # Hotfix release after previous final or hotfix release.
            message = "New upstream hotfix release."

    _callDebchange("--newversion=%s" % debian_version, message)
    _callDebchange("-r", "--distribution", distribution, "")


def checkChangeLog(message):
    """Check debian changelog for given message to be present."""

    for line in getFileContentByLine("debian/changelog"):
        if line.startswith(" --"):
            return False

        if message in line:
            return True

    sys.exit("Error, didn't find in debian/changelog: '%s'" % message)


def shallNotIncludeInlineCopy(codename):
    # Keep inline copy for old variants that cannot otherwise work
    return codename not in ("stretch", "jessie", "xenial")


def cleanupTarfileForDebian(codename, filename, new_name):
    """Remove files that shouldn't be in Debian.

    The inline copies should definitely not be there. Also remove the
    PDF files.
    """

    copyFile(filename, new_name)
    check_call(["gunzip", new_name])

    if shallNotIncludeInlineCopy(codename):
        command = [
            "tar",
            "--wildcards",
            "--delete",
            "--file",
            new_name[:-3],
            "Nuitka*/build/inline_copy",
        ]

        check_call(command)

    check_call(["gzip", "-9", "-n", new_name[:-3]])


def runPy2dsc(filename, new_name):
    check_call(["py2dsc", new_name])

    # Fixup for py2dsc not taking our custom suffix into account, so we need
    # to rename it ourselves.
    before_deb_name = filename[:-7].lower().replace("-", "_")
    after_deb_name = before_deb_name.replace("rc", "~rc")

    os.rename(
        "deb_dist/%s.orig.tar.gz" % before_deb_name,
        "deb_dist/%s+ds.orig.tar.gz" % after_deb_name,
    )

    check_call(["rm -f deb_dist/*_source*"], shell=True)

    # Remove the now useless input, py2dsc has copied it, and we don't
    # publish it.
    os.unlink(new_name)

    # Assert that the unpacked directory is there and find it. Otherwise fail badly.

    entry = None
    for fullname, entry in listDir("deb_dist"):
        if (
            os.path.isdir(fullname)
            and entry.startswith("nuitka")
            and not entry.endswith(".orig")
        ):
            break

    if entry is None:
        assert False

    # Import the "debian" directory from above. It's not in the original tar and
    # overrides fully what py2dsc did.
    check_call(["rm -r deb_dist/%s/debian/*" % entry], shell=True)

    check_call(
        [
            "rsync",
            "-a",
            "--exclude",
            "pbuilder-hookdir",
            "../debian/",
            "deb_dist/%s/debian/" % entry,
        ]
    )

    check_call(["rm deb_dist/*.dsc deb_dist/*.debian.tar.xz"], shell=True)

    return entry


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
