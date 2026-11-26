#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Release tools related to Debian packaging."""

import os
import sys

from nuitka.Tracing import tools_logger
from nuitka.utils.Execution import check_call, getNullInput
from nuitka.utils.FileOperations import (
    copyFile,
    copyTree,
    deleteFile,
    getFileContentByLine,
    getFileContents,
    getFileList,
    listDir,
    openTextFile,
    removeFileExecutablePermission,
    resetDirectory,
    resolveShellPatternToFilenames,
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


def fixupPermissionsInplace(
    dest_path,
    file_perm,
    dir_perm,
    ignore_filenames=(),
):
    """Set permissions for all files and directories below a path.

    Args:
        dest_path: Root directory to fix up.
        file_perm: Permission bits to set on files.
        dir_perm: Permission bits to set on directories.
        ignore_filenames: Filenames that shall keep their permissions.
    """

    for filename in getFileList(dest_path, ignore_filenames=ignore_filenames):
        os.chmod(filename, file_perm)
        os.chmod(os.path.dirname(filename), dir_perm)


def copySourceForDebianBuild(source_path):
    """Copy the source checkout for building Debian packages.

    Notes:
        The source checkout may be on a mount that reports all files as
        executable and ignores 'chmod', e.g. a Windows share mounted into a
        container. The debhelper tooling then executes the Debian config files
        instead of reading them, which fails, so work on a copy where the
        permissions can be fixed. This changes the current directory to the
        copy.

    Args:
        source_path: Root directory of the source checkout to copy.
    """

    tools_logger.info(
        "Copying src to temporary location before modifying it.", style="blue"
    )

    copyTree(source_path, "/var/tmp/src")
    os.chdir("/var/tmp/src")

    fixupPermissionsInplace(
        "debian", int("644", 8), int("755", 8), ignore_filenames=("rules",)
    )
    fixupPermissionsInplace("nuitka", int("644", 8), int("755", 8))


def _fixupPy2dscDebianPermissions(debian_dir):
    """Remove executable permissions from copied Debian config files.

    Notes:
        On mounts that report all files as executable, e.g. container builds
        using Windows shares, the copied Debian config files inherit the
        executable bit. The debhelper tooling then runs 'nuitka.install' as an
        executable config file instead of reading it, which fails. Keep 'rules'
        executable, but remove the executable permission from the rest.
    """

    for filename in getFileList(debian_dir, ignore_filenames=("rules",)):
        removeFileExecutablePermission(filename)


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

    for matched_filename in resolveShellPatternToFilenames("deb_dist/*_source*"):
        deleteFile(matched_filename, must_exist=True)

    # Remove the now useless input, py2dsc has copied it, and we don't
    # publish it.
    deleteFile(new_name, must_exist=True)

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
    debian_dir = "deb_dist/%s/debian" % entry
    assert os.path.isdir(debian_dir), debian_dir

    resetDirectory(
        path=debian_dir,
        logger=tools_logger,
        ignore_errors=False,
        extra_recommendation=None,
    )

    check_call(
        [
            "rsync",
            "-a",
            "--exclude",
            "pbuilder-hookdir",
            "../debian/",
            debian_dir + "/",
        ]
    )

    _fixupPy2dscDebianPermissions(debian_dir)

    for pattern in ("deb_dist/*.dsc", "deb_dist/*.debian.tar.xz"):
        matched_filenames = resolveShellPatternToFilenames(pattern)
        assert matched_filenames, pattern

        for matched_filename in matched_filenames:
            deleteFile(matched_filename, must_exist=True)

    return entry


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
