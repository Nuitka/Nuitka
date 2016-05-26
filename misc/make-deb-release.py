#!/usr/bin/env python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
import shutil
import subprocess
from optparse import OptionParser

parser = OptionParser()

parser.add_option(
    "--no-pbuilder-update",
    action  = "store_false",
    dest    = "update_pbuilder",
    default = True,
    help    = """\
Update the pbuilder chroot before building. Default %default."""
)

options, positional_args = parser.parse_args()

assert len(positional_args) == 1, positional_args
codename = positional_args[0]

nuitka_version = subprocess.check_output(
    "./bin/nuitka --version", shell = True
).strip()

branch_name = subprocess.check_output(
    "git name-rev --name-only HEAD".split()
).strip()

assert branch_name in (
    b"master",
    b"develop",
    b"factory",
    b"release/" + nuitka_version,
    b"hotfix/" + nuitka_version
), branch_name

if str is not bytes:
    branch_name = branch_name.decode()

def checkChangeLog(message):
    for line in open("debian/changelog"):
        if line.startswith(" --"):
            return False

        if message in line:
            return True
    else:
        assert False, message # No new messages.

if branch_name.startswith("release") or \
   branch_name == "master" or \
   branch_name.startswith("hotfix/"):
    if nuitka_version.count('.') == 2:
        assert checkChangeLog("New upstream release.")
    else:
        assert checkChangeLog("New upstream hotfix release.")

    category = "stable"
else:
    assert checkChangeLog("New upstream pre-release.")

    if branch_name == "factory":
        category = "factory"
    else:
        category = "develop"

shutil.rmtree("dist", ignore_errors = True)
shutil.rmtree("build", ignore_errors = True)

assert 0 == os.system("misc/make-doc.py")
assert 0 == os.system("python setup.py sdist --formats=gztar")

os.chdir("dist")

# Clean the stage for the debian package. The name "deb_dist" is what "py2dsc"
# uses for its output later on.
shutil.rmtree("deb_dist", ignore_errors = True)

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
        assert 0 == os.system(
            "gunzip " + new_name
        )
        assert 0 == os.system(
            "tar --wildcards --delete --file " + new_name[:-3] + \
            " Nuitka*/tests/benchmarks Nuitka*/*.pdf Nuitka*/build/inline_copy"
        )
        assert 0 == os.system(
            "gzip -9 -n " + new_name[:-3]
        )

        assert 0 == os.system(
            "py2dsc " + new_name
        )

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

        break
else:
    assert False

os.chdir("deb_dist")

# Assert that the unpacked directory is there and file it. Otherwise fail badly.
for entry in os.listdir('.'):
    if os.path.isdir(entry) and \
       entry.startswith("nuitka") and \
       not entry.endswith(".orig"):
        break
else:
    assert False

# Import the "debian" directory from above. It's not in the original tar and
# overrides or extends what py2dsc does.
assert 0 == os.system(
    "rsync -a --exclude pbuilder-hookdir ../../debian/ %s/debian/" % entry
)

assert 0 == os.system(
    "rm *.dsc *.debian.tar.[gx]z"
)
os.chdir(entry)

# Build the debian package, but disable the running of tests, will be done later
# in the pbuilder test steps.
assert 0 == os.system(
    "debuild --set-envvar=DEB_BUILD_OPTIONS=nocheck"
)

os.chdir("../../..")
assert os.path.exists("dist/deb_dist")

# Check with pylint in pedantic mode and don't proceed if there were any
# warnings given. Nuitka is lintian clean and shall remain that way. For
# hotfix releases, i.e. "master" builds, we skip this test though.
if branch_name != "master":
    assert 0 == os.system(
        "lintian --pedantic --fail-on-warnings --allow-root dist/deb_dist/*.changes"
    )
else:
    print("Skipped lintian checks for stable releases.")

os.system("cp dist/deb_dist/*.deb dist/")

# Build inside the pbuilder chroot, and output to dedicated directory.
shutil.rmtree("package", ignore_errors = True)
os.makedirs("package")

if options.update_pbuilder:
    command = """\
sudo /usr/sbin/pbuilder --update --basetgz  /var/cache/pbuilder/%s.tgz""" % (
        codename
    )

    assert 0 == os.system(command), codename

command = """\
sudo /usr/sbin/pbuilder --build --basetgz  /var/cache/pbuilder/%s.tgz \
--hookdir debian/pbuilder-hookdir --debemail "Kay Hayen <kay.hayen@gmail.com>" \
--buildresult package dist/deb_dist/*.dsc""" % codename

assert 0 == os.system(command), codename

# Cleanup the build directory, not needed anymore.
shutil.rmtree("build", ignore_errors = True)

os.chdir("package")

os.makedirs("repo")
os.chdir("repo")

os.makedirs("conf")

with open("conf/distributions",'w') as output:
    output.write("""\
Origin: Nuitka
Label: Nuitka
Codename: %(codename)s
Architectures: i386 amd64 armel armhf powerpc
Components: main
Description: Apt repository for project Nuitka %(codename)s
SignWith: 2912B99C
""" % {
        "codename" : codename
}
    )

assert 0 == os.system(
    "reprepro includedeb %s ../*.deb" % codename
)

print("Uploading...")

assert 0 == os.system(
    "ssh root@nuitka.net mkdir -p /var/www/deb/%s/%s/" % (
        category,
        codename
    )
)
assert 0 == os.system(
    "rsync -avz --delete dists pool --chown www-data root@nuitka.net:/var/www/deb/%s/%s/" % (
        category,
        codename
    )
)

print("Finished.")
