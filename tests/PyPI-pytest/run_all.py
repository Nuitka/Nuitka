#!/usr/bin/env python
#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

from nuitka.tools.testing.OutputComparison import compareOutput
from nuitka.tools.testing.Virtualenv import withVirtualenv
from nuitka.utils.FileOperations import removeDirectory
from nuitka.tools.testing.Common import createSearchMode, my_print
from nuitka.utils.AppDirs import getCacheDir
import nuitka



# TODO: Get closer to 50 items :)

packages = {
    "attrs": {
        "url": "https://github.com/python-attrs/attrs.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "chardet": {
        "url": "https://github.com/chardet/chardet.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "colorama": {
        "url": "https://github.com/tartley/colorama.git",
        "requirements_file": "requirements-dev.txt",
        "ignored_tests": None,
    },

    "cryptography": {
        "url": "https://github.com/pyca/cryptography.git",
        "requirements_file": "dev-requirements.txt",
        "ignored_tests": None,
    },

    "dateutil": {
        "url": "https://github.com/dateutil/dateutil.git",
        "requirements_file": "requirements-dev.txt",
        "ignored_tests": None,
    },

    "idna": {
        "url": "https://github.com/kjd/idna.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "jinja2": {
        "url": "https://github.com/pallets/jinja.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "jmespath": {
        "url": "https://github.com/jmespath/jmespath.py.git",
        "requirements_file": "requirements.txt",
        "ignored_tests": None,
    },

    "markupsafe": {
        "url": "https://github.com/pallets/markupsafe.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "numpy": {
        "url": "https://github.com/numpy/numpy.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "pyasn1": {
        "url": "https://github.com/etingof/pyasn1.git",
        "requirements_file": "requirements.txt",
        "ignored_tests": None,
    },

    "pycparser": {
        "url": "https://github.com/eliben/pycparser.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "pytz": {
        "url": "https://github.com/stub42/pytz.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "pyyaml": {
        "url": "https://github.com/yaml/pyyaml.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "requests": {
        "url": "https://github.com/kennethreitz/requests.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "rsa": {
        "url": "https://github.com/sybrenstuvel/python-rsa.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "simplejson": {
        "url": "https://github.com/simplejson/simplejson.git",
        "requirements_file": None,
        "ignored_tests": None,
    },

    "urllib3": {
        "url": "https://github.com/urllib3/urllib3.git",
        "requirements_file": "dev-requirements.txt",
        "ignored_tests": (
            "test/test_no_ssl.py",
        )
    },
}



def main():
    cache_dir = os.path.join(getCacheDir(), "pypi-git-clones")

    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)

    os.chdir(cache_dir)

    search_mode = createSearchMode()

    results = []

    for package_name, details in sorted(packages.items()):
        active = search_mode.consider(dirname=None, filename=package_name)

        if not active:
            continue

        # skip these packages
        if package_name in (
            "attrs", # __import__ check fails for uncompiled whl
            "cryptography", # setup.py develop fails
            "jinja2", # bdist_wheel fails
            "numpy",
            "pycparser", # __import__ check fails for compiled whl; pytest passes
            "pytz",
            "pyyaml", # invalid command 'bdist_nuitka'
        ):
            if search_mode.abortIfExecuted():
                break
            continue

        package_dir = os.path.join(cache_dir, package_name)

        # update package if existing, else clone
        try:
            assert os.system("cd %s && git fetch && git reset --hard origin" % package_name) == 0
        except AssertionError:
            assert os.system("git clone %s %s --depth 1 --single-branch --no-tags" % (details["url"], package_name)) == 0, \
                "Error while git cloning package %s, aborting..." % package_name


        try:
            with withVirtualenv("venv_%s" % package_name) as venv:
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
                    cmds += [
                        "python -m pip install -r %s" % details["requirements_file"],
                    ]

                # build uncompiled .whl
                cmds += [
                    "python setup.py bdist_wheel",
                ]

                venv.runCommand(
                    commands=cmds
                )

                # install and print out if the active .whl is compiled or not
                venv.runCommand(
                    commands=[
                        "python -m pip install -U %s" % os.path.join(dist_dir, os.listdir(dist_dir)[0]),
                        "python -c print(getattr(__import__('%s'),'__compiled__','__uncompiled_version__'))" % package_name,
                    ]
                )

                # get uncompiled pytest results
                uncompiled_stdout, uncompiled_stderr = venv.runCommandWithOutput(
                    commands=[
                        "cd %s" % package_dir,
                        "python -m pytest --disable-warnings",
                    ]
                )

                # build nuitka compiled .whl
                venv.runCommand(
                    commands=[
                        "cd %s" % package_dir,
                        "rm -rf dist",
                        "python setup.py bdist_nuitka",
                    ]
                )

                # install and print out if the active .whl is compiled or not
                venv.runCommand(
                    commands=[
                        "python -m pip install -U %s" % os.path.join(dist_dir, os.listdir(dist_dir)[0]),
                        "python -c print(getattr(__import__('%s'),'__compiled__','__uncompiled_version__'))" % package_name,
                    ]
                )

                # get compiled pytest results
                compiled_stdout, compiled_stderr = venv.runCommandWithOutput(
                    commands=[
                        "cd %s" % package_dir,
                        "python -m pytest --disable-warnings",
                    ]
                )

                venv.runCommand("rm -rf %s" % dist_dir)


        except Exception as e:
            my_print("Package", package_name, "ran into an exception during execution, traceback: ")
            my_print(e)
            removeDirectory(venv.getVirtualenvDir(), ignore_errors=False)

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


        results.append((package_name,stdout_diff,stderr_diff))

        exit_code = stdout_diff or stderr_diff


        my_print(
            "\n=================================================================================",
            "\n--- %s ---" % package_name,
            "exit_stdout:",
            stdout_diff,
            "exit_stderr:",
            stderr_diff,
            "\nError, outputs differed for package %s." % package_name if exit_code \
                else "\nNo differences found for package %s." % package_name,
            "\n=================================================================================\n",
            style="red" if exit_code else "green"
        )


        if exit_code != 0 and search_mode.abortOnFinding(dirname=None, filename=package_name):
            break

        if search_mode.abortIfExecuted():
            break

    search_mode.finish()


    # give a summary of all packages

    my_print(
        "\n\n=====================================SUMMARY=====================================",
        style="yellow"
    )

    for package_name, stdout_diff, stderr_diff in results:
        my_print(
            package_name,
            "-",
            end=" ",
            style="red" if (stdout_diff or stderr_diff) else "green"
        )

        my_print(
            "stdout:",
            stdout_diff,
            end=" ",
            style="red" if stdout_diff else "green"
        )

        my_print(
            "stderr:",
            stderr_diff,
            end="",
            style="red" if stderr_diff else "green"
        )

        my_print("\n---------------------------------------------------------------------------------")


    my_print(
        "TOTAL NUMBER OF PACKAGES TESTED: %s" % len(results),
        style="yellow"
    )

    num_failed = sum(y or z for _,y,z in results)

    my_print(
        "TOTAL PASSED: %s" % (len(results) - num_failed),
        style="green"
    )

    my_print(
        "TOTAL FAILED: %s" % num_failed,
        style="red"
    )


if __name__ == "__main__":
    main()
