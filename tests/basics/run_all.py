#!/usr/bin/env python
#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

""" Runner for basic tests of Nuitka.

Basic tests are those that cover our back quickly, but need not necessarily,
be complete.

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
    decideNeeds2to3,
    getDebugPython,
    scanDirectoryForTestCases,
    setup,
)


def main():
    setup(suite="basics", needs_io_encoding=True)

    search_mode = createSearchMode()

    # Now run all the tests in this directory.
    for filename in scanDirectoryForTestCases("."):
        extra_flags = [
            # No error exits normally, unless we break tests, and that we would
            # like to know.
            "expect_success",
            # Keep no temporary files.
            "remove_output",
            # Do not follow imports.
            "--nofollow-imports",
            # Use the original __file__ value, at least one case warns about things
            # with filename included.
            "--file-reference-choice=original",
            # Cache the CPython results for re-use, they will normally not change.
            "cpython_cache",
            # To understand what is slow.
            "timing",
            # We annotate some tests, use that to lower warnings.
            "plugin_enable:pylint-warnings",
        ]

        # This test should be run with the debug Python, and makes outputs to
        # standard error that might be ignored.
        if filename.startswith("Referencing") and getDebugPython() is not None:
            extra_flags.append("--python-debug")

        # This tests warns about __import__() used.
        if filename == "OrderChecksTest.py":
            extra_flags.append("ignore_warnings")

        # This tests warns about an package relative import despite
        # being in no package.
        if filename == "ImportingTest.py":
            extra_flags.append("ignore_warnings")

        # TODO: Nuitka does not give output for ignored exception in dtor, this is
        # not fully compatible and potentially an error.
        if filename == "YieldFromTest33.py":
            extra_flags.append("ignore_stderr")

        # For Python2 there is a "builtins" package that gives warnings. TODO: We
        # ought to NOT import that package and detect statically that __builtins__
        # import won't raise ImportError.
        if filename == "BuiltinOverloadTest.py":
            extra_flags.append("ignore_warnings")

        active = search_mode.consider(dirname=None, filename=filename)

        if active:
            compareWithCPython(
                dirname=None,
                filename=filename,
                extra_flags=extra_flags,
                search_mode=search_mode,
                needs_2to3=decideNeeds2to3(filename),
            )

    search_mode.finish()


if __name__ == "__main__":
    main()
