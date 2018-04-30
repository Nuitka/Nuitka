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

import subprocess
import sys
import os
import tempfile
import shutil
import getpass

nuitka_dir = os.path.normcase(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

code_name = sys.argv[1]
verbose = int(sys.argv[2])

if not verbose:
    sys.stdout = open("/dev/null")
    sys.stderr = open("/dev/null")

shutil.rmtree("Asserts-%s.build" % code_name, ignore_errors = True)
shutil.rmtree("Asserts-%s.dist" % code_name, ignore_errors = True)

with tempfile.NamedTemporaryFile("w", delete = False) as script_file:
    script_file.write("apt-get install -y lsb-release python python-dev\n")
    script_file.write("CODE_NAME=`lsb_release -c -s`\n")
    script_file.write('echo Hello pbuilder for "$CODE_NAME".\n')
    script_file.write("cd %s\n" % nuitka_dir)
    script_file.write("python bin/nuitka --python-flag=-S --standalone tests/basics/Asserts.py\n")

#    script_file.write("python3 bin/nuitka --standalone tests/basics/Asserts.py\n")

    tmp_script = script_file.name

try:
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

    shutil.move(
        "Asserts.build",
        "Asserts-%s.build" % code_name
    )
    shutil.move(
        "Asserts.dist",
        "Asserts-%s.dist" % code_name
    )

    subprocess.check_call(
        [
            "sudo",
            "chown",
            "-R",
            getpass.getuser() + ":",
            "Asserts-%s.build" % code_name,
            "Asserts-%s.dist" % code_name
        ]
    )

finally:
    os.unlink(tmp_script)
