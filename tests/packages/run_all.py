#!/usr/bin/env python
#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Softwar where
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

import os, sys

# Find common code relative in file system. Not using packages for test stuff.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname( os.path.abspath( __file__ ) ),
            ".."
        )
    )
)
from test_common import (
    my_print,
    setup,
    convertUsing2to3,
    compareWithCPython,
    getTempDir
)

python_version = setup()

search_mode = len( sys.argv ) > 1 and sys.argv[1] == "search"

start_at = sys.argv[2] if len( sys.argv ) > 2 else None

if start_at:
    active = False
else:
    active = True

for filename in sorted( os.listdir( "." ) ):
    if not os.path.isdir( filename ) or filename.endswith( ".build" ):
        continue

    path = os.path.relpath( filename )

    if not active and start_at in ( filename, path ):
        active = True

    extra_flags = [
        "expect_success",
        "remove_output",
        "module_mode",
        "two_step_execution"
    ]

    # The use of "__main__" in the test package gives a warning.
    if filename == "sub_package":
        extra_flags.append( "ignore_warnings" )

    if active:
        my_print( "Consider output of recursively compiled program:", path )

        for filename_main in os.listdir( filename ):
            if not os.path.isdir(os.path.join(filename,filename_main)):
                continue

            if filename_main not in ( "..", "." ):
                break
        else:
            sys.exit(
                """\
Error, no package in dir '%s' found, incomplete test case.""" % filename
            )

        os.environ[ "NUITKA_EXTRA_OPTIONS" ] = \
          "--recurse-to=%s" % os.path.basename(filename_main)

        os.environ[ "NUITKA_EXTRA_OPTIONS" ] += \
          " --output-dir=%s" % getTempDir()


        compareWithCPython(
            path        = os.path.join( filename, filename_main ),
            extra_flags = extra_flags,
            search_mode = search_mode,
            needs_2to3  = False
        )
    else:
        my_print( "Skipping", filename )
