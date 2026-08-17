#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests that reads a data file via path"""

# nuitka-project: --include-package=some_package

from importlib.resources import contents, is_resource, path

try:
    from importlib.resources import files
except ImportError:
    files = None

# Test contents (returns iterable of resource names)
print("CONTENTS", sorted(contents("some_package")))

# Test is_resource
assert is_resource("some_package", "DATA_FILE.txt") is True
assert is_resource("some_package", "missing.txt") is False

# Test path
with path("some_package", "DATA_FILE.txt") as data_path:
    with open(data_path, encoding="utf8") as data_file:
        print("RES", data_file.read())

if files is not None:
    # Test files with argument
    print("importlib.resources.files('some_package'):", files("some_package"))

    # Test files() with no argument
    try:
        print("importlib.resources.files():", files())
    except Exception as e:
        print("importlib.resources.files() with no arguments gave exception", type(e))

    # Test files with non-existent package
    try:
        print(
            "importlib.resources.files('some_package.non_existent'):",
            files("some_package.non_existent"),
        )
    except Exception as e:
        print(
            "importlib.resources.files('some_package.non_existent') with non-existent package gave exception",
            type(e),
        )

print("OK.")

#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
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
