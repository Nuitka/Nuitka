#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Pipenv backend for maintaining locked package state with nuitka-watch. """

from nuitka.utils.FileOperations import changeTextFileContents

from .Common import getPlatformRequirements


def updatePipenvFile(installed_python, case_data, dry_run):
    pipenv_filename = "Pipfile"
    pipenv_package_requirements = []

    for requirement in getPlatformRequirements(
        installed_python=installed_python, case_data=case_data
    ):
        # Ignore spaces in requirements.
        requirement = requirement.replace(" ", "")

        if all(char not in requirement for char in "=><"):
            pipenv_package_requirements.append('"%s" = "*"' % requirement)
        else:
            operator_index = min(
                requirement.find(char) for char in "=><" if char in requirement
            )

            pipenv_package_requirements.append(
                '"%s" = "%s"'
                % (requirement[:operator_index], requirement[operator_index:])
            )

    # TODO: Other indexes, e.g. nvidia might be needed too
    changed_pipenv_file = changeTextFileContents(
        pipenv_filename,
        """\
[[source]]
name = "pypi"
url = "https://pypi.org/simple"
verify_ssl = true

[requires]
python_version = "%(python_version)s"

[packages]
%(pipenv_package_requirements)s
"""
        % {
            "pipenv_package_requirements": "\n".join(pipenv_package_requirements),
            "python_version": installed_python.getPythonVersion(),
        },
        compare_only=dry_run,
    )

    return changed_pipenv_file, pipenv_filename


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
