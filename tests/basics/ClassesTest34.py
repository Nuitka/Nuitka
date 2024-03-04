#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Covers Python3 meta classes with __prepare__ non-dict values. """

# nuitka-project: --nofollow-imports

from enum import Enum

print("Enum class with duplicate enumeration values:")
try:

    class Color(Enum):
        red = 1
        green = 2
        blue = 3
        red = 4

        print("not allowed to get here")

except Exception as e:
    print("Occurred", e)

print("Class variable that conflicts with closure variable:")


def testClassNamespaceOverridesClosure():
    # See #17853.
    x = 42

    class X:
        locals()["x"] = 43
        y = x

    print("should be 43:", X.y)


testClassNamespaceOverridesClosure()

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
