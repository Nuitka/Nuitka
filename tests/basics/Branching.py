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
""" Some random branching to cover most common cases. """

from __future__ import print_function


def branchingFunction(a, b, c):
    print("branchingFunction:", a, b, c)

    print("a or b", a or b)
    print("a and b", a and b)
    print("not a", not a)
    print("not b", not b)

    print("Simple branch with both branches")
    if a:
        l = "YES"
    else:
        l = "NO"

    print(a, "->", l)

    print("Simple not branch with both branches")
    if not a:
        l = "YES"
    else:
        l = "NO"

    print(not a, "->", l)

    print("Simple branch with a nested branch in else path:")
    if a:
        m = "yes"
    else:
        if True:
            m = "no"

    print(a, "->", m)

    print("Triple 'and' chain:")

    v = "NO"
    if a and b and c:
        v = "YES"

    print(a, b, c, "->", v)

    print("Triple or chain:")

    k = "NO"
    if a or b or c:
        k = "YES"

    print(a, b, c, "->", k)

    print("Nested 'if not' chain:")
    p = "NO"
    if not a:
        if not b:
            p = "YES"

    print("not a, not b", not a, not b, "->", p)

    print("or condition in braces:")
    q = "NO"
    if a or b:
        q = "YES"
    print("(a or b) ->", q)

    print("Braced if not with two 'or'")

    if not (a or b or c):
        q = "YES"
    else:
        q = "NO"
    print("not (a or b or c)", q)

    print("Braced if not with one 'or'")
    q = "NO"
    if not (b or b):
        q = "YES"
    print("not (b or b)", q)

    print("Expression a or b", a or b)
    print("Expression not(a or b)", not (a or b))
    print("Expression a and (b+5)", a and (b + 5))

    print("Expression (b if b else 2)", (b if b else 2))
    print("Expression (a and (b if b else 2))", (a and (b if b else 2)))

    print("Braced if not chain with 'and' and conditional expression:")

    if not (a and (b if b else 2)):
        print("oki")

    print("Nested if chain with outer else:")

    d = 1

    if a:
        if b or c:
            if d:
                print("inside nest")

    else:
        print("outer else")

    print("Complex conditional expression:")
    v = (3 if a + 1 else 0) or (b or (c * 2 if c else 6) if b - 1 else a and b and c)
    print(v)

    if True:
        print("Predictable branch taken")


branchingFunction(1, 0, 3)

x = 3


def optimizationVictim():

    if x:
        pass
    else:
        pass

    if x:
        pass
        pass


optimizationVictim()


def dontOptimizeSideEffects():
    print(
        "Lets see, if conditional expression in known true values are correctly handled:"
    )

    def returnTrue():
        print("function 'returnTrue' was called as expected")

        return True

    def returnFalse():
        print("function 'returnFalse' should not have beeen called")
        return False

    if (returnTrue() or returnFalse(),):
        print("Taken branch as expected.")
    else:
        print("Bad branch taken.")


dontOptimizeSideEffects()


def dontOptimizeTruthCheck():
    class A:
        def __nonzero__(self):
            raise ValueError

        __bool__ = __nonzero__

    a = A()

    if a:
        pass


try:
    print("Check that branch conditions are not optimized way: ", end="")
    dontOptimizeTruthCheck()
    print("FAIL.")
except ValueError:
    print("OK.")
