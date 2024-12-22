#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Pacman backend for maintaining locked package state with nuitka-watch. """

import os

from nuitka.utils.Execution import executeToolChecked
from nuitka.utils.FileOperations import changeTextFileContents

from .Common import getPlatformRequirements


def updatePacmanFile(installed_python, case_data, result_path):
    pacman_filename = os.path.join(result_path, "Pacman.txt")
    pipenv_package_requirements = []

    for requirement in getPlatformRequirements(
        installed_python=installed_python, case_data=case_data
    ):
        # Ignore spaces in requirements.
        requirement = requirement.replace(" ", "")

    changeTextFileContents(
        pacman_filename,
        """\
[python]
%(python_version)s
[packages]
%(pipenv_package_requirements)s
"""
        % {
            "pipenv_package_requirements": "\n".join(pipenv_package_requirements),
            "python_version": installed_python.getPythonVersion(),
        },
    )

    return pacman_filename


def updatePacmanLockFile(logger):
    pacman_lock_filename = "Pacman.lock"

    pacman_output = executeToolChecked(
        logger=logger,
        command=["pacman", "-Q"],
        absence_message="needs pacman to query package status on MSYS2",
        decoding=str is not bytes,
    )

    changeTextFileContents(filename=pacman_lock_filename, contents=pacman_output)

    return pacman_lock_filename


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
