#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
Tool to extract build configuration from uv_build projects.

This script executes the PEP 517 hook `prepare_metadata_for_build_wheel`
to generate the metadata directory, then parses it to find entry points
and package information. It outputs Nuitka arguments directly.
"""

import csv
import json
import os
import sys
import tempfile
import zipfile

from nuitka.containers.OrderedDicts import OrderedDict

# We expect `uv_build` to be installed in the environment running this script.
try:
    import uv_build
except ImportError:
    sys.exit("Error, 'uv_build' not installed in this environment.")


# uv_build requires 'uv-build' or 'uv' executable to be in PATH.
# On Windows, it's often in Scripts/ but not in PATH during tests or some environments.
# In a venv, python is in Scripts/ folder, so that is the one to add.
candidates = (
    os.path.dirname(sys.executable),
    os.path.join(os.path.dirname(sys.executable), "Scripts"),
)

for script_dir in candidates:
    if os.path.exists(script_dir) and script_dir not in os.environ["PATH"]:
        os.environ["PATH"] = script_dir + os.pathsep + os.environ["PATH"]


def _parseMetaData(metadata_file):
    info = {"Name": "", "Requires-Dist": []}
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Name: "):
                    info["Name"] = line.split(": ", 1)[1].strip()
                elif line.startswith("Requires-Dist: "):
                    info["Requires-Dist"].append(line.split(": ", 1)[1].strip())
    return info


def _parseEntryPoints(entry_points_file):
    scripts = OrderedDict()

    current_section = None
    with open(entry_points_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                continue

            if current_section in ("console_scripts", "gui_scripts"):
                if "=" in line:
                    name, value = line.split("=", 1)
                    scripts[name.strip()] = value.strip()
    return scripts


def _extractFromUvBuild(temp_dir):
    # This is extremely detail rich, pylint: disable=too-many-branches,too-many-locals

    arguments = []

    # Generate metadata by building the wheel
    # We need to build the wheel because prepare_metadata_for_build_wheel
    # does not generate a complete RECORD file with all package files.
    wheel_filename = uv_build.build_wheel(temp_dir)
    wheel_path = os.path.join(temp_dir, wheel_filename)

    dist_info_dir = None

    with zipfile.ZipFile(wheel_path) as zf:
        for name in zf.namelist():
            if name.endswith(".dist-info/RECORD"):
                dist_info_dir = os.path.dirname(name)
                break

        if not dist_info_dir:
            sys.exit("Error, failed to find .dist-info directory in generated wheel.")

        # Extract the .dist-info directory to temp_dir so existing parsing logic works
        for name in zf.namelist():
            if name.startswith(dist_info_dir):
                zf.extract(name, temp_dir)

    metadata_path = os.path.join(temp_dir, dist_info_dir)

    # Parse METADATA for Name and Dependencies
    metadata_file = os.path.join(metadata_path, "METADATA")
    pkg_info = _parseMetaData(metadata_file)

    project_name = pkg_info.get("Name")
    requirements = pkg_info.get("Requires-Dist", [])
    for req in requirements:
        arguments.append("--project-requires=%s" % req)

    # Parse entry points
    entry_points_file = os.path.join(metadata_path, "entry_points.txt")
    if os.path.exists(entry_points_file):
        scripts = _parseEntryPoints(entry_points_file)

        for binary_name, entry_point in scripts.items():
            module_name, function_name = entry_point.split(":", 1)

            arguments.append(
                "--main-entry-point=%s=%s:%s"
                % (binary_name, module_name, function_name)
            )
            arguments.append("--output-filename=%s" % binary_name)
            arguments.append("--output-folder-name=%s" % binary_name)

    # Parse RECORD for packages and data files
    record_file = os.path.join(metadata_path, "RECORD")
    packages = set()
    data_files = []

    if os.path.exists(record_file):

        with open(record_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                path = row[0]

                # Skip the RECORD file itself and .dist-info directory content
                if path == "RECORD" or path.startswith(dist_info_dir):
                    continue

                parts = path.split("/")

                # Check for Python files or extension modules to identify packages
                if path.endswith((".py", ".pyd", ".so")):
                    # The top-level folder or file (module) is what we care about
                    packages.add(parts[0].replace(".py", ""))
                else:
                    data_files.append(path)

    return {
        "arguments": arguments,
        "project_name": project_name,
        "packages": list(packages),
        "data_files": data_files,
    }


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: %s <dump_filename>" % sys.argv[0])

    dump_filename = sys.argv[1]

    with tempfile.TemporaryDirectory() as temp_dir:
        result = _extractFromUvBuild(temp_dir)

        with open(dump_filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)


if __name__ == "__main__":
    main()

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
