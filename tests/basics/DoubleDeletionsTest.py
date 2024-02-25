#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

# nuitka-project: --nofollow-imports

a = 3

del a

try:
    del a
except NameError as e:
    print("Raised expected exception:", repr(e))


def someFunction(b, c):
    b = 1

    del b

    try:
        del b
    except UnboundLocalError as e:
        print("Raised expected exception:", repr(e))


someFunction(3, 4)

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
