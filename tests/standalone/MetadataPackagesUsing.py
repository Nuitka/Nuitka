#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" This test uses the meta data of metadata entry points lookups that wouldn't work at runtime.

But since Nuitka resolves them at compile time, no issue should happen.
"""

# nuitka-project: --standalone

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from importlib.metadata import entry_points
except ImportError:
    pass
else:
    print("Type of importlib.metadata.entry_points", type(entry_points()))
    try:
        print(
            "Type of importlib.metadata.entry_points subscript",
            type(entry_points()["console_scripts"]),
        )
        print("There are %d entry points" % len(entry_points()["console_scripts"]))
        print(
            "Example entry point",
            sorted(entry_points()["console_scripts"], key=lambda e: e.name)[0],
        )
    except KeyError:
        pass

try:
    from importlib_metadata import entry_points
except ImportError:
    pass
else:
    print("Type of importlib_metadata.entry_points", type(entry_points()))
    try:
        print(
            "Type of importlib_metadata.entry_points subscript",
            type(entry_points()["console_scripts"]),
        )
        print("There are %d entry points" % len(entry_points()["console_scripts"]))
        print(
            "Example entry point",
            sorted(entry_points()["console_scripts"], key=lambda e: e.name)[0],
        )
    except KeyError:
        pass
    try:
        print(
            "Example group from importlib_metadata.entry_points element",
            sorted(entry_points().groups)[0],
        )
    except (IndexError, AttributeError):
        pass
