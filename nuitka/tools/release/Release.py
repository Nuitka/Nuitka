#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Release related common functionality.

"""

import os
import subprocess

from nuitka.Version import getNuitkaVersion


def checkAtHome():
    assert os.path.isfile("setup.py")

    if os.path.isdir(".git"):
        git_dir = ".git"
    else:
        git_dir = open(".git")

        with open(".git") as f:
            line = f.readline().strip()

            assert line.startswith("gitdir:")

            git_dir = line[ 8:]

    git_description_filename = os.path.join(git_dir, "description")

    assert open(git_description_filename).read().strip() == "Nuitka Staging"


def checkBranchName():
    branch_name = subprocess.check_output(
        "git symbolic-ref --short HEAD".split()
    ).strip()

    if str is not bytes:
        branch_name = branch_name.decode()

    nuitka_version = getNuitkaVersion()

    assert branch_name in (
        "master",
        "develop",
        "factory",
        "release/" + nuitka_version,
        "hotfix/" + nuitka_version
    ), branch_name

    return branch_name

def getBranchCategory(branch_name):
    """ There are 3 categories of releases. Map branch name on them.

    """

    if branch_name.startswith("release") or \
       branch_name == "master" or \
       branch_name.startswith("hotfix/"):
        category = "stable"
    elif branch_name == "factory":
        category = "factory"
    elif branch_name == "develop":
        category = "develop"
    else:
        assert False

    return category


def checkNuitkaChangelog():
    first_line = open("Changelog.rst").readline()

    if "(Draft)" in first_line:
        return "draft"
    else:
        return "final"
