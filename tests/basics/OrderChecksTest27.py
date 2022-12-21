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
from __future__ import print_function


def setOrderCheck():
    print("Checking order of set literals:")

    def one():
        print("one")
        return "one"

    def two():
        print("two")
        return "two"

    return {one(), two()}


def raiseOrderCheck():
    print("Checking order of raises:")

    def exception_type():
        print("exception_type", end="")

        return ValueError

    def exception_value():
        print("exception_value", end="")

        return 1

    def exception_tb():
        print("exception_value", end="")

        return None

    print("3 args", end="")
    try:
        raise exception_type(), exception_value(), exception_tb()
    except Exception as e:
        print("caught", repr(e))

    print("2 args", end="")
    try:
        raise exception_type(), exception_value()
    except Exception as e:
        print("caught", repr(e))

    print("1 args", end="")
    try:
        raise exception_type()
    except Exception as e:
        print("caught", repr(e))


setOrderCheck()
raiseOrderCheck()
