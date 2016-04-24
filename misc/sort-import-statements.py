#!/usr/bin/env python
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

""" Sort import statements using isort for Nuitka code and helpers.

    Skips tests and inline copies of code.
"""

import os
import subprocess

home_dir = os.path.abspath(__file__)
home_dir = os.path.dirname(home_dir)
home_dir = os.path.dirname(home_dir)

os.chdir(home_dir)

target_files = []

for root, dirnames, filenames in os.walk(home_dir):
    if "inline_copy" in dirnames:
        dirnames.remove("inline_copy")
    if "tests" in dirnames:
        dirnames.remove("tests")

    if root == home_dir:
        continue

    for filename in filenames:
        full_path = os.path.join(root, filename)

        if filename.endswith(".py"):
            target_files.append(full_path)

target_files.append("bin/nuitka")
target_files.append("nuitka/build/SingleExe.scons")
target_files.append("setup.py")

subprocess.check_call(
    [
        "isort", "-ot", "-m3", "-ns", "__init__.py"
    ] + target_files
)
