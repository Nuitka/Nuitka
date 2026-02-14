#!/usr/bin/env python
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


import os
import sys


def main():
    print("example_uv: main called")
    exit_code = 0

    # Check data file
    # We expect data.txt to be in the package directory
    import example_uv

    package_dir = os.path.dirname(example_uv.__file__)
    data_path = os.path.join(package_dir, "data.txt")

    if os.path.exists(data_path):
        print("Data file found.")
        with open(data_path, "rb") as f:
            print("Data content:", f.read().strip())
    else:
        print("Data file NOT found at:", data_path)
        exit_code = 1

    # Check example_uv.subpackage data files
    from example_uv import subpackage

    package_dir_2 = os.path.dirname(subpackage.__file__)
    included_path = os.path.join(package_dir_2, "data_included.txt")

    if not os.path.exists(included_path):
        print("Error: data_included.txt missing in example_uv.subpackage")
        exit_code = 1

    print("Data file inclusion verification passed.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
