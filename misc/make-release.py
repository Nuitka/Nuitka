#!/usr/bin/env python
#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os
import sys

# Unchanged, running from checkout, use the parent directory, the nuitka
# package ought be there.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
        )
    )
)

import shutil
import subprocess
from optparse import OptionParser

from nuitka.tools.release.Release import checkAtHome, checkBranchName
from nuitka.tools.release.Debian import checkChangeLog
from nuitka.tools.release.Documentation import createReleaseDocumentation

parser = OptionParser()

parser.add_option(
    "--use-as-ds-source",
    action  = "store",
    dest    = "ds_source",
    default = None,
    help    = """\
When given, use this as the source for the Debian package instead. Default \
%default."""
)

options, positional_args = parser.parse_args()

assert not positional_args, positional_args

checkAtHome()

from nuitka.Version import getNuitkaVersion
nuitka_version = getNuitkaVersion()

branch_name = checkBranchName()

from nuitka.tools.release.Release import checkNuitkaChangelog

if branch_name.startswith("release") or \
   branch_name == "master" or \
   branch_name.startswith("hotfix/"):
    if nuitka_version.count('.') == 2:
        assert checkChangeLog("New upstream release.")
    else:
        assert checkChangeLog("New upstream hotfix release.")

    assert checkNuitkaChangelog() == "final", checkNuitkaChangelog()
else:
    assert checkChangeLog("New upstream pre-release."), branch_name
    assert checkNuitkaChangelog() == "draft", checkNuitkaChangelog()

shutil.rmtree("dist", ignore_errors = True)
shutil.rmtree("build", ignore_errors = True)

createReleaseDocumentation()
assert 0 == os.system("python setup.py sdist --formats=bztar,gztar,zip")

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

for filename in os.listdir('.'):
    if filename.endswith(".tar.gz"):
        new_name = filename[:-7] + "+ds.tar.gz"

        shutil.copy(filename, new_name)
        assert 0 == os.system("gunzip " + new_name)
        assert 0 == os.system(
            "tar --wildcards --delete --file " + new_name[:-3] + \
            " Nuitka*/*.pdf" + \
            " Nuitka*/build/inline_copy"
        )
        assert 0 == os.system("gzip -9 -n " + new_name[:-3])

        assert 0 == os.system("py2dsc " + new_name)

        # Fixup for py2dsc not taking our custom suffix into account, so we need
        # to rename it ourselves.
        before_deb_name = filename[:-7].lower().replace('-', '_')
        after_deb_name = before_deb_name.replace("rc", "~rc")

        assert 0 == os.system(
            "mv 'deb_dist/%s.orig.tar.gz' 'deb_dist/%s+ds.orig.tar.gz'" % (
                before_deb_name, after_deb_name
            )
        )

        assert 0 == os.system(
            "rm -f deb_dist/*_source*"
        )

        # Remove the now useless input, py2dsc has copied it, and we don't
        # publish it.
        os.unlink(new_name)

        if options.ds_source is not None:
            shutil.copyfile(options.ds_source, "deb_dist/%s+ds.orig.tar.gz" % after_deb_name)

        break
else:
    assert False

os.chdir("deb_dist")

# Assert that the unpacked directory is there and file it. Otherwise fail badly.
for entry in os.listdir('.'):
    if os.path.isdir(entry) and entry.startswith("nuitka") and not entry.endswith(".orig"):
        break
else:
    assert False

# Import the "debian" directory from above. It's not in the original tar and
# overrides or extends what py2dsc does.
assert 0 == os.system(
    "rsync -a --exclude pbuilder-hookdir ../../debian/ %s/debian/" % entry
)

assert 0 == os.system("rm *.dsc *.debian.tar.xz")
os.chdir(entry)

# Build the debian package, but disable the running of tests, will be done later
# in the pbuilders.
assert 0 == os.system("debuild --set-envvar=DEB_BUILD_OPTIONS=nocheck")

os.chdir("../../..")

checkAtHome()

assert os.path.exists("dist/deb_dist")

# Check with pylint in pedantic mode and don't proceed if there were any
# warnings given. Nuitka is lintian clean and shall remain that way.
assert 0 == os.system(
    "lintian --pedantic --fail-on-warnings dist/deb_dist/*.changes"
)

os.system("cp dist/deb_dist/*.deb dist/")

for filename in os.listdir("dist/deb_dist"):
    if os.path.isdir("dist/deb_dist/" + filename):
        shutil.rmtree("dist/deb_dist/" + filename)

# Sign the result files. The Debian binary package was copied here.
for filename in os.listdir("dist"):
    if os.path.isfile("dist/" + filename):
        assert 0 == os.system("chmod 644 dist/" + filename)
        assert 0 == os.system(
            "gpg --local-user 2912B99C --detach-sign dist/" + filename
        )

# Cleanup the build directory, not needed.
shutil.rmtree("build", ignore_errors = True)

print("Finished.")
