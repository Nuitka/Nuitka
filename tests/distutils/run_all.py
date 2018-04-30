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
    createSearchMode,
    decideFilenameVersionSkip
)

from nuitka.tools.testing.OutputComparison import compareOutput
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
            venv.runCommand(
                commands = [
                    'cd "%s"' % case_dir,
                    "python setup.py bdist_wheel",
                ]
            )

            dist_dir = os.path.join(case_dir, "dist")

            venv.runCommand(
                'pip install "%s"' % (
                    os.path.join(
                        dist_dir,
                        os.listdir(dist_dir)[0]
                    )
                )
            )

            # Need to call CPython binary for Windows.
            process = subprocess.Popen(
                args   = [
                    sys.executable,
                    os.path.join(venv.getVirtualenvDir(), "bin" if os.name != "nt" else "scripts", "runner")
                ],
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
            venv.runCommand(
                commands = [
                    'cd "%s"' % nuitka_dir,
                    "python setup.py install",
                ]
            )

            # Remove that left over from the install command.
            removeDirectory(
                path          = os.path.join(nuitka_dir, "Nuitka.egg-info"),
                ignore_errors = False
            )

            # Create the wheel with Nuitka compilation.
            venv.runCommand(
                commands = [
                    'cd "%s"' % case_dir,
                    "python setup.py bdist_nuitka"
                ]
            )

            dist_dir = os.path.join(case_dir, "dist")
            venv.runCommand(
                'pip install "%s"' % (
                    os.path.join(
                        dist_dir,
                        os.listdir(dist_dir)[0]
                    )
                )
            )

            process = subprocess.Popen(
                args   = [
                    sys.executable,
                    os.path.join(venv.getVirtualenvDir(), "bin" if os.name != "nt" else "scripts", "runner")
                ],
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

        exit_code_stdout = compareOutput(
            "stdout",
            stdout_cpython,
            stdout_nuitka,
            ignore_warnings = True,
            ignore_infos    = True,
            syntax_errors   = True
        )

        exit_code_stderr = compareOutput(
            "stderr",
            stderr_cpython,
            stderr_nuitka,
            ignore_warnings = True,
            ignore_infos    = True,
            syntax_errors   = True
        )

        exit_code_return = exit_cpython != exit_nuitka

        if exit_code_return:
            my_print(
                """\
Exit codes {exit_cpython:d} (CPython) != {exit_nuitka:d} (Nuitka)""".format(
                    exit_cpython = exit_cpython,
                    exit_nuitka  = exit_nuitka
                )
            )

        exit_code = exit_code_stdout or exit_code_stderr or exit_code_return

        if exit_code:
            sys.exit("Error, outputs differed.")

search_mode.finish()
