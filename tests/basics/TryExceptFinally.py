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
"Some doc"

from __future__ import print_function


def one():
    return 1


def tryScope1(x):
    try:
        try:
            x += one()
        finally:
            print("Finally is executed")

            try:
                _z = one()
            finally:
                print("Deep Nested finally is executed")
    except:
        print("Exception occurred")
    else:
        print("No exception occurred")


tryScope1(1)
print("*" * 20)
tryScope1([1])


def tryScope2(x, someExceptionClass):
    try:
        x += 1
    except someExceptionClass as e:
        print("Exception class from argument occurred:", someExceptionClass, repr(e))
    else:
        print("No exception occurred")


def tryScope3(x):
    if x:
        try:
            x += 1
        except TypeError:
            print("TypeError occurred")
    else:
        print("Not taken")


print("*" * 20)

tryScope2(1, TypeError)
tryScope2([1], TypeError)

print("*" * 20)

tryScope3(1)
tryScope3([1])
tryScope3([])

print("*" * 20)


def tryScope4(x):
    try:
        x += 1
    except:
        print("exception occurred")
    else:
        print("no exception occurred")
    finally:
        print("finally obeyed")


tryScope4(1)
tryScope4([1])


def tryScope5():
    import sys

    print("Exception info is initially", sys.exc_info())
    try:
        try:
            undefined_global += 1
        finally:
            print("Exception info in 'finally' clause is", sys.exc_info())
    except:
        pass


tryScope5()
