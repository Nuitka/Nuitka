#!/usr/bin/env python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

import os, sys, tempfile, subprocess

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
    setup,               # @UnresolvedImport
    my_print,            # @UnresolvedImport
    createSearchMode,    # @UnresolvedImport
    compareWithCPython,  # @UnresolvedImport
    compileLibraryTest   # @UnresolvedImport
)

setup(needs_io_encoding = True)
search_mode = createSearchMode()

tmp_dir = tempfile.gettempdir()

# Try to avoid RAM disk /tmp and use the disk one instead.
if tmp_dir == "/tmp" and os.path.exists("/var/tmp"):
    tmp_dir = "/var/tmp"

blacklist = (
    "__phello__.foo.py", # Triggers error for "." in module name
    "idnadata"           # Avoid too complex code for main program.
)

def decide(root, filename):
    return filename.endswith(".py") and \
           filename not in blacklist and \
           '(' not in filename

def action(stage_dir, root, path):
    command = [
        sys.executable,
        os.path.join(
            "..",
            "..",
            "bin",
            "nuitka"
        ),
        "--module",
        "--output-dir",
        stage_dir,
        "--recurse-none",
        "--remove-output"
    ]

    command += os.environ.get("NUITKA_EXTRA_OPTIONS", "").split()

    command.append(path)

    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        my_print("Falling back to full comparison due to error exit.")
        compareWithCPython(
            dirname     = None,
            filename    = path,
            extra_flags = ["expect_failure"],
            search_mode = search_mode,
            needs_2to3  = False
        )
    else:
        my_print("OK")

        if os.name == "nt":
            suffix = "pyd"
        else:
            suffix = "so"

        target_filename = os.path.basename(path).replace(".py",'.'+suffix)
        target_filename = target_filename.replace('(',"").replace(')',"")

        os.unlink(
            os.path.join(
                stage_dir, target_filename
            )
        )



compileLibraryTest(
    search_mode = search_mode,
    stage_dir   = os.path.join(tmp_dir, "compile_library"),
    decide      = decide,
    action      = action
)

