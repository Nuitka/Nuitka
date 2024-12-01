#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Release related common functionality.

"""

import os
import shutil

from nuitka.tools.Basics import getHomePath
from nuitka.tools.environments.Virtualenv import withVirtualenv
from nuitka.Tracing import tools_logger
from nuitka.utils.Execution import NuitkaCalledProcessError, check_output
from nuitka.utils.FileOperations import (
    getFileContents,
    getFileFirstLine,
    withDirectoryChange,
)
from nuitka.utils.InstalledPythons import findInstalledPython
from nuitka.Version import getNuitkaVersion, getNuitkaVersionTuple


def checkAtHome(expected="Nuitka Staging"):
    assert os.path.isfile("setup.py")

    if os.path.isdir(".git"):
        git_dir = ".git"
    else:
        line = getFileFirstLine(".git", "r").strip()
        git_dir = line[8:]

    git_description_filename = os.path.join(git_dir, "description")
    description = getFileContents(git_description_filename).strip()

    assert description == expected, (expected, description)


def _getGitCommandOutput(command):
    if type(command) is str:
        command = command.split()

    home_path = getHomePath()

    with withDirectoryChange(home_path):
        output = check_output(command).strip()

    if str is not bytes:
        output = output.decode()

    return output


def getBranchName():
    """Get the git branch name currently running from."""
    # Using a fallback for old git, hopefully not necessary as much anymore.
    try:
        return _getGitCommandOutput("git branch --show-current")
    except NuitkaCalledProcessError:
        return _getGitCommandOutput("git symbolic-ref --short HEAD")


def getBranchRemoteName():
    """Get the git remote name of the branch currently running from."""
    return _getGitCommandOutput("git config branch.%s.remote" % getBranchName())


def getBranchRemoteUrl():
    """Get the git remote url of the branch currently running from."""
    return _getGitCommandOutput("git config remote.%s.url" % getBranchRemoteName())


def getBranchRemoteIdentifier():
    """Get the git remote identifier of the branch currently running from.

    This identifier is used to classify git origins, they might be github,
    private git, or unknown.
    """

    branch_remote_url = getBranchRemoteUrl()

    branch_remote_host = branch_remote_url.split(":", 1)[0].split("@")[-1]

    if branch_remote_host.endswith(".home"):
        branch_remote_host = branch_remote_host.rsplit(".", 1)[0]

    if branch_remote_host == "mastermind":
        return "private"
    elif branch_remote_host.endswith("nuitka.net"):
        return "private"
    elif branch_remote_host == "github":
        return "public"
    else:
        return "unknown"


def checkBranchName():
    branch_name = getBranchName()

    nuitka_version = getNuitkaVersion()

    assert branch_name in (
        "main",
        "develop",
        "factory",
        "release/" + nuitka_version,
        "hotfix/" + nuitka_version,
    ), branch_name

    return branch_name


def getBranchCategory(branch_name):
    """There are 3 categories of releases. Map branch name on them."""

    if (
        branch_name.startswith("release")
        or branch_name == "main"
        or branch_name.startswith("hotfix/")
    ):
        category = "stable"
    elif branch_name == "factory":
        category = "factory"
    elif branch_name == "develop":
        category = "develop"
    else:
        assert False

    return category


def makeNuitkaSourceDistribution(formats=None, sign=True):
    # spell-checker: ignore bztar,gztar
    if formats is None:
        formats = ("bztar", "gztar", "zip")

    checkAtHome()

    python = findInstalledPython(
        python_versions=("3.10", "3.11", "3.12"),
        module_name="setuptools",
        module_version=None,
    )

    # Avoid strange permissions in archive
    os.system("umask 0022 && chmod -R a+rX .")

    filenames = []

    with withVirtualenv(
        "venv_nuitka",
        logger=tools_logger,
        style="blue",
        delete=False,
        python=python.getPythonExe(),
    ) as venv:
        # TODO: Should use a newer one, and predict more compliant filename, and
        # release 75.3.0 ought to work fine.
        venv.runCommand("python -m pip install -U 'setuptools<68'")
        venv.runCommand(
            "python setup.py sdist --formats=%s" % ",".join(formats), keep_cwd=True
        )

    # Cleanup the build directory, not needed.
    shutil.rmtree("build", ignore_errors=True)

    nuitka_version = getNuitkaVersionTuple()

    if nuitka_version[3] is False:
        filename = "dist/Nuitka-%d.%drc%d.tar.gz" % (
            nuitka_version[0],
            nuitka_version[1],
            nuitka_version[-1],
        )
    else:
        filename = "dist/Nuitka-%d.%d.%d.tar.gz" % nuitka_version[:3]

    assert os.path.exists(filename), filename

    # Delete requires.txt as it confuses poetry and potentially other tools
    assert os.system("gunzip -9 %s" % filename) == 0
    os.system(
        "tar --wildcards --delete --file %s Nuitka-*/Nuitka.egg-info/requires.txt"
        % filename[:-3]
    )

    assert os.system("gzip -9 %s" % filename[:-3]) == 0
    assert os.path.exists(filename), filename

    assert os.system("chmod 644 %s" % filename) == 0

    filenames.append(filename)

    if nuitka_version[3] is False:
        filename = "dist/Nuitka-%d.%drc%d.tar.bz2" % (
            nuitka_version[0],
            nuitka_version[1],
            nuitka_version[-1],
        )
    else:
        filename = "dist/Nuitka-%d.%d.%d.tar.bz2" % nuitka_version[:3]

    if os.path.exists(filename):
        # Delete requires.txt as it confuses poetry and potentially other tools,
        # spell-checker: ignore bunzip2
        assert os.system("bunzip2 %s" % filename) == 0
        os.system(
            "tar --wildcards --delete --file %s Nuitka-*/Nuitka.egg-info/requires.txt"
            % filename[:-4]
        )
        assert os.system("bzip2 -9 %s" % filename[:-4]) == 0
        assert os.path.exists(filename), filename

        filenames.append(filename)

    if nuitka_version[3] is False:
        filename = "dist/Nuitka-%d.%drc%d.zip" % (
            nuitka_version[0],
            nuitka_version[1],
            nuitka_version[-1],
        )
    else:
        filename = "dist/Nuitka-%d.%d.%d.zip" % nuitka_version[:3]

    if os.path.exists(filename):
        # Delete requires.txt as it confuses poetry and potentially other tools
        os.system("zip -d %s Nuitka-*/Nuitka.egg-info/requires.txt" % filename)
        assert os.path.exists(filename), filename

        filenames.append(filename)

    for filename in filenames:
        assert os.system("chmod 644 %s" % filename) == 0

        if sign:
            assert (
                os.system("gpg --local-user 2912B99C --detach-sign %s" % filename) == 0
            )

    tools_logger.info("Created source distribution as '%s'." % filenames[0])
    return filenames


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
