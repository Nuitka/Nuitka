#!/usr/bin/python -u
#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

""" Make PyPI upload of Nuitka, and check success of it. """

from __future__ import print_function

import os
import shutil
import sys

from nuitka.tools.release.Documentation import createReleaseDocumentation
from nuitka.tools.release.Release import checkBranchName
from nuitka.tools.testing.Virtualenv import withVirtualenv
from nuitka.Tracing import my_print
from nuitka.Version import getNuitkaVersion


def main():
    nuitka_version = getNuitkaVersion()

    branch_name = checkBranchName()

    # Only real master releases so far.
    assert branch_name == "master", branch_name
    assert "pre" not in nuitka_version and "rc" not in nuitka_version

    my_print("Working on Nuitka %r." % nuitka_version)

    shutil.rmtree("check_nuitka", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)

    my_print("Creating documentation.")
    createReleaseDocumentation()
    my_print("Creating source distribution.")
    assert os.system("umask 0022 && chmod -R a+rX . && python setup.py sdist") == 0

    my_print("Creating a virtualenv for quick test:")
    with withVirtualenv("check_nuitka") as venv:
        my_print("Installing Nuitka into virtualenv:", style="blue")
        my_print("*" * 40, style="blue")
        venv.runCommand("python -m pip install ../dist/Nuitka*.tar.gz")
        my_print("*" * 40, style="blue")

        print("Compiling basic test:")
        my_print("*" * 40, style="blue")
        venv.runCommand("nuitka-run ../tests/basics/Asserts.py")
        my_print("*" * 40, style="blue")

    assert os.system("twine check dist/*") == 0

    if "--check" not in sys.argv:
        my_print("Uploading source dist")
        assert os.system("twine upload dist/*") == 0
        my_print("Uploaded.")
    else:
        my_print("Checked OK, but not uploaded.")
