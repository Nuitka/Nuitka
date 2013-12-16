#!/usr/bin/env python
#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os, sys, shutil

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
    compareWithCPython,
    decideFilenameVersionSkip,
    getRuntimeTraceOfLoadedFiles
)

python_version = setup()

search_mode = len( sys.argv ) > 1 and sys.argv[1] == "search"

start_at = sys.argv[2] if len( sys.argv ) > 2 else None

if start_at:
    active = False
else:
    active = True

for filename in sorted(os.listdir( "." )):
    if not filename.endswith( ".py" ):
        continue

    if not decideFilenameVersionSkip(filename):
        continue

    path = os.path.relpath(filename)

    if not active and start_at in (filename, path):
        active = True

    extra_flags = [
        "expect_success",
        "standalone",
        "remove_output"
    ]

    if filename == "PySideUsing.py":
        # Don't test on platforms not supported by current Debian testing, and
        # which should be considered irrelevant by now.
        if python_version.startswith("2.6") or python_version.startswith("3.2"):
            my_print("Skipping", filename, "not relevant.")
            continue

        # For the warnings.
        extra_flags.append( "ignore_stderr" )

    if filename not in ( "PySideUsing.py" ):
        extra_flags += [ "no_site" ]

    if active:
        my_print("Consider output of recursively compiled program:", filename)

        # First compare so we know the program behaves identical.
        compareWithCPython(
            path        = filename,
            extra_flags = extra_flags,
            # Do not expect PySide to work yet, because it has that bug still
            # where it won't call compiled functions as slots.
            search_mode = search_mode and not filename == "PySideUsing.py",
            needs_2to3  = False
        )

        # Second use strace on the result.
        loaded_filenames = getRuntimeTraceOfLoadedFiles(
            path = os.path.join(
                filename[:-3] + ".dist",
                filename[:-3] + ".exe"
            )
        )

        current_dir = os.path.normpath(os.getcwd())

        illegal_access = False

        for loaded_filename in loaded_filenames:
            loaded_filename = os.path.normpath(loaded_filename)

            if loaded_filename.startswith(current_dir):
                continue

            if loaded_filename.startswith("/etc/"):
                continue

            if loaded_filename.startswith("/proc/"):
                continue

            if loaded_filename.startswith("/dev/"):
                continue

            if loaded_filename.startswith( "/usr/lib/locale/" ):
                continue

            if loaded_filename.startswith( "/usr/share/locale/" ):
                continue

            if loaded_filename.startswith("/lib/libdl.") or \
               loaded_filename.startswith("/lib64/libdl."):
                continue

            if loaded_filename.startswith("/lib/libm.") or \
               loaded_filename.startswith("/lib64/libm."):
                continue

            if loaded_filename.startswith("/lib/libutil.") or \
               loaded_filename.startswith("/lib64/libutil."):
                continue

            if loaded_filename.startswith("/lib/libpthread.") or \
               loaded_filename.startswith("/lib64/libpthread."):
                continue

            # Loaded by C library potentially for DNS lookups.
            if os.path.basename(loaded_filename).startswith("libnss_") or \
               os.path.basename(loaded_filename).startswith("libnsl"):
                continue

            if loaded_filename.startswith("/home/") or \
               loaded_filename.startswith("/data/") or \
               loaded_filename in ("/home", "/data"):
                continue

            if os.path.basename(loaded_filename) == "gconv-modules.cache":
                continue

            if loaded_filename == "/usr/lib/python" + python_version[:3] + \
              "/dist-packages/PySide":
                continue

            my_print("Should not access '%s'." % loaded_filename)
            illegal_access = True

        if illegal_access:
            sys.exit(1)

        shutil.rmtree(filename[:-3] + ".dist")
    else:
        my_print( "Skipping", filename )
