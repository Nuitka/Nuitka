#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Script related extract build configuration from uv_build backend.

This is executed by Nuitka with the python executable used to compile
to get the configuration from "uv_build" and print it to a JSON
file.
"""

import json
import os
import sys
import glob

def _get_paths_from_patterns(patterns):
    """Return paths from glob patterns"""

    paths = set()

    for pattern in patterns:
        paths.update(glob.glob(pattern, recursive=True))

    return paths

def _get_entry_points(project):
    """Extract entry points from project."""

    arguments = []

    for name, spec in project.get("scripts", {}).items():
        arguments.append("--main-entry-point=%s=%s" % (name, spec))

    return arguments

def _get_packages_and_modules(settings):
    """Extract packages and modules."""
    arguments = []

    include_paths = _get_paths_from_patterns(settings.get("source-include", []))
    exclude_paths = _get_paths_from_patterns(settings.get("source-exclude", []))
    if settings.get("default-excludes", True):
        exclude_paths |= _get_paths_from_patterns(["__pycache__", "*.pyc", "*.pyo"])

    source_paths = list(include_paths - exclude_paths)

    for path in source_paths:
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "__init__.py")):
            arguments.append("--include-package=%s" % path)
        else:
            # It might be a module (file)
            if os.path.exists(path) and path.endswith(".py"):
                arguments.append("--include-module=%s" % path)

    package_dir = {}
    if "module-root" in settings:
        package_dir[""] = settings["module-root"]

    return arguments, package_dir


def _get_data_files(settings):
    """Extract data files."""
    arguments = []

    data_paths = settings.get("data", [])
    # Its type might be dict
    if isinstance(data_paths, dict):
        data_paths = data_paths.keys()

    exclude_paths = _get_paths_from_patterns(settings.get("wheel-exclude", []))
    if settings.get("default-excludes", True):
        exclude_paths |= _get_paths_from_patterns(["__pycache__", "*.pyc", "*.py"])

    data_paths = list(set(data_paths) - exclude_paths)

    for path in data_paths:
        abs_path = os.path.join(os.getcwd(), path)

        if os.path.isfile(path):
            arguments.append("--include-data-file=%s=%s" % (abs_path, path))
        elif os.path.isdir(path):
            arguments.append("--include-data-dir=%s=%s" % (abs_path, path))

    return arguments


def get_uv_build_config():
    try:
        from nuitka.utils.Toml import loadToml

        pyproject_data = loadToml("pyproject.toml")

        project = pyproject_data.get("project", {})
        settings = pyproject_data.get("tool", {}).get("uv", {}).get("build-backend", {})
        if project.get("namespace"):
            raise NotImplementedError("Namespace package is not supported")
    except Exception as e:  # pylint: disable=broad-exception-caught
        sys.exit("Error, failed to load uv_build project: %s" % e)

    entry_point_args = _get_entry_points(project)
    package_args, package_dir = _get_packages_and_modules(settings)
    data_file_args = _get_data_files(settings)

    arguments = entry_point_args + package_args + data_file_args
    for req in project.get("dependencies", []):
        arguments.append("--pyproject-requires=%s" % req)

    arguments.append("--output-folder-name=%s" % project.get("name"))

    result = {
        "package_dir": package_dir,
        "arguments": arguments,
    }
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: %s <output_file>" % sys.argv[0])

    config = get_uv_build_config()
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

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
