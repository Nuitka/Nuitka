#!/usr/bin/python -u
#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Make PyPI upload of Nuitka, and check success of it. """

import os
import shutil
import sys
from optparse import OptionParser

from nuitka.tools.environments.Virtualenv import withVirtualenv
from nuitka.tools.release.Documentation import checkReleaseDocumentation
from nuitka.tools.release.Release import checkBranchName
from nuitka.Tracing import tools_logger
from nuitka.utils.InstalledPythons import findInstalledPython
from nuitka.Version import getNuitkaVersion


def _checkNuitkaInVirtualenv(python):
    with withVirtualenv(
        "venv_nuitka", logger=tools_logger, style="blue", python=python.getPythonExe()
    ) as venv:
        tools_logger.info("Installing Nuitka into virtualenv:", style="blue")
        tools_logger.info("*" * 40, style="blue")
        venv.runCommand("python -m pip install ../dist/Nuitka*.tar.gz")
        tools_logger.info("*" * 40, style="blue")

        tools_logger.info("Compiling basic test with runner:", style="blue")
        tools_logger.info("*" * 40, style="blue")
        venv.runCommand(
            "nuitka%s ../tests/basics/AssertsTest.py" % python.getPythonVersion()[0],
            style="blue",
        )
        tools_logger.info("*" * 40, style="blue")

        tools_logger.info(
            "Compiling basic test with recommended -m mode:", style="blue"
        )
        tools_logger.info("*" * 40, style="blue")
        venv.runCommand(
            "python -m nuitka ../tests/basics/AssertsTest.py",
            style="blue",
        )
        tools_logger.info("*" * 40, style="blue")


def main():
    nuitka_version = getNuitkaVersion()

    branch_name = checkBranchName()

    parser = OptionParser()

    parser.add_option(
        "--token",
        action="store",
        dest="token",
        help="""
Token to use for upload.
""",
    )

    parser.add_option(
        "--check",
        action="store_true",
        dest="check",
        help="""
Do not update the the container, use it if updating was done recently.
""",
    )

    options, positional_args = parser.parse_args()

    if positional_args:
        tools_logger.sysexit(
            "This command takes no positional arguments, check help output."
        )

    # Only real main releases so far.
    if not options.check:
        assert branch_name == "main", branch_name
        assert "pre" not in nuitka_version and "rc" not in nuitka_version

    tools_logger.info("Working on Nuitka %r." % nuitka_version, style="blue")

    shutil.rmtree("check_nuitka", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)

    tools_logger.info("Creating documentation.", style="blue")
    checkReleaseDocumentation()
    tools_logger.info("Creating source distribution.", style="blue")
    assert (
        os.system("umask 0022 && chmod -R a+rX . && %s setup.py sdist" % sys.executable)
        == 0
    )

    # Delete requires.txt as it confuses poetry and potentially other tools
    assert os.system("gunzip dist/Nuitka*.tar.gz") == 0
    assert (
        os.system(
            "tar --wildcards --delete --file dist/Nuitka*.tar Nuitka-*/Nuitka.egg-info/requires.txt"
        )
        == 0
    )
    assert os.system("gzip -9 dist/Nuitka*.tar") == 0

    # Test with these Pythons if the installed package would work.
    pythons = [
        findInstalledPython(
            python_versions=("2.7",), module_name=None, module_version=None
        ),
        findInstalledPython(
            python_versions=("3.10",), module_name=None, module_version=None
        ),
    ]

    for python in pythons:
        _checkNuitkaInVirtualenv(python)

    assert os.system("twine check dist/*") == 0

    if not options.check:
        tools_logger.info("Uploading source dist")
        assert (
            os.system(
                "twine upload --username=__token__ --password=%s dist/* "
                % options.token
            )
            == 0
        )
        tools_logger.info("Uploaded.")
    else:
        tools_logger.info("Checked OK, but not uploaded.")


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
