#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
This module handles the extraction of build configuration from 'build' backend projects.
"""

import os
import sys

from nuitka.importing.Importing import addMainScriptDirectory
from nuitka.PythonVersions import getSitePackageCandidateNames
from nuitka.utils.Execution import (
    executeProcess,
    withEnvironmentVarsOverridden,
)
from nuitka.utils.FileOperations import (
    makePath,
    putTextFileContents,
    withDirectoryChange,
    withTemporaryDirectory,
)
from nuitka.utils.Json import loadJsonFromFilename


def getBuildBackendConfiguration(logger):
    """
    Get the build configuration from a project using the 'build' backend.
    """
    # This is "build" handling.
    with withTemporaryDirectory("nuitka-project-dump") as temp_dir:

        mock_site_packages_path = os.path.join(temp_dir, "site_packages")
        makePath(mock_site_packages_path)

        nuitka_path = os.path.dirname(os.path.dirname(sys.modules["nuitka"].__file__))

        # spell-checker: ignore sitecustomize,cmdclass
        putTextFileContents(
            filename=os.path.join(mock_site_packages_path, "sitecustomize.py"),
            contents="""
import sys
import os

# Ensure nuitka is importable
nuitka_path = %(nuitka_path)r
if nuitka_path not in sys.path:
    sys.path.insert(0, nuitka_path)

import setuptools
import distutils.core
import setuptools.command.egg_info
from nuitka.distutils.DistutilsCommands import build as nuitka_build

# Patch setuptools
_old_setuptools_setup = setuptools.setup
def new_setuptools_setup(**attrs):
    attrs['cmdclass'] = attrs.get('cmdclass', {})
    attrs['cmdclass']['build'] = nuitka_build
    return _old_setuptools_setup(**attrs)
setuptools.setup = new_setuptools_setup

# Patch distutils
_old_distutils_setup = distutils.core.setup
def new_distutils_setup(**attrs):
    attrs['cmdclass'] = attrs.get('cmdclass', {})
    attrs['cmdclass']['build'] = nuitka_build
    return _old_distutils_setup(**attrs)
distutils.core.setup = new_distutils_setup

# Force egg_base to temp_dir
_old_egg_info_initialize_options = setuptools.command.egg_info.egg_info.initialize_options
def new_egg_info_initialize_options(self):
    _old_egg_info_initialize_options(self)
    self.egg_base = %(egg_base)r
setuptools.command.egg_info.egg_info.initialize_options = new_egg_info_initialize_options
"""
            % {
                "nuitka_path": nuitka_path,
                "egg_base": temp_dir,
            },
        )

        dump_filename = os.path.join(temp_dir, "build_config.json")

        # We use the temporary directory for the project to avoid implicit imports
        # of the current directory, which may contain a "build" folder that clashes.
        project_dir = os.getcwd()

        with withEnvironmentVarsOverridden(
            {
                "NUITKA_DUMP_BUILD_CONFIG": dump_filename,
                "NUITKA_PROJECT_DIR": project_dir,
                "PYTHONPATH": os.pathsep.join(
                    [mock_site_packages_path]
                    + [
                        candidate
                        for candidate in sys.path
                        if os.path.dirname(candidate) in getSitePackageCandidateNames()
                    ]
                ),
            }
        ):
            with withDirectoryChange(temp_dir):
                _stdout, _stderr, exit_code = executeProcess(
                    [
                        sys.executable,
                        "-m",
                        "build",
                        "--no-isolation",
                        "--skip-dependency-check",
                        project_dir,
                    ],
                    stdin=False,
                )

        # The build is expected to fail with exit code 1 because we exit(0)
        # without producing a wheel, causing build frontend to complain. But if
        # we have the dump file, we are good.
        if exit_code == 0 or not os.path.exists(dump_filename):
            assert False, _stdout
            return logger.sysexit(
                "Error, failed to extract build configuration via 'python -m build'."
            )

        config = loadJsonFromFilename(dump_filename)

        package_dir = config.get("package_dir")
        if package_dir and "" in package_dir:
            addMainScriptDirectory(os.path.join(os.getcwd(), package_dir.get("")))
        else:
            addMainScriptDirectory(os.getcwd())

    return config.get("arguments", [])


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
