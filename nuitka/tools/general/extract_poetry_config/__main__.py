#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Script related extract build configuration from Poetry projects.

This is executed by Nuitka with the python executable used to compile
to get the configuration from "poetry-core" and print it to a JSON
file.
"""

import json
import os
import sys

try:
    from poetry.core.factory import Factory
except ImportError:
    sys.exit(
        "Error, 'poetry-core' not installed. Please install it to use --project=poetry."
    )


def _get_entry_points(package):
    """Extract entry points from package."""

    arguments = []

    for group, scripts in package.entry_points.items():
        # Normalize group name (poetry uses hyphen, setuptools uses underscore)
        group = group.replace("-", "_")

        # Poetry gives dict name->spec.
        # We should convert to list of strings "name=spec"
        entry_point_list = []
        for name, spec in scripts.items():
            entry_point_list.append("%s=%s" % (name, spec))

        if group == "console_scripts":
            for script_str in entry_point_list:
                arguments.append("--main-entry-point=%s" % script_str)

    return arguments


def _get_packages_and_modules(package):
    """Extract packages and modules."""
    arguments = []
    source_roots = set()

    for pkg in package.packages:
        include = pkg.get("include")
        from_dir = pkg.get("from", ".")

        if from_dir != ".":
            source_roots.add(from_dir)

        full_path = os.path.join(from_dir, include)

        if os.path.isdir(full_path):
            arguments.append("--include-package=%s" % include)
        else:
            # It might be a module (file)
            if os.path.exists(full_path + ".py"):
                arguments.append("--include-module=%s" % include)

    package_dir = {}
    if len(source_roots) == 1:
        package_dir[""] = list(source_roots)[0]

    return arguments, package_dir


def _get_data_files(package):
    """Extract data files."""
    arguments = []

    for inc in package.include:
        path = inc.get("path")
        abs_path = os.path.join(os.getcwd(), path)

        if os.path.isfile(abs_path):
            arguments.append("--include-data-file=%s=%s" % (abs_path, path))
        elif os.path.isdir(abs_path):
            arguments.append("--include-data-dir=%s=%s" % (abs_path, path))

    return arguments


def get_poetry_config():
    try:
        # Avoid using pathlib.Path, execute with string path, which poetry core supports
        p = Factory().create_poetry(os.getcwd())
        package = p.package
    except Exception as e:  # pylint: disable=broad-exception-caught
        sys.exit("Error, failed to load poetry project: %s" % e)

    entry_point_args = _get_entry_points(package)
    package_args, package_dir = _get_packages_and_modules(package)
    data_file_args = _get_data_files(package)

    arguments = entry_point_args + package_args + data_file_args
    for req in package.requires:
        arguments.append("--pyproject-requires=%s" % req)

    arguments.append("--output-folder-name=%s" % package.name)

    result = {
        "package_dir": package_dir,
        "arguments": arguments,
    }

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: %s <output_file>" % sys.argv[0])

    config = get_poetry_config()
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
