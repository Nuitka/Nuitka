#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
This module handles the extraction of build configuration from Poetry projects.
"""

import os
import sys

from nuitka.importing.Importing import addMainScriptDirectory
from nuitka.utils.Execution import executeProcess
from nuitka.utils.FileOperations import withTemporaryDirectory
from nuitka.utils.Json import loadJsonFromFilename


def getPoetryBuildConfiguration(logger):
    """
    Get the build configuration from a Poetry project.
    """
    # This is "poetry" handling.
    with withTemporaryDirectory("nuitka-project-dump") as temp_dir:
        dump_filename = os.path.join(temp_dir, "build_config.json")

        # Locate the script "misc/extract-poetry-config.py" relative to this module.
        # We assume this module is in "nuitka/options/Poetry.py"
        script_filename = os.path.join(
            os.path.dirname(__file__),
            "..",
            "tools",
            "general",
            "extract_poetry_config",
        )

        _stdout, _stderr, exit_code = executeProcess(
            [
                sys.executable,
                script_filename,
                dump_filename,
            ],
            stdin=False,
        )

        if exit_code != 0:
            assert False, (_stdout, _stderr)
            return logger.sysexit(
                "Error, failed to extract build configuration via 'poetry'."
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
