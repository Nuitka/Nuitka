#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Utilities for parsing TOML files."""

from nuitka.PythonVersions import python_version

from .FileOperations import getFileContents


def getTomlLoads():
    """Get the toml loads function to use.

    Returns:
        callable: The toml loads function.
    """
    if python_version >= 0x3B0:
        # stdlib only for 3.11+, pylint: disable=I0021,import-error
        from tomllib import loads as toml_loads
    else:
        try:
            from tomli import loads as toml_loads
        except ImportError:
            try:
                from toml import loads as toml_loads
            except ImportError:
                return None

    return toml_loads


def loadToml(filename):
    """Load a TOML file.

    Args:
        filename (str): The filename to load.

    Returns:
        dict: The loaded TOML data.
    """
    toml_loads = getTomlLoads()

    if toml_loads is None:
        return None

    return toml_loads(getFileContents(filename))


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
