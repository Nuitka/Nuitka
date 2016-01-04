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

def closureTest1():
    # Assign, but the value is not supposed to be used by the function, instead the later
    # update is effective.
    d = 1

    def subby():
        return d

    d = 22222*2222

    return subby()


def closureTest2():
    # Using a closure variable that is not initialized at the time it is closured should
    # work as well.

    def subby():
        return d

    d = 2222*2222

    return subby()

def closureTest3():
    def subby():
        return undefined_global  # @UndefinedVariable

    try:
        return subby()
    except NameError:
        return 88

d = 1

def scopeTest4():
    try:
        return d

        d = 1
    except UnboundLocalError as e:
        return repr(e)


print("Test closure where value is overwritten:", closureTest1())
print("Test closure where value is assigned only late:", closureTest2())

print("Test function where closured value is never assigned:", closureTest3())

print("Scope test where UnboundLocalError is expected:", scopeTest4())


def function():
    pass

class ClosureLocalizerClass:
    print("Function before assigned in a class:", function)

    function = 1

    print("Function after it was assigned in class:", function)

ClosureLocalizerClass()

def ClosureLocalizerFunction():
    try:
        function = function

        print("Function didn't give unbound local error")
    except UnboundLocalError as e:
        print("Function gave unbound local error when accessing function before assignment:", repr(e))

ClosureLocalizerFunction()

class X:
    def __init__(self, x):
        self.x = x

def changingClosure():
    print("Changing a closure taken value after it was taken.")

    a = 1

    def closureTaker():
        return X(a)

    x = closureTaker()
    a=2
    print("Closure value first time:", x.x)
    x = closureTaker()
    print("Closure value second time:", x.x)

changingClosure()
