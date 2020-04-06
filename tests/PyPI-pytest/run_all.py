#!/usr/bin/env python
#     Copyright 2020, Tommy Li, mailto:tommyli3318@gmail.com
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

""" Runner for PyPI Pytest comparison

This script automates the comparing of pytest results of a nuitka compiled wheel
using `python setup.py bdist_nuitka` to the pytest results of an uncompiled wheel
built using `python setup.py bdist_wheel` for the most popular PyPI packages.
Testing is done to ensure that nuitka is building the wheel correctly. If the
pytests pass/fail in the same way, that means Nuitka built the wheel properly.
Else if the tests differ, then something is wrong.
Virtualenv is used to create a clean environment with no outside pollution.

"""

import os
import sys
import json

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

import nuitka
from nuitka.tools.testing.Common import createSearchMode, my_print, reportSkip, setup
from nuitka.tools.testing.OutputComparison import compareOutput
from nuitka.tools.testing.Virtualenv import withVirtualenv
from nuitka.utils.AppDirs import getCacheDir


def executeCommand(command):
    my_print("Executing:", command, style="blue")

    return os.system(command) == 0


def gitClone(package, url, directory):
    """
    Update package with git if already existing in directory
    else git clone the package into directory
    """

    os.chdir(directory)
    if not executeCommand(
        "cd %s && git fetch -q && git reset -q --hard origin && git clean -q -dfx"
        % package
    ):
        assert executeCommand(
            "git clone %s %s --depth 1 --single-branch --no-tags" % (url, package)
        ), ("Error while git cloning package %s, aborting..." % package)


