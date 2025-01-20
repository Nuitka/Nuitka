#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


import sys

print("This must be Python3 which no longer needs __init__.py to accept a package.")


print("The parent path is", sys.modules["some_package.sub_package"].__path__)


def s():
    pass


print(s)

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
