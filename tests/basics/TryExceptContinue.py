#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

def tryWhileExceptContinueTest():
    print("Check if continue is executed in a except handler using for loop:")

    global undefined

    x = 0

    while x < 10:
        x += 1

        try:
            if x % 2 == 1:
                undefined
        except:
            print(x, end = ' ')
            continue

        print('-', end = ' ')

    print()

def tryForExceptContinueTest():
    print("Check if continue is executed in a except handler using for loop:")

    for x in range(10):
        try:
            if x % 2 == 1:
                undefined
        except:
            print(x, end = ' ')
            continue

        print('-', end = ' ')

    print()

def tryWhileExceptBreakTest():
    print("Check if break is executed in a except handler using while loop:")

    x = 0

    while x < 10:
        x += 1

        try:
            if x == 5:
                undefined
        except:
            print(x, end = ' ')
            break

        print('-', end = ' ')

    print()

def tryForExceptBreakTest():
    print("Check if break is executed in a except handler using for loop:")

    for x in range(10):
        try:
            if x == 5:
                undefined
        except:
            print(x, end = ' ')
            break

        print('-', end = ' ')

    print()

tryWhileExceptContinueTest()
tryWhileExceptBreakTest()

tryForExceptContinueTest()
tryForExceptBreakTest()
