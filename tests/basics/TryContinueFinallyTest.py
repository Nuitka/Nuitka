#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function


def tryWhileContinueFinallyTest():
    print("Check if finally is executed in a continue using for loop:")

    x = 0

    while x < 10:
        x += 1

        try:
            if x % 2 == 1:
                continue
        finally:
            print(x, end=" ")

        print("-", end=" ")

    print()


def tryForContinueFinallyTest():
    print("Check if finally is executed in a continue using for loop:")

    for x in range(10):
        try:
            if x % 2 == 1:
                continue
        finally:
            print(x, end=" ")

        print("-", end=" ")

    print()


def tryWhileBreakFinallyTest():
    print("Check if finally is executed in a break using while loop:")

    x = 0

    while x < 10:
        x += 1

        try:
            if x == 5:
                break
        finally:
            print(x, end=" ")

        print("-", end=" ")

    print()


def tryForBreakFinallyTest():
    print("Check if finally is executed in a break using for loop:")

    for x in range(10):
        try:
            if x == 5:
                break
        finally:
            print(x, end=" ")

        print("-", end=" ")

    print()


tryWhileContinueFinallyTest()
tryWhileBreakFinallyTest()

tryForContinueFinallyTest()
tryForBreakFinallyTest()

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
