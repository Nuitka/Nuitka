#!/usr/bin/env python
#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os, sys

# Find common code relative in file system. Not using packages for test stuff.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            ".."
        )
    )
)
from test_common import (
    my_print,
    setup,
    decideFilenameVersionSkip,
    compareWithCPython,
    hasDebugPython
)

python_version = setup(needs_io_encoding = True)

search_mode = len(sys.argv) > 1 and sys.argv[1] == "search"

start_at = sys.argv[2] if len( sys.argv ) > 2 else None

if start_at:
    active = False
else:
    active = True

# Create large constants test on the fly, if it's not there, not going to
# add it to release archives for no good reason.
if not os.path.exists( "BigConstants.py" ):
    with open( "BigConstants.py", "w" ) as output:
        output.write(
            "# Automatically generated test, not part of releases or git.\n\n"
        )
        output.write(
            "print('%s')\n" % ("1234" * 17000)
        )

# Now run all the tests in this directory.
for filename in sorted(os.listdir(".")):
    if not filename.endswith(".py"):
        continue

    if not decideFilenameVersionSkip(filename):
        continue

    # The overflow functions test gives syntax error on Python 3.x and will be
    # skiped as well.
    if filename == "OverflowFunctions.py" and python_version.startswith("3"):
        continue

    path = filename

    if not active and start_at in (filename, path):
        active = True

    extra_flags = ["expect_success", "remove_output"]

    # This test should be run with the debug Python, and makes outputs to
    # standard error that might be ignored.
    if filename.startswith( "Referencing" ):
        extra_flags.append( "python_debug" )

    # This tests warns about __import__() used.
    if filename == "OrderChecks.py":
        extra_flags.append( "ignore_stderr" )

    # TODO: Nuitka does not give output for ignored exception in dtor, this is
    # not fully compatible and potentially an error.
    if filename == "YieldFrom33.py":
        extra_flags.append("ignore_stderr")

    # These tests don't work with 3.4 yet, and the list is considered the major
    # TODO for 3.4 support.
    skips_34 = (
        # The "__class__" doesn't work as expected.
        "BuiltinSuper.py",

        # Dictionary order changes from star args usages
        "Constants.py",

        # Too little attributes for generator objects, "__del__" is missing it
        # seems.
        "GeneratorExpressions.py",

        # Order change for dictionary contraction"
        "ListContractions.py"
    )

    if active:
        if filename.startswith("Referencing") and not hasDebugPython():
            my_print("Skipped (no debug Python)")
            continue

        needs_2to3 = python_version.startswith("3") and \
                     not filename.endswith("32.py") and \
                     not filename.endswith("33.py")

        compareWithCPython(
            path        = path,
            extra_flags = extra_flags,
            search_mode = search_mode and not (
                filename in skips_34 and python_version.startswith("3.4")
            ),
            needs_2to3  = needs_2to3
        )
    else:
        my_print("Skipping", filename)
