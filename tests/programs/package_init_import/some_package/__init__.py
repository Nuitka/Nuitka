#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import sys

print(
    "This is some_package",
    __name__,
    "in",
    "__package__: ",
    (
        __package__
        if __package__ is not None or sys.version_info[:2] != (3, 2)
        else ".".join(__name__.split(".")[:-1])
    ),
)

try:
    import PackageLocal
except ImportError:
    print("This must be Python3, doing local import then.")
    from . import PackageLocal

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
