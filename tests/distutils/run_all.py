#!/usr/bin/env python
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

""" Runner for distutils integration

Tests for example packages demonstrating that wheel creation with Nuitka
is compatible to normal packaging.

"""

import os
import sys

# Find nuitka package relative to us. The replacement is for POSIX python
# and Windows paths on command line.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__.replace("\\", os.sep))), "..", ".."
        )
    ),
)

# isort:start

import subprocess

from nuitka.tools.testing.Common import (
    createSearchMode,
    decideFilenameVersionSkip,
    my_print,
    reportSkip,
    setup,
)
from nuitka.tools.testing.OutputComparison import compareOutput
from nuitka.tools.testing.Virtualenv import withVirtualenv
from nuitka.utils.FileOperations import copyFile, deleteFile, removeDirectory


def main():
    # Complex stuff, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    python_version = setup(suite="distutils", needs_io_encoding=True)

    search_mode = createSearchMode()

    nuitka_dir = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))

    for filename in sorted(os.listdir(".")):
        if (
            not os.path.isdir(filename)
            or filename.endswith((".build", ".dist"))
            or filename.startswith("venv_")
        ):
            continue

        filename = os.path.relpath(filename)

        if not decideFilenameVersionSkip(filename):
            continue

        active = search_mode.consider(dirname=None, filename=filename)

        if active:
            my_print("Consider distutils example:", filename)

            py3_only_examples = ("example_3", "nested_namespaces")
            if python_version < (3,) and (
                filename in py3_only_examples or "_pyproject_" in filename
            ):
                reportSkip("Skipped, only relevant for Python3", ".", filename)
                continue

            if filename == "example_pyproject_2":
                reportSkip(
                    "Skipped, 'poetry' based pyproject is now working for now",
                    ".",
                    filename,
                )
                continue

            case_dir = os.path.join(os.getcwd(), filename)

            removeDirectory(os.path.join(case_dir, "build"), ignore_errors=False)
            removeDirectory(os.path.join(case_dir, "dist"), ignore_errors=False)

            with withVirtualenv("venv_cpython") as venv:
                if "_pyproject_" not in filename:
                    venv.runCommand(
                        commands=['cd "%s"' % case_dir, "python setup.py bdist_wheel"]
                    )

                else:
                    venv.runCommand("pip install build")

                    copyFile(
                        source_path=os.path.join(case_dir, "pyproject.cpython.toml"),
                        dest_path=os.path.join(case_dir, "pyproject.toml"),
                    )
                    venv.runCommand(commands=['cd "%s"' % case_dir, "python -m build"])
                    deleteFile(
                        os.path.join(case_dir, "pyproject.toml"), must_exist=True
                    )

                dist_dir = os.path.join(case_dir, "dist")

                venv.runCommand(
                    'pip install "%s"'
                    % (os.path.join(dist_dir, os.listdir(dist_dir)[0]))
                )

                runner_binary = os.path.join(
                    venv.getVirtualenvDir(),
                    "bin" if os.name != "nt" else "scripts",
                    "runner",
                )

                # TODO: Is this something to be abstracted into a function.
                # pylint: disable=consider-using-with

                if os.path.exists(runner_binary):
                    # Need to call CPython binary for Windows.
                    process = subprocess.Popen(
                        args=[
                            os.path.join(
                                venv.getVirtualenvDir(),
                                "bin" if os.name != "nt" else "scripts",
                                "python",
                            ),
                            os.path.join(
                                venv.getVirtualenvDir(),
                                "bin" if os.name != "nt" else "scripts",
                                "runner",
                            ),
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                else:
                    assert os.path.exists(runner_binary + ".exe")

                    process = subprocess.Popen(
                        args=[runner_binary + ".exe"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                stdout_cpython, stderr_cpython = process.communicate()
                exit_cpython = process.returncode

                my_print("STDOUT CPython:")
                my_print(stdout_cpython)
                my_print("STDERR CPython:")
                my_print(stderr_cpython)

                assert exit_cpython == 0, exit_cpython
                my_print("EXIT was OK.")

            removeDirectory(os.path.join(case_dir, "build"), ignore_errors=False)
            removeDirectory(os.path.join(case_dir, "dist"), ignore_errors=False)

            with withVirtualenv("venv_nuitka") as venv:
                # Install nuitka from source.
                venv.runCommand(
                    commands=['cd "%s"' % nuitka_dir, "python setup.py install"],
                    style="test-prepare",
                )

                # Remove that left over from the install command.
                removeDirectory(
                    path=os.path.join(nuitka_dir, "Nuitka.egg-info"),
                    ignore_errors=False,
                )

                # Create the wheel with Nuitka compilation.
                if "_pyproject_" not in filename:
                    venv.runCommand(
                        commands=['cd "%s"' % case_dir, "python setup.py bdist_nuitka"]
                    )
                else:
                    venv.runCommand("pip install build")

                    copyFile(
                        source_path=os.path.join(case_dir, "pyproject.nuitka.toml"),
                        dest_path=os.path.join(case_dir, "pyproject.toml"),
                    )
                    venv.runCommand(commands=['cd "%s"' % case_dir, "python -m build"])
                    deleteFile(
                        os.path.join(case_dir, "pyproject.toml"), must_exist=True
                    )

                dist_dir = os.path.join(case_dir, "dist")
                venv.runCommand(
                    'pip install "%s"'
                    % (os.path.join(dist_dir, os.listdir(dist_dir)[0]))
                )

                runner_binary = os.path.join(
                    venv.getVirtualenvDir(),
                    "bin" if os.name != "nt" else "scripts",
                    "runner",
                )

                # TODO: Is this something to be abstracted into a function.
                # pylint: disable=consider-using-with

                if os.path.exists(runner_binary):
                    process = subprocess.Popen(
                        args=[
                            os.path.join(
                                venv.getVirtualenvDir(),
                                "bin" if os.name != "nt" else "scripts",
                                "python",
                            ),
                            runner_binary,
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                else:
                    assert os.path.exists(runner_binary + ".exe")

                    process = subprocess.Popen(
                        args=[runner_binary + ".exe"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                stdout_nuitka, stderr_nuitka = process.communicate()
                exit_nuitka = process.returncode

                my_print("STDOUT Nuitka:")
                my_print(stdout_nuitka)
                my_print("STDERR Nuitka:")
                my_print(stderr_nuitka)

                assert exit_nuitka == 0, exit_nuitka
                my_print("EXIT was OK.")

            exit_code_stdout = compareOutput(
                "stdout",
                stdout_cpython,
                stdout_nuitka,
                ignore_warnings=True,
                syntax_errors=True,
            )

            exit_code_stderr = compareOutput(
                "stderr",
                stderr_cpython,
                stderr_nuitka,
                ignore_warnings=True,
                syntax_errors=True,
            )

            exit_code_return = exit_cpython != exit_nuitka

            if exit_code_return:
                my_print(
                    """\
Exit codes {exit_cpython:d} (CPython) != {exit_nuitka:d} (Nuitka)""".format(
                        exit_cpython=exit_cpython, exit_nuitka=exit_nuitka
                    )
                )

            exit_code = exit_code_stdout or exit_code_stderr or exit_code_return

            if exit_code:
                sys.exit("Error, outputs differed.")

    search_mode.finish()


if __name__ == "__main__":
    main()
