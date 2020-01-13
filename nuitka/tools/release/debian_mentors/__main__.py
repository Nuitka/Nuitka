#!/usr/bin/env python

""" Debian/Ubuntu package release.

"""

from __future__ import print_function

import os
import shutil

from nuitka.tools.release.Debian import cleanupTarfileForDebian, runPy2dsc
from nuitka.tools.release.Documentation import createReleaseDocumentation
from nuitka.tools.release.Release import checkBranchName


def main():
    branch_name = checkBranchName()
    assert branch_name == "master"

    createReleaseDocumentation()
    assert os.system("python setup.py sdist --formats=gztar") == 0

    os.chdir("dist")

    # Clean the stage for the debian package. The name "deb_dist" is what "py2dsc"
    # uses for its output later on.
    shutil.rmtree("deb_dist", ignore_errors=True)

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

            runPy2dsc(filename, new_name)

            break
    else:
        assert False

    os.chdir("deb_dist")

    # Assert that the unpacked directory is there. Otherwise fail badly.
    for entry in os.listdir("."):
        if (
            os.path.isdir(entry)
            and entry.startswith("nuitka")
            and not entry.endswith(".orig")
        ):
            break
    else:
        assert False

    # We know the dir is not empty, pylint: disable=undefined-loop-variable

    # Import the "debian" directory from above. It's not in the original tar and
    # overrides or extends what py2dsc does.
    assert (
        os.system(
            "rsync -a --exclude pbuilder-hookdir ../../debian/ %s/debian/" % entry
        )
        == 0
    )

    # Remove now unnecessary files.
    assert os.system("rm *.dsc *.debian.tar.[gx]z") == 0
    os.chdir(entry)

    # Build the debian package, but disable the running of tests, will be done later
    # in the pbuilder test steps.
    assert os.system("debuild --set-envvar=DEB_BUILD_OPTIONS=nocheck") == 0

    os.chdir("../../..")
    assert os.path.exists("dist/deb_dist")

    # Cleanup the build directory, not needed anymore.
    shutil.rmtree("build", ignore_errors=True)

    print("Uploading...")
    os.chdir("dist/deb_dist")

    assert os.system("dput mentors *.changes") == 0

    print("Finished.")
