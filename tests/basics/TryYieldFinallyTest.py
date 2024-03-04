#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


def tryContinueFinallyTest():
    for x in range(10):
        try:
            if x % 2 == 1:
                continue
        finally:
            yield x

        yield "-"


def tryBreakFinallyTest():
    for x in range(10):
        try:
            if x == 5:
                break
        finally:
            yield x

        yield "-"


def tryFinallyAfterYield():
    try:
        yield 3
    finally:
        print("Executing finally")


def tryReturnFinallyYield():
    try:
        return
    finally:
        yield 1


def tryReturnExceptYield():
    try:
        return
    except StopIteration:
        print("Caught StopIteration")
        yield 2
    except:
        yield 1
    else:
        print("No exception")


def tryStopIterationExceptYield():
    try:
        raise StopIteration
    except StopIteration:
        print("Caught StopIteration")
        yield 2
    except:
        yield 1
    else:
        print("No exception")


print("Check if finally is executed in a continue using for loop:")
print(tuple(tryContinueFinallyTest()))

print("Check if finally is executed in a break using for loop:")
print(tuple(tryBreakFinallyTest()))

print("Check what try yield finally something does:")
print(tuple(tryFinallyAfterYield()))

print("Check if yield is executed in finally after return:")
print(tuple(tryReturnFinallyYield()))

print("Check if yield is executed in except after return:")
print(tuple(tryReturnExceptYield()))

print("Check if yield is executed in except after StopIteration:")
print(tuple(tryReturnExceptYield()))

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
