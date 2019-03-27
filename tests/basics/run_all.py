#!/usr/bin/env python
#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)


from nuitka.tools.testing.Common import (
    my_print,
    setup,
    decideFilenameVersionSkip,
    compareWithCPython,
    hasDebugPython,
    createSearchMode
)

python_version = setup(suite="basics", needs_io_encoding=True)

search_mode = createSearchMode()

# Create large constants test on the fly, if it's not there, not going to
# add it to release archives for no good reason.
if not os.path.exists("BigConstants.py"):
    with open("BigConstants.py", "w") as output:
        output.write("# Automatically generated test, not part of releases or git.\n\n")
        output.write("print('%s')\n" % ("1234" * 17000))

# Now run all the tests in this directory.
for filename in sorted(os.listdir(".")):
    if not filename.endswith(".py"):
        continue

    if not decideFilenameVersionSkip(filename):
        continue

    extra_flags = [
        # No error exits normally, unless we break tests, and that we would
        # like to know.
        "expect_success",
        # Keep no temporary files.
        "remove_output",
        # Include imported files, mostly nothing though.
        "recurse_all",
        # Use the original __file__ value, at least one case warns about things
        # with filename included.
        "original_file",
        # Cache the CPython results for re-use, they will normally not change.
        "cpython_cache",
    ]

    # This test should be run with the debug Python, and makes outputs to
    # standard error that might be ignored.
    if filename.startswith("Referencing"):
        extra_flags.append("python_debug")

        extra_flags.append("recurse_not:nuitka")

    # This tests warns about __import__() used.
    if filename == "OrderChecks.py":
        extra_flags.append("ignore_warnings")

    # This tests warns about an package relative import despite
    # being in no package.
    if filename == "Importing.py":
        extra_flags.append("ignore_warnings")

    # TODO: Nuitka does not give output for ignored exception in dtor, this is
    # not fully compatible and potentially an error.
    if filename == "YieldFrom33.py":
        extra_flags.append("ignore_stderr")

    # For Python2 there is a "builtins" package that gives warnings. TODO: We
    # ought to NOT import that package and detect statically that __builtins__
    # import won't raise ImportError.
    if filename == "BuiltinOverload.py":
        extra_flags.append("ignore_warnings")

    active = search_mode.consider(dirname=None, filename=filename)

    if active:
        if filename.startswith("Referencing") and not hasDebugPython():
            my_print("Skipped (no debug Python)")
            continue

        needs_2to3 = (
            python_version.startswith("3")
            and not filename.endswith("32.py")
            and not filename.endswith("33.py")
            and not filename.endswith("35.py")
            and not filename.endswith("36.py")
        )

        compareWithCPython(
            dirname=None,
            filename=filename,
            extra_flags=extra_flags,
            search_mode=search_mode,
            needs_2to3=needs_2to3,
        )
    else:
        my_print("Skipping", filename)

search_mode.finish()
