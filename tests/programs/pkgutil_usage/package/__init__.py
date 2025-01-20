#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" This package loads a file via pkgutil.get_data and outputs its contents in import.

"""

from __future__ import print_function

import pkgutil

print("This is", __name__, "in", __package__, "speaking:")

# Setting version from a file, is an example use case of this, but not limited
# to that of course.
__version__ = pkgutil.get_data(__package__, "DATA_FILE.txt").decode("ascii").strip()

print("pkgutil.get_data()", __version__)

try:
    import pkg_resources
except ImportError:
    pass
else:
    data = pkg_resources.resource_string(__package__, "DATA_FILE2.txt")
    print("pkg_resources.resource_string", data)

    readable = pkg_resources.resource_stream(__package__, "DATA_FILE3.txt")
    data = readable.read()
    print("pkg_resources.resource_readable.read()", data)

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
