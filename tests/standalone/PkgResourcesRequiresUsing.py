#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" This test uses the meta data of metadata lookups that wouldn't work at runtime.

But since Nuitka resolves them at compile time, no issue should happen, unless
the module used in the example is not installed.
"""

# nuitka-project: --standalone

import sys

# nuitka-skip-unless-imports: lxml

try:
    from pkg_resources import get_distribution, require
except ImportError:
    print("No pkg_resources found")
else:
    x = require("lxml")
    print(x[0].version)
    print(x[0].parsed_version)
    __version__ = get_distribution("lxml").version
    print("pkg_resources gives version", __version__)
    __version__ = get_distribution("lxml").parsed_version
    print("pkg_resources gives parsed version", __version__)


try:
    from importlib.metadata import version
except ImportError:
    print("Old Python", sys.version_info)
else:
    __version__ = version("lxml")
    print("Stdlib importlib.metadata gives version", __version__)


try:
    from importlib_metadata import version
except ImportError:
    print("Backport importlib_metadata is not installed.")
else:
    __version__ = version("lxml")
    print("Backport importlib_metadata gives version", __version__)

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
