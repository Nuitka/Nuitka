#!/usr/bin/env python
#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Runner for distutils integration

Tests for example packages demonstrating that wheel creation with Nuitka
is compatible to standard packaging tools.

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

from nuitka.tools.environments.Virtualenv import (
    NuitkaCalledProcessError,
    withVirtualenv,
)
from nuitka.tools.testing.Common import (
    createSearchMode,
    my_print,
    reportSkip,
    scanDirectoryForTestCaseFolders,
    setup,
    test_logger,
)
from nuitka.tools.testing.OutputComparison import compareOutput
from nuitka.utils.FileOperations import (
    deleteFile,
    getFileContents,
    putTextFileContents,
    removeDirectory,
)


def _adaptPyProjectFile(case_dir, source_filename):
    pyproject_filename = os.path.join(case_dir, "pyproject.toml")

    putTextFileContents(
        filename=pyproject_filename,
        contents=getFileContents(os.path.join(case_dir, source_filename)).replace(
            "file:../../..",
            "file:%s"
            % (
                os.path.abspath(os.path.join(case_dir, "..", "..", "..")).replace(
                    "\\", "/"
                )
            ),
        ),
    )

    return pyproject_filename


def _handleCase(python_version, nuitka_dir, filename):
    # Complex stuff, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    my_print("Consider distutils example: '%s'" % filename, style="blue")

    if filename == "example_2_pyproject":
        reportSkip(
            "Skipped, 'poetry' based pyproject is not working for now",
            ".",
            filename,
        )
        return

    is_pyproject = "_pyproject" in filename

    if is_pyproject and python_version < (3,):
        reportSkip(
            "Skipped, pyproject cases are not for Python2",
            ".",
            filename,
        )
        return

    case_dir = os.path.join(os.getcwd(), filename)

    removeDirectory(
        os.path.join(case_dir, "build"),
        logger=test_logger,
        ignore_errors=False,
        extra_recommendation=None,
    )
    removeDirectory(
        os.path.join(case_dir, "dist"),
        logger=test_logger,
        ignore_errors=False,
        extra_recommendation=None,
    )

    with withVirtualenv("venv_cpython", logger=test_logger) as venv:
        if is_pyproject:
            venv.runCommand("pip install build")

            pyproject_filename = _adaptPyProjectFile(
                case_dir=case_dir, source_filename="pyproject.cpython.toml"
            )

            venv.runCommand(commands=['cd "%s"' % case_dir, "python -m build"])
            deleteFile(pyproject_filename, must_exist=True)
        else:
            venv.runCommand("pip install setuptools wheel")

            venv.runCommand(
                commands=['cd "%s"' % case_dir, "python setup.py bdist_wheel"]
            )

        dist_dir = os.path.join(case_dir, "dist")

        venv.runCommand(
            'pip install "%s"' % (os.path.join(dist_dir, os.listdir(dist_dir)[0]))
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

    removeDirectory(
        os.path.join(case_dir, "build"),
        logger=test_logger,
        ignore_errors=False,
        extra_recommendation=None,
    )
    removeDirectory(
        os.path.join(case_dir, "dist"),
        logger=test_logger,
        ignore_errors=False,
        extra_recommendation=None,
    )

    with withVirtualenv("venv_nuitka", logger=test_logger) as venv:
        # Create the wheel with Nuitka compilation.
        if is_pyproject:
            venv.runCommand("pip install build")

            pyproject_filename = _adaptPyProjectFile(
                case_dir=case_dir, source_filename="pyproject.nuitka.toml"
            )

            venv.runCommand(commands=['cd "%s"' % case_dir, "python -m build -w"])

            deleteFile(pyproject_filename, must_exist=True)
        else:
            venv.runCommand("pip install setuptools wheel")
            # Install nuitka from source so "bdist_nuitka" can work.

            try:
                venv.runCommand(
                    commands=['cd "%s"' % nuitka_dir, "python setup.py install"],
                    style="test-prepare",
                    env={"PYTHONWARNINGS": "ignore"},
                )
            finally:
                # Remove that left over from the install command.
                removeDirectory(
                    path=os.path.join(nuitka_dir, "Nuitka.egg-info"),
                    logger=test_logger,
                    ignore_errors=False,
                    extra_recommendation=None,
                )

            venv.runCommand(
                commands=['cd "%s"' % case_dir, "python setup.py bdist_nuitka"]
            )

        dist_dir = os.path.join(case_dir, "dist")
        venv.runCommand(
            'pip install "%s"' % (os.path.join(dist_dir, os.listdir(dist_dir)[0]))
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


def main():
    python_version = setup(suite="distutils", needs_io_encoding=True)

    search_mode = createSearchMode()

    nuitka_dir = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))

    for filename, _filename_main in scanDirectoryForTestCaseFolders("."):
        active = search_mode.consider(dirname=None, filename=filename)

        if active:
            try:
                _handleCase(python_version, nuitka_dir, filename)
            except NuitkaCalledProcessError:
                test_logger.sysexit("Error in test case '%s'." % filename)

    search_mode.finish()


if __name__ == "__main__":
    main()

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
