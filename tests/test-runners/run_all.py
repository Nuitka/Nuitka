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

import difflib
import shutil
import subprocess
import time

from nuitka.tools.testing.Common import getTempDir, my_print, setup
from nuitka.utils.FileOperations import listDir, removeDirectory


def main():
    python_version = setup()

    os.chdir("subject")

    nuitka_main_path = os.path.join("..", "..", "..", "bin", "nuitka")
    tmp_dir = getTempDir()

    command = [
        os.environ["PYTHON"],
        nuitka_main_path,
        "--plugin-enable=pylint-warnings",
        "--output-dir=%s" % tmp_dir,
        "--follow-imports",
        "--include-package=package",
        "--nofollow-import-to=*.tests",
        "--python-flag=-v",
        "--debug",
        "--module",
        "package",
    ]

    result = subprocess.call(command)

    if result != 0:
        sys.exit(result)

    os.makedirs(os.path.join(tmp_dir, "package.ext"))
    shutil.copytree("package", os.path.join(tmp_dir, "package.ext/package"))

    os.chdir(tmp_dir)

    # We compile the package non-closed, so we can smuggle in tests
    # and user code. This is going to be the example code.
    with open("package.ext/package/user_provided.py", "w") as output:
        # TODO: Maybe assert that the type name of a local function and one from
        # the package are not the same, i.e. we are running inside the compiled
        # package.
        output.write(
            """
from __future__ import print_function

import package
print("__name__:",    package.__name__)
print("__package__:", package.__package__)
print("__path__:",    package.__path__)
print("__file__:",    package.__file__)
# print("__loader__:",    package.__loader__)

import package.sub_package1
print("__name__:",    package.sub_package1.__name__)
print("__package__:", package.sub_package1.__package__)
print("__path__:",    package.sub_package1.__path__)
print("__file__:",    package.sub_package1.__file__)
# print("__loader__:",    package.sub_package1.__loader__)

import package.sub_package1.tests;
print("__name__:",    package.sub_package1.tests.__name__)
print("__package__:", package.sub_package1.tests.__package__)
print("__path__:",    package.sub_package1.tests.__path__)
print("__file__:",    package.sub_package1.tests.__file__)
# print("__loader__:",    package.sub_package1.tests.__loader__)
"""
        )

    os.makedirs("nose")
    with open("nose/usage.txt", "w") as output:
        pass

    os.system("find | sort")

    # Inform about the extra path, format is NUITKA_PACKAGE_fullname where
    # dots become "_" and should point to the directory where external code
    # to be loaded will live under. Probably should be an absolute path, but
    # we avoid it here.
    os.environ["NUITKA_PACKAGE_package"] = "./package.ext/package"

    # Lets make sure these to not work. These will be used in the compiled
    # form only.
    for module_path in ("__init__.py", "sub_package1__init__.py"):
        with open(os.path.join("./package.ext/package", module_path), "w") as output:
            output.write("assert False")

    # Check the compiled package is functional for importing.
    my_print("Running package as basic test:")
    command = [os.environ["PYTHON"], "-c", "import package"]

    result = subprocess.call(command)

    if result != 0:
        sys.exit(result)

    my_print("Running nose tests:")
    # assert os.system(os.environ["PYTHON"] + " -m nose --first-package-wins -s package.sub_package1.tests" ) == 0

    my_print("Running py.test tests:")
    command = [
        os.environ["PYTHON"],
        "-m",
        "pytest",
        "-v",
        "--pyargs",
        "package.sub_package1.tests",
    ]

    result = subprocess.call(command)

    if result != 0:
        sys.exit(result)


if __name__ == "__main__":
    main()
