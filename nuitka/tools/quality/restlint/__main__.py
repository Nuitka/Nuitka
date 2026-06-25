#!/usr/bin/env python
#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Main program for restlint checker tool."""

import sys

from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.tools.Basics import addPYTHONPATH, getHomePath, goHome
from nuitka.tools.release.Documentation import (
    checkReleaseDocumentation,
    checkRstLint,
)
from nuitka.tools.testing.Common import hasModule, setup
from nuitka.Tracing import tools_logger
from nuitka.utils.PrivatePipSpace import tryDownloadPackageName


def main():
    setup(go_main=False)

    addPYTHONPATH(getHomePath())
    parser = makeOptionsParser(usage="%prog [options]", epilog=None)

    parser.add_option(
        "--assume-yes-for-downloads",
        action="store_true",
        dest="assume_yes_for_downloads",
        default=False,
        help="""\
Allow download and execution of tools if needed. Default is %default.""",
    )

    options, positional_args = parser.parse_args()

    if options.assume_yes_for_downloads:
        if not hasModule("restructuredtext_lint"):
            tools_logger.info("Installing restlint...")

            site_packages_folder, _assume_yes_for_downloads = tryDownloadPackageName(
                logger=tools_logger,
                package_name="restructuredtext_lint",
                module_name="restructuredtext_lint",
                package_version=None,
                force_update=False,
                assume_yes_for_downloads=True,
                reject_message="Restlint is needed for checking source code.",
            )

            if site_packages_folder is not None:
                sys.path.insert(0, site_packages_folder)

        if not hasModule("pygments"):
            tools_logger.info("Installing pygments...")

            site_packages_folder, _assume_yes_for_downloads = tryDownloadPackageName(
                logger=tools_logger,
                package_name="pygments",
                module_name="pygments",
                package_version=None,
                force_update=False,
                assume_yes_for_downloads=True,
                reject_message="Pygments is needed for RST code block analysis.",
            )

            if site_packages_folder is not None:
                sys.path.insert(0, site_packages_folder)

    if len(positional_args) < 1:
        goHome()
        checkReleaseDocumentation()
    else:
        for document in positional_args:
            checkRstLint(document)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
