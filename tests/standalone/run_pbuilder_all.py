#!/usr/bin/env python
#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

import subprocess
import sys
import os
import tempfile

nuitka_dir = os.path.normcase(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
my_dir = os.path.dirname(os.path.abspath(__file__))

verbose = False

code_names = []

for filename in os.listdir("/var/cache/pbuilder/"):
    if not filename.endswith(".tgz"):
        continue

    code_names.append(filename[:-4])

if not code_names:
    sys.exit("Error, found no pbuilder images.")

code_names.sort()

print("Working on:", ",".join(code_names))

# For build the test case with everything.
if True:
    for code_name in code_names:
        subprocess.check_call(
            [
                os.path.join(my_dir, "run_pbuilder.py"),
                code_name,
                "1" if verbose else "0"
            ]
        )


# Running on host machine, for basic overview.
error = False
for code_name in code_names:
    exit_code = subprocess.call(
        [
            "./Asserts-%s.dist/Asserts.exe" % code_name
        ],
        stdout = open("/dev/null") if not verbose else sys.stdout,
        stderr = subprocess.STDOUT
    )

    if exit_code:
        print(code_name.title(), "FAIL")
        error = True
    else:
        print(code_name.title(), "OK")


if not error:
    with tempfile.NamedTemporaryFile("w", delete = False) as script_file:
        script_file.write("cd %s\n" % nuitka_dir)
        for code_name in code_names:
            script_file.write(
                """\
(./Asserts-%(code_name)s.dist/Asserts.exe >/dev/null && echo %(code_name)s OK) || \
echo %(code_name)s FAIL\n""" % {"code_name" : code_name}
            )

        tmp_script = script_file.name

    try:
        for code_name in code_names:
            print("CHECK", code_name, ":")
            subprocess.check_call(
                [
                    "sudo",
                    "pbuilder",
                    "--execute",
                    "--basetgz",
                    "/var/cache/pbuilder/" + code_name + ".tgz",
                    "--bindmounts", nuitka_dir,
                    tmp_script
                ]
            )
    finally:
        os.unlink(tmp_script)
