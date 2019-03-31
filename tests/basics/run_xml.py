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

from __future__ import print_function

import os, sys, subprocess, tempfile, shutil

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            ".."
        )
    )
)

from nuitka.tools.testing.Common import check_output

# Go its own directory, to have it easy with path knowledge.
nuitka1 = sys.argv[1]
nuitka2 = sys.argv[2]

search_mode = len(sys.argv) > 3 and sys.argv[3] == "search"
start_at = sys.argv[4] if len(sys.argv) > 4 else None

if start_at:
    active = False
else:
    active = True

my_dir = os.path.dirname(os.path.abspath(__file__))

for filename in sorted(os.listdir(my_dir)):
    if not filename.endswith(".py") or filename.startswith("run_"):
        continue

    path = os.path.relpath(os.path.join(my_dir, filename))

    if not active and start_at in (filename, path):
        active = True

    if active:
        command = "%s %s '%s' '%s' %s" % (
            sys.executable,
            os.path.join(my_dir, "..", "..", "bin", "compare_with_xml"),
            nuitka1,
            nuitka2,
            path,
        )

        result = subprocess.call(
            command,
            shell = True
        )

        if result == 2:
            sys.stderr.write("Interrupted, with CTRL-C\n")
            sys.exit(2)

        if result != 0 and search_mode:
            print("Error exit!", result)
            sys.exit(result)
    else:
        print("Skipping", filename)
