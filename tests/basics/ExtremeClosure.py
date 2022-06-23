#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" These tests contain all forms of closure absuse.

"""
from __future__ import print_function

a = 1
b = 1


def someFunction():
    a = a  # pylint: disable=redefined-outer-name,unused-variable


class SomeClass:
    b = b


SomeClass()

try:
    someFunction()
except UnboundLocalError as e:
    print("Expected unbound local error occurred:", repr(e))

try:

    class AnotherClass:
        b = undefined_global


except NameError as e:
    print("Expected name error occurred:", repr(e))

try:

    class YetAnotherClass:
        b = 1
        del b
        print(b)


except NameError as e:
    print("Expected name error occurred:", repr(e))
