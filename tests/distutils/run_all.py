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

import os
import sys
import subprocess

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
from nuitka.tools.testing.Common import (
    my_print,
    setup,
    compareWithCPython,
    createSearchMode,
    decideFilenameVersionSkip
)
from nuitka.tools.testing.Virtualenv import withVirtualenv
from nuitka.utils.FileOperations import removeDirectory


python_version = setup(needs_io_encoding = True)

search_mode = createSearchMode()

nuitka_dir = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))

for filename in sorted(os.listdir('.')):
    if not os.path.isdir(filename) or \
       filename.endswith(".build") or \
       filename.endswith(".dist"):
        continue

    filename = os.path.relpath(filename)

    if not decideFilenameVersionSkip(filename):
        continue

    active = search_mode.consider(
        dirname  = None,
        filename = filename
    )



    if active:
        my_print("Consider distutils example:", filename)

        case_dir = os.path.join(os.getcwd(), filename)

        removeDirectory(os.path.join(case_dir, "build"), ignore_errors = False)
        removeDirectory(os.path.join(case_dir, "dist"), ignore_errors = False)

        with withVirtualenv("venv_cpython") as venv:
            venv.runCommand("cd %r; python setup.py install" % case_dir)

            process = subprocess.Popen(
                args   = os.path.join(venv.getVirtualenvDir(), "bin", "runner"),
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )

            stdout_cpython, stderr_cpython = process.communicate()
            exit_cpython = process.returncode

            print("STDOUT CPython:")
            print(stdout_cpython)
            print("STDERR CPython:")
            print(stderr_cpython)

            assert exit_cpython == 0, exit_cpython
            print("EXIT was OK.")

        removeDirectory(os.path.join(case_dir, "build"), ignore_errors = False)
        removeDirectory(os.path.join(case_dir, "dist"), ignore_errors = False)

        with withVirtualenv("venv_nuitka") as venv:
            # Install nuitka from source.
            venv.runCommand("cd %r; python setup.py install; rm -rf Nuitka.egg-info" % nuitka_dir)

            # Create the wheel
            venv.runCommand("cd %r; python setup.py bdist_nuitka; pip install dist/*.whl" % case_dir)

            process = subprocess.Popen(
                args   = os.path.join(venv.getVirtualenvDir(), "bin", "runner"),
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )

            stdout_nuitka, stderr_nuitka = process.communicate()
            exit_nuitka = process.returncode

            print("STDOUT Nuitka:")
            print(stdout_cpython)
            print("STDERR Nuitka:")
            print(stderr_cpython)

            assert exit_nuitka == 0, exit_nuitka
            print("EXIT was OK.")


search_mode.finish()
