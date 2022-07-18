#!/usr/bin/python -u
#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

    check_mode = "--check" in sys.argv

    # Only real main releases so far.
    if not check_mode:
        assert branch_name == "main", branch_name
        assert "pre" not in nuitka_version and "rc" not in nuitka_version

    my_print("Working on Nuitka %r." % nuitka_version, style="blue")

    shutil.rmtree("check_nuitka", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)

    my_print("Creating documentation.", style="blue")
    createReleaseDocumentation()
    my_print("Creating source distribution.", style="blue")
    assert os.system("umask 0022 && chmod -R a+rX . && python setup.py sdist") == 0

    with withVirtualenv("venv_nuitka", style="blue") as venv:
        my_print("Installing Nuitka into virtualenv:", style="blue")
        my_print("*" * 40, style="blue")
        venv.runCommand("python -m pip install ../dist/Nuitka*.tar.gz")
        my_print("*" * 40, style="blue")

        my_print("Compiling basic test with runner:", style="blue")
        my_print("*" * 40, style="blue")
        venv.runCommand(
            "nuitka%d-run ../tests/basics/Asserts.py" % sys.version_info[0],
            style="blue",
        )
        my_print("*" * 40, style="blue")

        my_print("Compiling basic test with recommended -m mode:", style="blue")
        my_print("*" * 40, style="blue")
        venv.runCommand(
            "python -m nuitka ../tests/basics/Asserts.py",
            style="blue",
        )
        my_print("*" * 40, style="blue")

    assert os.system("twine check dist/*") == 0

    if not check_mode:
        my_print("Uploading source dist")
        assert os.system("twine upload dist/*") == 0
        my_print("Uploaded.")
    else:
        my_print("Checked OK, but not uploaded.")
