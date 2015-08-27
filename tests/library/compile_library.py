#!/usr/bin/env python
#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
    my_print,            # @UnresolvedImport
    setup,               # @UnresolvedImport
    compareWithCPython,  # @UnresolvedImport
    createSearchMode     # @UnresolvedImport
)

python_version = setup(needs_io_encoding = True)

search_mode = createSearchMode()

start_at = sys.argv[2] if len(sys.argv) > 2 else None

if start_at:
    active = False
else:
    active = True

os_path = os.path.normcase(os.path.dirname(os.__file__))

my_print("Using standard library path", os_path)

try:
    import numpy

    extra_path = os.path.normcase(
        os.path.dirname(
            os.path.dirname(
                numpy.__file__
            )
        )
    )

    my_print("Using extra library path", extra_path)
except ImportError:
    extra_path = os_path

try:
    import matplotlib

    extra_path2 = os.path.normcase(
        os.path.dirname(
            os.path.dirname(
                matplotlib.__file__
            )
        )
    )

    my_print("Using extra2 library path", extra_path2)
except ImportError:
    extra_path2 = os_path

os_path = os.path.normpath(os_path)
extra_path = os.path.normpath(extra_path)

tmp_dir = tempfile.gettempdir()

# Try to avoid RAM disk /tmp and use the disk one instead.
if tmp_dir == "/tmp" and os.path.exists("/var/tmp"):
    tmp_dir = "/var/tmp"

stage_dir = os.path.join(tmp_dir, "compile_library")

blacklist = (
    "__phello__.foo.py", # Triggers error for "." in module name
)

def compilePath(path):
    global active

    for root, _dirnames, filenames in os.walk(path):
        filenames = [
            filename
            for filename in filenames
            if filename.endswith(".py")
            if filename not in blacklist
        ]

        for filename in sorted(filenames):
            if '(' in filename:
                continue

            path = os.path.join(root, filename)

            if not active and start_at in (filename, path):
                active = True

            if not active:
                continue

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
            my_print(path, ':', end = ' ')
            sys.stdout.flush()

            try:
                subprocess.check_call(command)
            except subprocess.CalledProcessError as e:
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

compilePath(os_path)

if extra_path != os_path:
    compilePath(extra_path)

if extra_path2 not in (os_path, extra_path):
    compilePath(extra_path2)
