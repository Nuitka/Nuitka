#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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


def updateDebianChangelog(old_version, new_version):
    debian_version = new_version.replace("rc", "~rc") + "+ds-1"

    os.environ["DEBEMAIL"] = "Kay Hayen <kay.hayen@gmail.com>"

    if "rc" in new_version:
        if "rc1" in new_version:
            os.system('debchange -R "New upstream pre-release."')
            os.system('debchange --newversion=%s ""'  % debian_version)
        else:
            os.system('debchange --newversion=%s ""'  % debian_version)

        changelog = open("Changelog.rst").read()
        if "(Draft)" not in changelog.splitlines()[0]:
            title = "Nuitka Release " + new_version[:-3] + " (Draft)"

            with open("Changelog.rst", 'w') as changelog_file:
                changelog_file.write(title + '\n' + ('=' * len(title) + "\n\n"))
                changelog_file.write("This release is not done yet.\n\n\n")
                changelog_file.write(changelog)

    else:
        if "rc" in old_version:
            # Initial final release after pre-releases.
            changelog_lines = open("debian/changelog").readlines()
            with open("debian/changelog", 'w') as output:
                first = True
                for line in changelog_lines[1:]:
                    if line.startswith("nuitka") and first:
                        first = False

                    if not first:
                        output.write(line)

            os.system('debchange -R "New upstream release."')
            os.system('debchange --newversion=%s ""'  % debian_version)
        else:
            # Hotfix release after previous final or hotfix release.
            os.system('debchange -R "New upstream hotfix release."')
            os.system('debchange --newversion=%s ""'  % debian_version)

        os.system('debchange -r ""')


def checkChangeLog(message):
    """ Check debian changelog for given message to be present.

    """

    for line in open("debian/changelog"):
        if line.startswith(" --"):
            return False

        if message in line:
            return True

    sys.exit("Error, didn't find in debian/changelog: '%s'" % message)


def cleanupTarfileForDebian(filename, new_name):
    """ Remove files that shouldn't be in Debian.

    The inline copies should definitely not be there. Also remove the
    PDF files for now.
    """

    shutil.copy(filename, new_name)
    assert os.system(
        "gunzip " + new_name
    ) == 0
    assert os.system(
        "tar --wildcards --delete --file " + new_name[:-3] + \
        " Nuitka*/*.pdf Nuitka*/build/inline_copy"
    ) == 0
    assert os.system(
        "gzip -9 -n " + new_name[:-3]
    ) == 0
