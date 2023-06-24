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
    shallNotIncludeInlineCopy,
)
from nuitka.tools.release.Release import checkBranchName, getBranchCategory
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.Execution import check_call, withEnvironmentVarOverridden
from nuitka.utils.FileOperations import (
    copyTree,
    getFileList,
    putTextFileContents,
    resolveShellPatternToFilenames,
    withDirectoryChange,
)
from nuitka.Version import getNuitkaVersion


def parseArgs():
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

    return options, codename


def fixupPermissionsInplace(
    dest_path,
    file_perm,
    dir_perm,
    ignore_filenames=(),
):
    for filename in getFileList(dest_path, ignore_filenames=ignore_filenames):
        os.chmod(filename, file_perm)
        os.chmod(os.path.dirname(filename), dir_perm)


def fixupPermissionsCopy(source_path, dest_path, ignore_filenames=()):
    copyTree(source_path=source_path, dest_path=dest_path)

    fixupPermissionsInplace(
        dest_path=dest_path,
        file_perm=int("600", 8),
        dir_perm=int("700", 8),
        ignore_filenames=ignore_filenames,
    )


def main():
    # Complex stuff, pylint: disable=too-many-statements

    # Make sure error messages are in English.
    os.environ["LANG"] = "C"

    options, codename = parseArgs()

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

    # Clean the stage for the debian package. The name "deb_dist" is what "py2dsc"
    # uses for its output later on.
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("build", ignore_errors=True)

    copyTree("/src", "/var/tmp/src")
    os.chdir("/var/tmp/src")

    fixupPermissionsInplace(
        "debian", int("644", 8), int("755", 8), ignore_filenames=("rules",)
    )
    fixupPermissionsInplace("nuitka", int("644", 8), int("755", 8))

    # Build the source distribution as per our setup, however that's not going
    # to be good enough for Debian packages. We may want to avoid inline copies
    # being added to sdist for the Debian that do not need it.
    # spellchecker: ignore gztar
    with withEnvironmentVarOverridden(
        "NUITKA_NO_INLINE_COPY", "1" if shallNotIncludeInlineCopy(codename) else "0"
    ):
        check_call([sys.executable, "setup.py", "sdist", "--formats=gztar"])

        with withDirectoryChange("dist"):
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

                    entry = runPy2dsc(filename, new_name)

                    break
            else:
                assert False

        # Copy gnupg folder, to control the permissions.
        fixupPermissionsCopy(source_path="/root/.gnupg", dest_path="/root/.gnupg2")
        os.environ["GNUPGHOME"] = "/root/.gnupg2"

        # Copy ssh folder to control permissions.
        fixupPermissionsCopy(source_path="/root/.ssh2", dest_path="/root/.ssh")

        with withDirectoryChange(os.path.join("dist", "deb_dist", entry)):
            for filename in getFileList("debian", ignore_filenames=("rules",)):
                os.chmod(filename, int("644", 8))

            # Build the debian package, but disable the running of tests, will be done later
            # in the pbuilder test steps, pass inline copy setting on, and make sure that
            # the signing works, gpg-agent otherwise refuses to start.
            check_call(
                [
                    "debuild",
                    "--set-envvar=DEB_BUILD_OPTIONS=nocheck",
                    "--set-envvar=NUITKA_NO_INLINE_COPY=%s"
                    % os.environ["NUITKA_NO_INLINE_COPY"],
                    "--set-envvar=GNUPGHOME=%s" % os.environ["GNUPGHOME"],
                ]
            )

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
    assert os.system("cp dist/deb_dist/*.deb dist/") == 0

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

        check_call(
            ["sudo", "/usr/sbin/pbuilder", "--update", "--basetgz", basetgz_filename]
        )

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
        tools_logger.sysexit("Finished check.", exit_code=0)

    my_print("Uploading ...", style="blue")

    # Create repo folder unless already done. This is needed for the first
    # build only. It also prevents us from talking to foreign servers, by
    # letting ssh check all it wants.
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
