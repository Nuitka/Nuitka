#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Some random branching to cover most common cases."""

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
        print("function 'returnFalse' should not have been called")
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


def conditionalExpressionAppend(score):
    hits = []
    misses = []
    for item in (("kept", 3), ("dropped", 7)):
        if item[1] <= 3:
            (hits if score == item[1] else misses).append(item[0])

    if hits:
        print("Conditional expression append result:", hits)
    else:
        print("Conditional expression append result: empty")


conditionalExpressionAppend(3)


def conditionalExpressionDictSet(score):
    hits = {}
    misses = {}
    for item in (("kept", 3), ("dropped", 7)):
        if item[1] <= 3:
            (hits if score == item[1] else misses).setdefault(item[0], item[1])

    if hits:
        print("Conditional expression dict set result:", sorted(hits.items()))
    else:
        print("Conditional expression dict set result: empty")


conditionalExpressionDictSet(3)


def conditionalExpressionDictSubscript(score):
    hits = {}
    misses = {}
    for item in (("kept", 3), ("dropped", 7)):
        if item[1] <= 3:
            (hits if score == item[1] else misses)[item[0]] = item[1]

    if hits:
        print("Conditional expression dict subscript result:", sorted(hits.items()))
    else:
        print("Conditional expression dict subscript result: empty")


conditionalExpressionDictSubscript(3)


def conditionalExpressionDictDel(score):
    hits = {"kept": 3}
    misses = {}
    for item in (("kept", 3),):
        if item[1] <= 3 and score == item[1]:
            del (hits if score == item[1] else misses)[item[0]]

    if "kept" not in hits:
        print("Conditional expression dict del result: removed")
    else:
        print("Conditional expression dict del result: kept")


conditionalExpressionDictDel(3)


def conditionalExpressionSetAdd(score):
    hits = set()
    misses = set()
    for item in (("kept", 3), ("dropped", 7)):
        if item[1] <= 3:
            (hits if score == item[1] else misses).add(item[0])

    if hits:
        print("Conditional expression set add result:", sorted(hits))
    else:
        print("Conditional expression set add result: empty")


conditionalExpressionSetAdd(3)


def conditionalOrExpressionSetAdd(given):
    hits = set()
    for item in ("kept",):
        (given or hits).add(item)

    if hits:
        print("Conditional or expression set add result:", sorted(hits))
    else:
        print("Conditional or expression set add result: empty")


conditionalOrExpressionSetAdd(None)


def conditionalAndExpressionSetAdd(given):
    hits = set()
    for item in ("kept",):
        (given and hits).add(item)

    if hits:
        print("Conditional and expression set add result:", sorted(hits))
    else:
        print("Conditional and expression set add result: empty")


conditionalAndExpressionSetAdd(True)


def addToSet(value, item):
    value.add(item)


def conditionalExpressionSetArgument(score):
    hits = set()
    misses = set()
    for item in (("kept", 3), ("dropped", 7)):
        if item[1] <= 3:
            addToSet(hits if score == item[1] else misses, item[0])

    if hits:
        print("Conditional expression set argument result:", sorted(hits))
    else:
        print("Conditional expression set argument result: empty")


conditionalExpressionSetArgument(3)


def conditionalOrExpressionSetArgument(given):
    hits = set()
    for item in ("kept",):
        addToSet(given or hits, item)

    if hits:
        print("Conditional or expression set argument result:", sorted(hits))
    else:
        print("Conditional or expression set argument result: empty")


conditionalOrExpressionSetArgument(None)


class MutatingDelAttribute(object):
    def __init__(self):
        self.removed = False
        self.item = "value"

    def __delattr__(self, name):
        self.removed = True
        object.__delattr__(self, name)


def conditionalExpressionDelAttribute(given):
    hits = MutatingDelAttribute()
    misses = MutatingDelAttribute()
    for item in ("kept",):
        del (hits if given else misses).item

    print(
        "Conditional expression del attribute result:",
        hits.removed,
        misses.removed,
    )


conditionalExpressionDelAttribute(True)


class MutatingSubscript:
    def __init__(self):
        self.items = []

    def __getitem__(self, key):
        self.items.append(key)
        return key


def conditionalExpressionSubscriptGet(given):
    hits = MutatingSubscript()
    misses = MutatingSubscript()
    for item in ("kept",):
        (hits if given else misses)[item]

    print("Conditional expression subscript get result:", bool(hits.items))


conditionalExpressionSubscriptGet(True)


class MutatingSlice:
    def __init__(self):
        self.items = []

    def __getitem__(self, key):
        self.items.append(key)
        return key


def conditionalExpressionSliceGet(given):
    hits = MutatingSlice()
    misses = MutatingSlice()
    for item in ("kept",):
        (hits if given else misses)[0:1]

    print("Conditional expression slice get result:", bool(hits.items))


conditionalExpressionSliceGet(True)

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
