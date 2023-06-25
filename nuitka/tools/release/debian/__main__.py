#!/usr/bin/env python

""" Debian/Ubuntu package release.

"""

import os
import shutil
import sys
from optparse import OptionParser

from nuitka.tools.release.Debian import (
    checkChangeLog,
    cleanupTarfileForDebian,
    runPy2dsc,
)
from nuitka.tools.release.Release import checkBranchName, getBranchCategory
from nuitka.Tracing import my_print
from nuitka.utils.Execution import check_call
from nuitka.utils.FileOperations import (
    putTextFileContents,
    resolveShellPatternToFilenames,
)
from nuitka.Version import getNuitkaVersion


def main():
    # Complex stuff, pylint: disable=too-many-statements

    # Make sure error messages are in English.
    os.environ["LANG"] = "C"

    parser = OptionParser()

    parser.add_option(
        "--no-pbuilder-update",
        action="store_false",
        dest="update_pbuilder",
        default=True,
        help="""\
Update the pbuilder chroot before building. Default %default.""",
    )

    parser.add_option(
        "--check",
        action="store_true",
        dest="check",
        default=False,
        help="""\
Check only, if the package builds, do not upload. Default %default.""",
    )

    options, positional_args = parser.parse_args()

    assert len(positional_args) == 1, positional_args
    codename = positional_args[0]

    nuitka_version = getNuitkaVersion()

    branch_name = checkBranchName()

    category = getBranchCategory(branch_name)

    if category == "stable":
        if nuitka_version.count(".") == 1:
            assert checkChangeLog("New upstream release.")
        else:
            assert checkChangeLog("New upstream hotfix release.")
    else:
        assert checkChangeLog("New upstream pre-release.")

    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("build", ignore_errors=True)

    # Build the source distribution as per our setup, however that's not going
    # to be good enough for Debian packages. spellchecker: ignore gztar
    assert os.system("%s setup.py sdist --formats=gztar" % sys.executable) == 0

    os.chdir("dist")

    # Clean the stage for the debian package. The name "deb_dist" is what "py2dsc"
    # uses for its output later on.
    shutil.rmtree("deb_dist", ignore_errors=True)

    # Provide a re-packed tar.gz for the Debian package as input.

    # Create it as a "+ds" file, removing:
    # - the benchmarks (too many sources, not useful to end users, potential license
    #   issues)
    # - the inline copy of scons (not wanted for Debian)

    for filename in os.listdir("."):
        if filename.endswith(".tar.gz"):
            new_name = filename[:-7] + "+ds.tar.gz"

            cleanupTarfileForDebian(
                codename=codename, filename=filename, new_name=new_name
            )

            runPy2dsc(filename, new_name)

            break
    else:
        assert False

    os.chdir("..")
    assert os.path.exists("dist/deb_dist")

    # Check with pylint in pedantic mode and don't proceed if there were any
    # warnings given. Nuitka is lintian clean and shall remain that way. For
    # hotfix releases, i.e. "stable" builds, we skip this test though.

    if category == "stable":
        my_print("Skipped lintian checks for stable releases.", style="blue")
    else:
        # TODO: Do the lintian checks inside the pbuilder, we do not build
        # the package locally anymore, or with a builder that focusses on
        # that with e.g. the develop branch as a target on a regular basis.
        my_print("Skipped lintian checks for now.", style="blue")
        # assert os.system("lintian --pedantic --allow-root dist/deb_dist/*.changes") == 0

    # Move the created debian package files out.
    os.system("cp dist/deb_dist/*.deb dist/")

    # Build inside the pbuilder chroot, and output to dedicated directory.
    shutil.rmtree("package", ignore_errors=True)
    os.makedirs("package")

    # Now update the pbuilder, spell-checker: ignore basetgz

    basetgz_filename = "/pbuilder/%s.tgz" % codename

    if options.update_pbuilder:
        command = """\
sudo /usr/sbin/pbuilder --update --basetgz %s""" % (
            basetgz_filename
        )

        assert os.system(command) == 0, codename

    (dsc_filename,) = resolveShellPatternToFilenames("dist/deb_dist/*.dsc")

    # Execute the package build in the pbuilder with tests.
    # spell-checker: ignore hookdir,debemail,buildresult
    command = (
        "sudo",
        "/usr/sbin/pbuilder",
        "--build",
        "--basetgz",
        basetgz_filename,
        "--hookdir",
        "debian/pbuilder-hookdir",
        "--debemail",
        "Kay Hayen <kay.hayen@gmail.com>",
        "--buildresult",
        "package",
        dsc_filename,
    )

    check_call(command, shell=False)

    # Cleanup the build directory, not needed anymore.
    shutil.rmtree("build", ignore_errors=True)

    # Now build the repository.
    my_print("Building repository ...", style="blue")

    os.chdir("package")

    os.makedirs("repo")
    os.chdir("repo")

    os.makedirs("conf")

    # spell-checker: ignore armel armhf
    putTextFileContents(
        "conf/distributions",
        contents="""\
Origin: Nuitka
Label: Nuitka
Codename: %(codename)s
Architectures: i386 amd64 armel armhf powerpc
Components: main
Description: Apt repository for project Nuitka %(codename)s
SignWith: D96ADCA1377F1CEB6B5103F11BFC33752912B99C
"""
        % {"codename": codename},
    )

    # spell-checker: ignore reprepro includedeb
    command = ["reprepro", "includedeb", codename]
    command.extend(resolveShellPatternToFilenames("../*.deb"))

    check_call(command, shell=False)

    if options.check:
        my_print("Finished check.", style="blue")

    my_print("Uploading ...", style="blue")

    # Create repo folder unless already done. This is needed for the first
    # build only.
    assert (
        os.system(
            "ssh root@ssh.nuitka.net mkdir -p /var/www/deb/%s/%s/"
            % (category, codename)
        )
        == 0
    )

    # Update the repository on the web site.
    assert (
        os.system(
            "rsync -avz --delete dists pool --chown www-data root@ssh.nuitka.net:/var/www/deb/%s/%s/"
            % (category, codename)
        )
        == 0
    )

    my_print("Finished.", style="blue")
