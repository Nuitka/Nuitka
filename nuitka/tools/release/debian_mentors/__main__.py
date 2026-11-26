"""Debian/Ubuntu package release."""

import os
import shutil
import sys

from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.tools.release.DebianPackage import (
    cleanupTarfileForDebian,
    copySourceForDebianBuild,
    runPy2dsc,
)
from nuitka.tools.release.Documentation import checkReleaseDocumentation
from nuitka.tools.release.Release import (
    checkBranchName,
    cleanupSourceDistributionState,
)
from nuitka.Tracing import my_print, tools_logger
from nuitka.utils.FileOperations import listDir


def parseArgs():
    parser = makeOptionsParser(usage=None, epilog=None)

    parser.add_option(
        "--assume-yes-for-downloads",
        action="store_true",
        dest="assume_yes_for_downloads",
        default=False,
        help="""\
Allow download and execution of tools if needed. Default is %default.""",
    )

    options, positional_args = parser.parse_args()

    if positional_args:
        return tools_logger.sysexit(
            "This command takes no positional arguments, check help output."
        )

    return options


def main():
    options = parseArgs()

    branch_name = checkBranchName()
    assert branch_name == "main"

    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("build", ignore_errors=True)

    copySourceForDebianBuild(source_path=os.getcwd())

    cleanupSourceDistributionState()

    checkReleaseDocumentation(assume_yes_for_downloads=options.assume_yes_for_downloads)

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

    # Then run "py2dsc" on it.

    for _fullname, filename in listDir("."):
        if filename.endswith(".tar.gz"):
            new_name = filename[:-7] + "+ds.tar.gz"

            cleanupTarfileForDebian(
                codename="sid",
                filename=filename,
                new_name=new_name,
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
