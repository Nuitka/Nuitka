#!/usr/bin/env python

""" Debian/Ubuntu package release.

"""

from __future__ import print_function

import os
import shutil
from optparse import OptionParser

from nuitka.tools.release.Debian import checkChangeLog, cleanupTarfileForDebian
from nuitka.tools.release.Documentation import createReleaseDocumentation
from nuitka.tools.release.Release import checkBranchName, getBranchCategory
from nuitka.Version import getNuitkaVersion


def main():
    # Complex stuff, pylint: disable=too-many-branches,too-many-statements

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

    nuitka_version = getNuitkaVersion()

    branch_name = checkBranchName()

    category = getBranchCategory(branch_name)

    if category == "stable":
        if nuitka_version.count('.') == 2:
            assert checkChangeLog("New upstream release.")
        else:
            assert checkChangeLog("New upstream hotfix release.")
    else:
        assert checkChangeLog("New upstream pre-release.")

    shutil.rmtree("dist", ignore_errors = True)
    shutil.rmtree("build", ignore_errors = True)

    createReleaseDocumentation()
    assert os.system("python setup.py sdist --formats=gztar") == 0

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

            cleanupTarfileForDebian(filename, new_name)

            assert os.system(
                "py2dsc " + new_name
            ) == 0

            # Fixup for py2dsc not taking our custom suffix into account, so we need
            # to rename it ourselves.
            before_deb_name = filename[:-7].lower().replace('-', '_')
            after_deb_name = before_deb_name.replace("rc", "~rc")

            assert os.system(
                "mv 'deb_dist/%s.orig.tar.gz' 'deb_dist/%s+ds.orig.tar.gz'" % (
                    before_deb_name, after_deb_name
                )
            ) == 0

            assert os.system(
                "rm -f deb_dist/*_source*"
            ) == 0

            # Remove the now useless input, py2dsc has copied it, and we don't
            # publish it.
            os.unlink(new_name)

            break
    else:
        assert False

    os.chdir("deb_dist")

    # Assert that the unpacked directory is there. Otherwise fail badly.
    for entry in os.listdir('.'):
        if os.path.isdir(entry) and \
           entry.startswith("nuitka") and \
           not entry.endswith(".orig"):
            break
    else:
        assert False

    # We know the dir is not empty, pylint: disable=undefined-loop-variable

    # Import the "debian" directory from above. It's not in the original tar and
    # overrides or extends what py2dsc does.
    assert os.system(
        "rsync -a --exclude pbuilder-hookdir ../../debian/ %s/debian/" % entry
    ) == 0

    # Remove now unnecessary files.
    assert os.system(
        "rm *.dsc *.debian.tar.[gx]z"
    ) == 0
    os.chdir(entry)

    # Build the debian package, but disable the running of tests, will be done later
    # in the pbuilder test steps.
    assert os.system(
        "debuild --set-envvar=DEB_BUILD_OPTIONS=nocheck"
    ) == 0

    os.chdir("../../..")
    assert os.path.exists("dist/deb_dist")

    # Check with pylint in pedantic mode and don't proceed if there were any
    # warnings given. Nuitka is lintian clean and shall remain that way. For
    # hotfix releases, i.e. "stable" builds, we skip this test though.
    if category == "stable":
        print("Skipped lintian checks for stable releases.")
    else:
        assert os.system(
            "lintian --pedantic --fail-on-warnings --allow-root dist/deb_dist/*.changes"
        ) == 0

    # Move the created debian package files out.
    os.system("cp dist/deb_dist/*.deb dist/")

    # Build inside the pbuilder chroot, and output to dedicated directory.
    shutil.rmtree("package", ignore_errors = True)
    os.makedirs("package")

    # Now update the pbuilder.
    if options.update_pbuilder:
        command = """\
sudo /usr/sbin/pbuilder --update --basetgz  /var/cache/pbuilder/%s.tgz""" % (
            codename
        )

        assert os.system(command) == 0, codename

    # Execute the package build in the pbuilder with tests.
    command = """\
sudo /usr/sbin/pbuilder --build --basetgz  /var/cache/pbuilder/%s.tgz \
--hookdir debian/pbuilder-hookdir --debemail "Kay Hayen <kay.hayen@gmail.com>" \
--buildresult package dist/deb_dist/*.dsc""" % codename

    assert os.system(command) == 0, codename

    # Cleanup the build directory, not needed anymore.
    shutil.rmtree("build", ignore_errors = True)

    # Now build the repository.
    os.chdir("package")

    os.makedirs("repo")
    os.chdir("repo")

    os.makedirs("conf")

    with open("conf/distributions",'w') as output:
        output.write(
            """\
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

    assert os.system(
        "reprepro includedeb %s ../*.deb" % codename
    ) == 0

    print("Uploading...")

    # Create repo folder unless already done. This is needed for the first
    # build only.
    assert os.system(
        "ssh root@nuitka.net mkdir -p /var/www/deb/%s/%s/" % (
            category,
            codename
        )
    ) == 0

    # Update the repository on the web site.
    assert os.system(
        "rsync -avz --delete dists pool --chown www-data root@nuitka.net:/var/www/deb/%s/%s/" % (
            category,
            codename
        )
    ) == 0

    print("Finished.")
