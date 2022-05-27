#!/usr/bin/env python
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

""" Release script for manual usage.

"""

import os
import sys

# Unchanged, running from checkout, use the parent directory, the nuitka
# package ought be there.
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

# isort:start

import shutil
from optparse import OptionParser

from nuitka.tools.release.Debian import (
    checkChangeLog,
    cleanupTarfileForDebian,
    runPy2dsc,
)
from nuitka.tools.release.Documentation import createReleaseDocumentation
from nuitka.tools.release.Release import (
    checkAtHome,
    checkBranchName,
    checkNuitkaChangelog,
)
from nuitka.Version import getNuitkaVersion

parser = OptionParser()

options, positional_args = parser.parse_args()

assert not positional_args, positional_args

checkAtHome()

nuitka_version = getNuitkaVersion()

branch_name = checkBranchName()


if (
    branch_name.startswith("release")
    or branch_name == "main"
    or branch_name.startswith("hotfix/")
):
    if nuitka_version.count(".") == 1:
        assert checkChangeLog("New upstream release.")
    else:
        assert checkChangeLog("New upstream hotfix release.")

    assert checkNuitkaChangelog() == "final", checkNuitkaChangelog()
else:
    assert checkChangeLog("New upstream pre-release."), branch_name
    assert checkNuitkaChangelog() == "draft", checkNuitkaChangelog()

shutil.rmtree("dist", ignore_errors=True)
shutil.rmtree("build", ignore_errors=True)

createReleaseDocumentation()
assert os.system("python setup.py sdist --formats=bztar,gztar,zip") == 0

os.chdir("dist")

# Clean the stage for the debian package. The name "deb_dist" is what "py2dsc"
# uses for its output later on.

if os.path.exists("deb_dist"):
    shutil.rmtree("deb_dist")

# Provide a re-packed tar.gz for the Debian package as input.

# Create it as a "+ds" file, removing:
# - the benchmarks (too many sources, not useful to end users, potential license
#   issues)
# - the inline copy of scons (not wanted for Debian)

# Then run "py2dsc" on it.

for filename in os.listdir("."):
    if filename.endswith(".tar.gz"):
        new_name = filename[:-7] + "+ds.tar.gz"

        cleanupTarfileForDebian(filename, new_name)

        entry = runPy2dsc(filename, new_name)

        break
else:
    assert False

os.chdir("deb_dist")
os.chdir(entry)

# Build the debian package, but disable the running of tests, will be done later
# in the pbuilders.
assert os.system("debuild --set-envvar=DEB_BUILD_OPTIONS=nocheck") == 0

os.chdir("../../..")

checkAtHome()

assert os.path.exists("dist/deb_dist")

# Check with pylint in pedantic mode and don't proceed if there were any
# warnings given. Nuitka is lintian clean and shall remain that way.
assert os.system("lintian --pedantic dist/deb_dist/*.changes") == 0

os.system("cp dist/deb_dist/*.deb dist/")

for filename in os.listdir("dist/deb_dist"):
    if os.path.isdir("dist/deb_dist/" + filename):
        shutil.rmtree("dist/deb_dist/" + filename)

# Sign the result files. The Debian binary package was copied here.
for filename in os.listdir("dist"):
    if os.path.isfile("dist/" + filename):
        assert os.system("chmod 644 dist/" + filename) == 0
        assert (
            os.system("gpg --local-user 2912B99C --detach-sign dist/" + filename) == 0
        )

# Cleanup the build directory, not needed.
shutil.rmtree("build", ignore_errors=True)

print("Finished.")
