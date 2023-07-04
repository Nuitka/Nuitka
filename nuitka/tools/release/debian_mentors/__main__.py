#!/usr/bin/env python

""" Debian/Ubuntu package release.

"""

import os
import shutil

from nuitka.tools.release.Debian import cleanupTarfileForDebian, runPy2dsc
from nuitka.tools.release.Documentation import createReleaseDocumentation
from nuitka.tools.release.Release import checkBranchName
from nuitka.Tracing import my_print


def main():
    branch_name = checkBranchName()
    assert branch_name == "main"

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

            cleanupTarfileForDebian(
                codename="sid", filename=filename, new_name=new_name
            )

            entry = runPy2dsc(filename, new_name)

            break
    else:
        assert False

    os.chdir("deb_dist")
    os.chdir(entry)

    # Build the debian package, but disable the running of tests, will be done later
    # in the pbuilder test steps.
    assert os.system("debuild --set-envvar=DEB_BUILD_OPTIONS=nocheck") == 0

    os.chdir("../../..")
    assert os.path.exists("dist/deb_dist")

    # Cleanup the build directory, not needed anymore.
    shutil.rmtree("build", ignore_errors=True)

    my_print("Uploading...", style="blue")
    os.chdir("dist/deb_dist")

    assert os.system("dput mentors *.changes") == 0

    my_print("Finished.", style="blue")
