#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
This module handles the extraction of build configuration from UV Build projects.
"""

import os
import sys

from nuitka.importing.Importing import addMainScriptDirectory
from nuitka.utils.Execution import executeProcess
from nuitka.utils.FileOperations import withTemporaryDirectory
from nuitka.utils.Json import loadJsonFromFilename

from .BuildPackageCommon import (
    reportBuildError,
    setProjectExpectedDataFiles,
    setProjectName,
)


def _maybeVirtualEnv(path):
    """
    Check if a directory might be a virtualenv.
    """
    # Windows
    if os.path.exists(os.path.join(path, "Scripts", "python.exe")):
        return True

    # Unix
    if os.path.exists(os.path.join(path, "bin", "python")):
        return True

    return False


def getUvBuildConfiguration(logger, pyproject_data):
    """
    Get the build configuration from a UV Build project.
    """
    with withTemporaryDirectory("nuitka-project-dump") as temp_dir:
        dump_filename = os.path.join(temp_dir, "build_config.json")

        # Locate the script "tools/general/extract_uv_config/__main__.py" relative to this module.
        # We assume this module is in "nuitka/options/UvBuild.py"
        script_filename = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tools",
            "general",
            "extract_uv_config",
        )

        command = (
            sys.executable,
            script_filename,
            dump_filename,
        )

        stdout, stderr, exit_code = executeProcess(
            command,
            stdin=False,
        )

        if exit_code != 0:
            reportBuildError(logger, "uv_build", command, stdout, stderr)

        if not os.path.exists(dump_filename):
            logger.sysexit(
                "Error, 'uv_build' configuration extraction produced no output file."
            )

        config = loadJsonFromFilename(dump_filename)

        # UV projects typically use 'src' layout or root layout.
        # We auto-detect 'src' and add it to python path.
        if os.path.exists("src"):
            addMainScriptDirectory(os.path.abspath("src"))

        arguments = config.get("arguments", [])

        # Parse tool.uv configuration for data files
        uv_config = pyproject_data.get("tool", {}).get("uv", {})

        if uv_config:
            for unhandled_key in uv_config:
                logger.warning(
                    """\
Unhandled UV config key '%s' in [tool.uv] of the 'pyproject.toml', we might \
have to ignore list or handle it: %s"""
                    % unhandled_key
                )

        detected_packages = config.get("packages", [])

        # Add --include-package-data for detected packages
        # Only if not already specified by other means (though duplicate args are usually fine/merged)
        for package_name in detected_packages:
            arguments.append("--include-package-data=%s" % package_name)
            arguments.append("--include-package=%s" % package_name)

        setProjectName(config.get("project_name"))
        setProjectExpectedDataFiles(config.get("data_files", []))

        # TODO: Check against IncludedDataFiles set once that is considered complete

        return arguments


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
