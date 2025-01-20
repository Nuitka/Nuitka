#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Assignment tests, cover most forms of them. """

# nuitka-project: --nofollow-imports

from __future__ import print_function

import sys

# Tests are dirty on purpose.
#
# pylint: disable=broad-except,global-variable-undefined,redeclared-assigned-name
# pylint: disable=global-variable-not-assigned,invalid-name,self-assigning-variable


def someFunction():
    a = 2
    print("Simple assignment to variable:", a)

    b = c = 3
    print("Assignment to 2 variables", b, c)

    z = [1, 2, 3]
    z[2] = z[1] = 5

    print("Assignment to list subscripts:", z)

    d, e = 1, 2
    print("Assignment to variable tuple:", d, e)

    [f, g] = 7, 9
    print("Assignment to variable list:", f, g)

    j = [h, i] = (7, 9)
    print("Complex Assignment from variable list:", j, type(j), h, i)

    a, (b, c) = 1, (2, 3)
    print("Assignment to nested tuples:", a, b, c)

    v = [1, 2, 3, 4]
    v[2:3] = (8, 9)
    print("Assignment to list slice", v)


def varargsFunction(*args):
    f1, f2, f3, f4 = args

    print("Assignment from list", f1, f2, f3, f4)


def otherFunction():
    class Iterable:
        def __iter__(self):
            return iter(range(3))

    a, b, c = Iterable()

    print("Assignments from iterable", a, b, c)

    print("Assignments from too small iterable", end=" ")

    try:
        f, g = (1,)
    except Exception as e:
        print("gave", type(e), repr(e))

        try:
            print(f)
        except UnboundLocalError:
            print("Variable f is untouched")

        try:
            print(g)
        except UnboundLocalError:
            print("Variable g is untouched")

    print("Assignments from too large iterable", end=" ")

    try:
        d, j = 1, 2, 3
    except Exception as e:
        print("gave", type(e), repr(e))

        try:
            print(d)
        except UnboundLocalError:
            print("Variable d is untouched")

        try:
            print(j)
        except UnboundLocalError:
            print("Variable j is untouched")

    class BasicIterClass:
        def __init__(self, n):
            self.n = n
            self.i = 0

        def __next__(self):
            res = self.i
            if res >= self.n:
                raise StopIteration
            self.i = res + 1
            return res

        if sys.version_info[0] < 3:

            def next(self):
                return self.__next__()

    class IteratingSequenceClass:
        def __init__(self, n):
            self.n = n

        def __iter__(self):
            return BasicIterClass(self.n)

    print("Exception from iterating over too short class:", end=" ")
    try:
        a, b, c = IteratingSequenceClass(2)
    except ValueError:
        print("gave", sys.exc_info())


def anotherFunction():
    d = {}

    print("Assignment to dictionary with comma subscript:", end="")
    # d["f"] = 3

    d["a", "b"] = 6
    d["c", "b"] = 9

    print(sorted(d.items()))


def swapVariables():
    print("Strange swap form:")
    a = 1
    b = 2

    a, b, a = b, a, b

    print(a, b)


def InterruptedUnpack():
    a = 1
    b = 2

    print("Assignment from a too short tuple to multiple targets:", end=" ")

    try:
        s = (a,)

        c, d = s
    except ValueError as e:
        print("gives ValueError", repr(e))

        try:
            print(c)
        except UnboundLocalError as e:
            print("and then nothing is assigned:", repr(e))
    else:
        del d

    del a, b

    z = []

    try:
        a, z.unknown, b = 1, 2, 3
    except AttributeError:
        print("Interrupted unpack, leaves value assigned", a)


def multiTargetInterrupt():
    a = 1
    b = 2

    print("Multiple, overlapping targets", end="")

    d = c, d = a, b
    print(d, c, end="")

    del c
    del d

    c, d = d = a, b
    print(d, c)

    print("Error during multiple assignments", end="")

    del c
    del d
    e = 9

    z = []
    try:
        c, d = e, z.a = a, b
    except AttributeError:
        print("having attribute error", c, d, e)

    del c
    del d
    e = 9

    print("Error during multiple assignments", end="")

    try:
        c, d = z.a, e = a, b
    except AttributeError:
        print("having attribute error", c, d, e)


def optimizeableTargets():
    a = [1, 2]

    a[int(1)] = 3

    print("Optimizable slice operation, results in", a)


def complexDel():
    a = b = c = d = 1

    del a, b, (c, d)

    try:
        print(c)
    except UnboundLocalError as e:
        print("yes, del worked", repr(e))


def sliceDel():
    # Python3 ranges are not lists.
    a = list(range(6))

    del a[2:4]

    print("Del slice operation, results in", a)


def globalErrors():
    global unassigned_1, unassigned_2

    try:
        unassigned_1 = unassigned_1
    except NameError as e:
        print("Accessing unassigned global gives", repr(e))

    try:
        del unassigned_2
    except NameError as e:
        print("Del on unassigned global gives", repr(e))


someFunction()
varargsFunction(1, 2, 3, 4)
otherFunction()
anotherFunction()
swapVariables()
InterruptedUnpack()
multiTargetInterrupt()
optimizeableTargets()
complexDel()
sliceDel()
globalErrors()

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
