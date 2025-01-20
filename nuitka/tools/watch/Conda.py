#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Conda backend for maintaining locked package state with nuitka-watch. """

from nuitka.utils.Execution import check_call, executeToolChecked
from nuitka.utils.FileOperations import changeTextFileContents
from nuitka.utils.Utils import isWin32Windows

from .Common import getPlatformRequirements


def _getCaseEnvironmentName(installed_python, case_data):
    return "nuitka-watch-case-%(python_version)s-%(case)s" % {
        "python_version": installed_python.getPythonVersion(),
        "case": case_data["case"],
    }


def getCondaRunCommand(installed_python, case_data):
    return [
        "conda",
        "run",
        "--live-stream",
        "-n",
        _getCaseEnvironmentName(installed_python=installed_python, case_data=case_data),
        "python",
    ]


# spell-checker: ignore opencv
_package_name_table = {
    "dask_ml": "dask-ml",
    "opencv-python-headless": "opencv",
    "opencv-python": "opencv",
}


def _translatePyPIPackageName(package_name):
    for key, value in _package_name_table.items():
        package_name = package_name.replace(key, value)

    return package_name


def updateCondaEnvironmentFile(installed_python, case_data):
    conda_env_filename = "environment.yml"
    conda_package_requirements = ["python=%s" % installed_python.getPythonVersion()]

    if not isWin32Windows():
        conda_package_requirements.append("libpython-static")

    for requirement in getPlatformRequirements(
        installed_python=installed_python, case_data=case_data
    ):
        # Ignore spaces in requirements.
        requirement = requirement.replace(" ", "")

        # TODO: Ought to work on the package name only, but
        # we get away with bad code here for now.
        requirement = _translatePyPIPackageName(requirement)

        conda_package_requirements.append(requirement)

    changeTextFileContents(
        conda_env_filename,
        """\
name: "%(name)s"
dependencies:
%(conda_package_requirements)s
"""
        % {
            "name": _getCaseEnvironmentName(
                installed_python=installed_python, case_data=case_data
            ),
            "conda_package_requirements": "\n".join(
                "  - %s" % conda_package_requirement
                for conda_package_requirement in conda_package_requirements
            ),
        },
    )


def updateCondaEnvironmentLockFile(logger, installed_python, case_data):
    conda_lock_filename = "environment.lock"

    check_call(
        ["conda", "env", "update", "-f", "environment.yml", "--prune"],
        logger=logger,
    )

    conda_output = executeToolChecked(
        logger=logger,
        command=[
            "conda",
            "env",
            "export",
            "-n",
            _getCaseEnvironmentName(
                installed_python=installed_python, case_data=case_data
            ),
        ],
        absence_message="needs conda to query package status on Anaconda Python",
        decoding=str is not bytes,
    )

    changeTextFileContents(filename=conda_lock_filename, contents=conda_output)

    return conda_lock_filename


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
