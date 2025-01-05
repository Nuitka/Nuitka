#!/usr/bin/env python
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Runner for package tests of Nuitka.

Package tests are typically aiming at checking specific module constellations
in module mode and making sure the details are being right there. These are
synthetic small packages, each of which try to demonstrate one or more points
or special behavior.

"""


import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

from nuitka.tools.testing.Common import (
    compareWithCPython,
    createSearchMode,
    getTempDir,
    my_print,
    scanDirectoryForTestCaseFolders,
    setup,
)
from nuitka.utils.FileOperations import getSubDirectories, relpath


def main():
    setup(suite="packages")

    search_mode = createSearchMode()

    for filename, filename_main in scanDirectoryForTestCaseFolders(
        ".", allow_none=True
    ):
        active = search_mode.consider(dirname=None, filename=filename)

        if filename_main is None:
            filename_main = relpath(path=getSubDirectories(filename)[0], start=filename)

        if active:
            my_print("Consider output of compiled package:", filename)

            extra_flags = [
                "--mode=module",
                "expect_success",
                "remove_output",
                "two_step_execution",
            ]

            extra_flags.append("--output-dir=%s" % getTempDir())

            # TODO: This mismatches a rename and means the test is never
            # actually ran.
            if filename == "top_level_attributes":
                extra_flags.append("--mode=module-entry-point=main")

            compareWithCPython(
                dirname=filename,
                filename=filename_main,
                extra_flags=extra_flags,
                search_mode=search_mode,
            )

    search_mode.finish()


if __name__ == "__main__":
    main()

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