def main():
    # pylint: disable=broad-except,too-many-branches,too-many-locals,too-many-statements

    _python_version = setup()

    # cache_dir is where the git clones are cached
    cache_dir = os.path.join(getCacheDir(), "pypi-git-clones")
    base_dir = os.getcwd()

    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)

    search_mode = createSearchMode()

    results = []

    # load json
    with open("packages.json", "r") as f:
        packages = json.load(f)

    for package_name, details in sorted(packages.items()):
        active = search_mode.consider(dirname=None, filename=package_name)

        if not active:
            continue

        if str is not bytes:
            # running on python3
            if package_name in ("futures", "future"):
                reportSkip("Does not run on Python3", ".", package_name)
                if search_mode.abortIfExecuted():
                    break
                continue

        if os.name == "nt":
            if package_name in ("cryptography",):
                reportSkip("Not working on Windows", ".", package_name)
                if search_mode.abortIfExecuted():
                    break
                continue

        if package_name == "pyyaml":
            reportSkip("Not yet supported, see Issue #476", ".", package_name)
            if search_mode.abortIfExecuted():
                break
            continue

        if package_name in ("pycparser", "numpy"):
            reportSkip("Not yet supported, see Issue #477", ".", package_name)
            if search_mode.abortIfExecuted():
                break
            continue

        if package_name in (
            "google-auth",  # bdist_nuitka fails AttributeError: single_version_externally_managed
            "jinja2",  # ModuleNotFoundError: No module named 'jinja2.tests'
            "pandas",  # ModuleNotFoundError: No module named 'Cython'
            "pytz",  # need to 'make build'
            "rsa",  # Now uses Poetry (no setup.py)
        ):
            if search_mode.abortIfExecuted():
                break
            continue

        package_dir = os.path.join(cache_dir, package_name)

        try:
            gitClone(package_name, details["url"], cache_dir)

            os.chdir(base_dir)
            with withVirtualenv(
                "venv_%s" % package_name, delete=False, style="blue"
            ) as venv:
                dist_dir = os.path.join(package_dir, "dist")

                # delete ignored tests if any
                if details["ignored_tests"]:
                    for test in details["ignored_tests"]:
                        venv.runCommand("rm -rf %s" % os.path.join(package_dir, test))

                # setup for pytest
                cmds = [
                    "python -m pip install pytest",
                    "cd %s" % os.path.join(os.path.dirname(nuitka.__file__), ".."),
                    "python setup.py develop",
                    "cd %s" % package_dir,
                ]

                if details["requirements_file"]:
                    cmds.append(
                        "python -m pip install -r %s" % details["requirements_file"]
                    )

                if details.get("extra_commands"):
                    cmds += details["extra_commands"]

                # build uncompiled .whl
                cmds.append("python setup.py bdist_wheel")

                venv.runCommand(commands=cmds)

                # install and print out if the active .whl is compiled or not
                venv.runCommand(
                    commands=[
                        "python -m pip install -U %s"
                        % os.path.join(dist_dir, os.listdir(dist_dir)[0]),
                        # use triple quotes for linux
                        """python -c "print(getattr(__import__('%s'),'__compiled__','__uncompiled_version__'))" """
                        % details.get("package_name", package_name),
                    ]
                )

                # get uncompiled pytest results
                uncompiled_stdout, uncompiled_stderr = venv.runCommandWithOutput(
                    commands=[
                        "cd %s" % package_dir,
                        "python -m pytest --disable-warnings",
                    ],
                    style="blue",
                )

                # clean up before building compiled .whl
                cmds = ["cd %s" % package_dir, "git clean -dfx"]

                if details.get("extra_commands"):
                    cmds += details["extra_commands"]

                # build nuitka compiled .whl
                cmds.append("python setup.py bdist_nuitka")

                venv.runCommand(commands=cmds)

                # install and print out if the active .whl is compiled or not
                venv.runCommand(
                    commands=[
                        "python -m pip install -U %s"
                        % os.path.join(dist_dir, os.listdir(dist_dir)[0]),
                        # use triple quotes for linux
                        """python -c "print(getattr(__import__('%s'),'__compiled__','__uncompiled_version__'))" """
                        % details.get("package_name", package_name),
                    ]
                )

                # get compiled pytest results
                compiled_stdout, compiled_stderr = venv.runCommandWithOutput(
                    commands=[
                        "cd %s" % package_dir,
                        "python -m pytest --disable-warnings",
                    ],
                    style="blue",
                )

                venv.runCommand(commands=["cd %s" % package_dir, "git clean -q -dfx"])

        except Exception as e:
            my_print(
                "Package",
                package_name,
                "ran into an exception during execution, traceback: ",
            )
            my_print(e)
            results.append((package_name, "ERROR", "ERROR"))

            if search_mode.abortIfExecuted():
                break
            continue

        # compare outputs
        stdout_diff = compareOutput(
            "stdout",
            uncompiled_stdout,
            compiled_stdout,
            ignore_warnings=True,
            ignore_infos=True,
            syntax_errors=True,
        )

        stderr_diff = compareOutput(
            "stderr",
            uncompiled_stderr,
            compiled_stderr,
            ignore_warnings=True,
            ignore_infos=True,
            syntax_errors=True,
        )

        results.append((package_name, stdout_diff, stderr_diff))

        exit_code = stdout_diff or stderr_diff

        my_print(
            "\n=================================================================================",
            "\n--- %s ---" % package_name,
            "exit_stdout:",
            stdout_diff,
            "exit_stderr:",
            stderr_diff,
            "\nError, outputs differed for package %s." % package_name
            if exit_code
            else "\nNo differences found for package %s." % package_name,
            "\n=================================================================================\n",
            style="red" if exit_code else "green",
        )

        if exit_code != 0 and search_mode.abortOnFinding(
            dirname=None, filename=package_name
        ):
            break

        if search_mode.abortIfExecuted():
            break

    search_mode.finish()

    # give a summary of all packages
    my_print(
        "\n\n=====================================SUMMARY=====================================",
        style="yellow",
    )

    for package_name, stdout_diff, stderr_diff in results:
        my_print(
            package_name,
            "-",
            end=" ",
            style="red" if (stdout_diff or stderr_diff) else "green",
        )

        my_print(
            "stdout:", stdout_diff, end=" ", style="red" if stdout_diff else "green"
        )

        my_print(
            "stderr:", stderr_diff, end="", style="red" if stderr_diff else "green"
        )

        my_print(
            "\n---------------------------------------------------------------------------------"
        )

    my_print("TOTAL NUMBER OF PACKAGES TESTED: %s" % len(results), style="yellow")

    num_failed = 0
    num_errors = 0

    # tally the number of errors and failed
    for _, y, z in results:
        if type(y) is str:
            # this means the package ran into an exception
            num_errors += 1
        elif y or z:
            num_failed += 1

    my_print(
        "TOTAL PASSED: %s" % (len(results) - num_failed - num_errors), style="green"
    )

    my_print("TOTAL FAILED (differences): %s" % num_failed, style="red")

    my_print("TOTAL ERRORS (exceptions): %s" % num_errors, style="red")


if __name__ == "__main__":
    main()
