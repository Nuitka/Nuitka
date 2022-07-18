#!/usr/bin/env python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

""" Runner for Python PGO tests of Nuitka.

PGO tests attempt to cover inclusion/non-inclusion of code and detection of
types.

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
    scanDirectoryForTestCaseFolders,
    setup,
)


def main():
    setup(suite="pgo", needs_io_encoding=True)

    search_mode = createSearchMode()

    # Now run all the tests in this directory.
    for filename, filename_main in scanDirectoryForTestCaseFolders("."):

        active = search_mode.consider(dirname=None, filename=filename)

        if active:
            extra_flags = [
                # No error exits normally, unless we break tests, and that we would
                # like to know.
                "expect_success",
                # Keep no temporary files.
                "remove_output",
                # Include imported files, PGO will then have to deal with unused ones.
                "--follow-imports",
                # The output during compilation from PGO capture is harmful, so
                # split compilation and execution of final result.
                "two_step_execution",
                # Inclusion report is used by the testing of expected things included
                # or not.
                "--report=%s.xml" % filename,
                # Cache the CPython results for re-use, they will normally not change.
                "cpython_cache",
            ]

            compareWithCPython(
                dirname=filename,
                filename=filename_main,
                extra_flags=extra_flags,
                search_mode=search_mode,
                needs_2to3=False,
            )

    search_mode.finish()


if __name__ == "__main__":
    main()
