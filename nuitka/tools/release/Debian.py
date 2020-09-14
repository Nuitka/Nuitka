#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Release tools related to Debian packaging.

"""

import os
import shutil
import sys

from nuitka.utils.FileOperations import getFileContentByLine, listDir


def _bumpVersion(debian_version):
    assert os.system('debchange --newversion=%s ""' % debian_version) == 0


def updateDebianChangelog(old_version, new_version, distribution):
    debian_version = new_version.replace("rc", "~rc") + "+ds-1"

    os.environ["DEBEMAIL"] = "Kay Hayen <kay.hayen@gmail.com>"

    if "rc" in new_version:
        if "rc1" in new_version:
            assert os.system('debchange -R "New upstream pre-release."') == 0

        _bumpVersion(debian_version)

        with open("Changelog.rst") as f:
            changelog = f.read()
        if "(Draft)" not in changelog.splitlines()[0]:
            title = "Nuitka Release " + new_version[:-3] + " (Draft)"

            with open("Changelog.rst", "w") as changelog_file:
                changelog_file.write(title + "\n" + ("=" * len(title) + "\n\n"))
                changelog_file.write("This release is not done yet.\n\n\n")
                changelog_file.write(changelog)

    else:
        if "rc" in old_version:
            # Initial final release after pre-releases.
            with open("debian/changelog") as f:
                changelog_lines = f.readlines()
            with open("debian/changelog", "w") as output:
                first = True
                for line in changelog_lines[1:]:
                    if line.startswith("nuitka") and first:
                        first = False

                    if not first:
                        output.write(line)

            os.system('debchange -R "New upstream release."')
        else:
            # Hotfix release after previous final or hotfix release.
            os.system('debchange -R "New upstream hotfix release."')

    _bumpVersion(debian_version)
    assert os.system('debchange -r "" --distribution "%s"' % distribution) == 0


def checkChangeLog(message):
    """Check debian changelog for given message to be present."""

    for line in getFileContentByLine("debian/changelog"):
        if line.startswith(" --"):
            return False

        if message in line:
            return True

    sys.exit("Error, didn't find in debian/changelog: '%s'" % message)


def cleanupTarfileForDebian(filename, new_name):
    """Remove files that shouldn't be in Debian.

    The inline copies should definitely not be there. Also remove the
    PDF files for now.
    """

    shutil.copyfile(filename, new_name)
    assert os.system("gunzip " + new_name) == 0
    assert (
        os.system(
            "tar --wildcards --delete --file "
            + new_name[:-3]
            + " Nuitka*/*.pdf Nuitka*/build/inline_copy"
        )
        == 0
    )
    assert os.system("gzip -9 -n " + new_name[:-3]) == 0


def runPy2dsc(filename, new_name):
    assert os.system("py2dsc " + new_name) == 0

    # Fixup for py2dsc not taking our custom suffix into account, so we need
    # to rename it ourselves.
    before_deb_name = filename[:-7].lower().replace("-", "_")
    after_deb_name = before_deb_name.replace("rc", "~rc")

    assert (
        os.system(
            "mv 'deb_dist/%s.orig.tar.gz' 'deb_dist/%s+ds.orig.tar.gz'"
            % (before_deb_name, after_deb_name)
        )
        == 0
    )

    assert os.system("rm -f deb_dist/*_source*") == 0

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
    assert os.system("rm -r deb_dist/%s/debian/*" % entry) == 0
    assert (
        os.system(
            "rsync -a --exclude pbuilder-hookdir ../debian/ deb_dist/%s/debian/" % entry
        )
        == 0
    )

    assert os.system("rm deb_dist/*.dsc deb_dist/*.debian.tar.xz") == 0

    return entry
