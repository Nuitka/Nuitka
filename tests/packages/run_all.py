#!/usr/bin/env python
#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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
    reportSkip,
    setup,
)
from nuitka.Version import getCommercialVersion


def main():
    # Complex stuff, even more should become common code though.
    # pylint: disable=too-many-branches

    setup(suite="packages")

    search_mode = createSearchMode()

    for filename in sorted(os.listdir(".")):
        if not os.path.isdir(filename) or filename.endswith(".build"):
            continue

        extra_flags = [
            "--module",
            "expect_success",
            "remove_output",
            "two_step_execution",
        ]

        active = search_mode.consider(dirname=None, filename=filename)

        if active:
            my_print("Consider output of compiled package:", filename)

            if "embed" in filename and getCommercialVersion() is None:
                reportSkip(
                    "Skipped, only working with Nuitka commercial",
                    ".",
                    filename,
                )
                continue

            filename_main = None

            filename_main = os.path.join(
                filename, "".join(part.title() for part in filename.split("_")) + ".py"
            )
            if os.path.exists(filename_main):
                filename_main = os.path.basename(filename_main)
            else:
                filename_main = None

            if filename_main is None:
                for filename_main in os.listdir(filename):
                    if filename_main == "__pycache__":
                        continue

                    if not os.path.isdir(os.path.join(filename, filename_main)):
                        continue

                    if filename_main not in ("..", "."):
                        break
                else:
                    search_mode.onErrorDetected(
                        """\
Error, no package in test directory '%s' found, incomplete test case."""
                        % filename
                    )

                extra_flags.append(
                    "--include-package=%s" % os.path.basename(filename_main)
                )

            extra_flags.append("--output-dir=%s" % getTempDir())

            if filename == "top_level_attributes":
                extra_flags.append("--module-entry-point=main")

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
