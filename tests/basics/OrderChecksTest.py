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


def separator():
    print("*" * 80)


def dictOrderCheck():
    def key1():
        print("key1 called")

        return 1

    def key2():
        print("key2 called")

        return 2

    def value1():
        print("value1 called")

        return 11

    def value2():
        print("value2 called")

        return 22

    print("Checking order of calls in dictionary creation from callables:")

    print({key1(): value1(), key2(): value2()})

    try:
        (1 / 0)[1.0j / 0] = 1.0 / 0
    except ZeroDivisionError as e:
        print("Expected exception caught:", repr(e))
    try:
        (1 / 0)[1.0 / 0] = 1
    except ZeroDivisionError as e:
        print("Expected exception caught:", repr(e))
    try:
        (1 / 0)[1] = 1.0 / 0
    except ZeroDivisionError as e:
        print("Expected exception caught:", repr(e))


def listOrderCheck():
    def value1():
        print("value1 called")

        return 11

    def value2():
        print("value2 called")

        return 22

    print([value1(), value2()])


def sliceOrderCheck():
    print("Slices:")
    d = list(range(10))

    def lvalue():
        print("lvalue", end=" ")

        return d

    def rvalue():
        print("rvalue", end=" ")

        return range(2)

    def rvalue4():
        print("rvalue", end=" ")

        return range(4)

    def low():
        print("low", end=" ")

        return 0

    def high():
        print("high", end=" ")

        return 4

    def step():
        print("step", end=" ")

        return 2

    print("Complex slice lookup:", end=" ")
    print(lvalue()[low() : high() : step()])

    print("Complex slice assignment:", end=" ")
    lvalue()[low() : high() : step()] = rvalue()
    print(d)

    print("Complex slice del:", end=" ")
    del lvalue()[low() : high() : step()]
    print(d)

    print("Complex inplace slice operation", end=" ")
    # TODO: This gives an error in CPython, but not in Nuitka.
    # lvalue()[ low() : high() : step() ] += rvalue()
    print(d)

    d = list(range(10))

    print("Simple slice lookup", end=" ")
    print(lvalue()[low() : high()])

    print("Simple slice assignment", end=" ")
    lvalue()[3 + low() : 3 + high()] = rvalue()
    print(d)

    print("Simple slice del", end=" ")
    del lvalue()[3 + low() : 3 + high()]
    print(d)

    print("Simple inplace slice operation", end=" ")
    lvalue()[low() : high()] += rvalue4()
    print(d)


def subscriptOrderCheck():
    print("Subscripts:")
    d = {}

    def lvalue():
        print("lvalue", end=" ")

        return d

    def rvalue():
        print("rvalue", end=" ")

        return 2

    def subscript():
        print("subscript", end=" ")

        return 1

    print("Assigning subscript:")
    lvalue()[subscript()] = rvalue()
    print(d)

    print("Lookup subscript:")
    print(lvalue()[subscript()])

    print("Deleting subscript:")
    del lvalue()[subscript()]
    print(d)


def attributeOrderCheck():
    def lvalue():
        print("lvalue", end=" ")

        return lvalue

    def rvalue():
        print("rvalue", end=" ")

        return 2

    print("Attribute assignment order:")

    lvalue().xxx = rvalue()
    print("Assigned was indeed:", lvalue.xxx)

    print("Checking attribute assignment to unassigned value from unassigned:")
    try:
        undefined_global_zzz.xxx = undefined_global_yyy
    except Exception as e:
        print("Expected exception caught:", repr(e))
    else:
        assert False

    try:
        (1 / 0).x = 1.0 / 0
    except ZeroDivisionError as e:
        print("Expected exception caught:", repr(e))


def compareOrderCheck():
    def lvalue():
        print("lvalue", end=" ")

        return 1

    def rvalue():
        print("rvalue", end=" ")

        return 2

    print("Comparisons:")
    print("==", lvalue() == rvalue())
    print("<=", lvalue() <= rvalue())
    print(">=", lvalue() >= rvalue())
    print("!=", lvalue() != rvalue())
    print(">", lvalue() > rvalue())
    print("<", lvalue() < rvalue())

    print("Comparison used in bool context:")
    print("==", "yes" if lvalue() == rvalue() else "no")
    print("<=", "yes" if lvalue() <= rvalue() else "no")
    print(">=", "yes" if lvalue() >= rvalue() else "no")
    print("!=", "yes" if lvalue() != rvalue() else "no")
    print(">", "yes" if lvalue() > rvalue() else "no")
    print("<", "yes" if lvalue() < rvalue() else "no")


def operatorOrderCheck():
    def left():
        print("left operand", end=" ")

        return 1

    def middle():
        print("middle operand", end=" ")

        return 3

    def right():
        print("right operand", end=" ")

        return 2

    print("Operations:")
    print("+", left() + middle() + right())
    print("-", left() - middle() - right())
    print("*", left() * middle() * right())
    print("/", left() / middle() / right())
    print("%", left() % middle() % right())
    print("**", left() ** middle() ** right())


def generatorOrderCheck():
    print("Generators:")

    def default1():
        print("default1", end=" ")

        return 1

    def default2():
        print("default2", end=" ")

        return 2

    def default3():
        print("default3", end=" ")

        return 3

    def value(x):
        print("value", x, end=" ")
        return x

    def generator(a=default1(), b=default2(), c=default3()):
        print("generator entry")
        yield value(a)
        yield value(b)
        yield value(c)
        print("generator exit")

    result = list(generator())
    print("Result", result)


def classOrderCheck():
    print("Checking order of class constructions:")

    class B1:
        pass

    class B2:
        pass

    def base1():
        print("base1", end=" ")

        return B1

    def base2():
        print("base2", end=" ")

        return B2

    def deco1(cls):
        print("deco1", end=" ")

        return cls

    def deco2(cls):
        print("deco2")

        return B2

    @deco2
    @deco1
    class X(base1(), base2()):
        print("class body", end=" ")

    print


def inOrderCheck():
    print("Checking order of in operator:")

    def container():
        print("container", end=" ")

        return [3]

    def searched():
        print("searched", end=" ")

        return 3

    print("in:", searched() in container())
    print("not in:", searched() not in container())


def unpackOrderCheck():
    class TraceRelease:
        def __init__(self, value):
            self.value = value

        def __del__(self):
            print("Deleting iteration value", self.value)
            pass

    print("Unpacking values:")

    class Iterable:
        def __init__(self):
            self.consumed = 2

        def __iter__(self):
            return Iterable()

        def __del__(self):
            print("Deleted iterable with", self.consumed)

        def next(self):
            print("Next with state", self.consumed)

            if self.consumed:
                self.consumed -= 1
            else:
                raise StopIteration

            return TraceRelease(self.consumed)

        __next__ = next

    iterable = Iterable()

    class RejectAttributeOwnership:
        def __setattr__(self, key, value):
            print("Setting", key, value.value)

    try:
        RejectAttributeOwnership().x, RejectAttributeOwnership().y = a, b = iterable
    except Exception as e:
        print("Caught", repr(e))

    return a, b


def superOrderCheck():
    print("Built-in super:")
    try:
        super(zzz, xxx)
    except Exception as e:
        print("Expected exception caught super 2", repr(e))


def isinstanceOrderCheck():
    print("Built-in isinstance:")
    try:
        isinstance(zzz, xxx)
    except Exception as e:
        print("Expected exception caught isinstance 2", repr(e))


def rangeOrderCheck():
    print("Built-in range:")
    try:
        range(zzz, yyy, xxx)
    except Exception as e:
        print("Expected exception caught range 3", repr(e))

    try:
        range(zzz, xxx)
    except Exception as e:
        print("Expected exception caught range 2", repr(e))


def importOrderCheck():
    print("Built-in __import__:")

    def name():
        print("name", end=" ")

    def globals():
        print("globals", end=" ")

    def locals():
        print("locals", end=" ")

    def fromlist():
        print("fromlist", end=" ")

    def level():
        print("level")

    try:
        __import__(name(), globals(), locals(), fromlist(), level())
    except Exception as e:
        print("Expected exception caught __import__ 5", repr(e))


def hasattrOrderCheck():
    print("Built-in hasattr:")
    try:
        hasattr(zzz, yyy)
    except Exception as e:
        print("Expected exception caught hasattr", repr(e))


def getattrOrderCheck():
    print("Built-in getattr:")
    try:
        getattr(zzz, yyy)
    except Exception as e:
        print("Expected exception caught getattr 2", repr(e))

    try:
        getattr(zzz, yyy, xxx)
    except Exception as e:
        print("Expected exception caught getattr 3", repr(e))

    def default():
        print("default used")

    print("Default side effects:", end=" ")
    print(getattr(1, "real", default()))


def typeOrderCheck():
    print("Built-in type:")
    try:
        type(zzz, yyy, xxx)
    except Exception as e:
        print("Expected exception caught type 3", repr(e))


def iterOrderCheck():
    print("Built-in iter:")
    try:
        iter(zzz, xxx)
    except Exception as e:
        print("Expected exception caught iter 2", repr(e))


def openOrderCheck():
    print("Built-in open:")
    try:
        open(zzz, yyy, xxx)
    except Exception as e:
        print("Expected exception caught open 3", repr(e))


def unicodeOrderCheck():
    print("Built-in unicode:")
    try:
        unicode(zzz, yyy, xxx)
    except Exception as e:
        print("Expected exception caught unicode", repr(e))


def longOrderCheck():
    print("Built-in long:")
    try:
        long(zzz, xxx)
    except Exception as e:
        print("Expected exception caught long 2", repr(e))


def intOrderCheck():
    print("Built-in int:")
    try:
        int(zzz, xxx)
    except Exception as e:
        print("Expected exception caught int", repr(e))


def nextOrderCheck():
    print("Built-in next:")
    try:
        next(zzz, xxx)
    except Exception as e:
        print("Expected exception caught next 2", repr(e))


def callOrderCheck():
    print("Checking nested call arguments:")

    class A:
        def __del__(self):
            print("Doing del inner object")

    def check(obj):
        print("Outer function")

    def p(obj):
        print("Inner function")

    check(p(A()))


def boolOrderCheck():
    print("Checking order of or/and arguments:")

    class A(int):
        def __init__(self, value):
            self.value = value

        def __del__(self):
            print("Doing del of %s" % self)

        def __bool__(self):
            print("Test of %s" % self)
            return self.value != 0

        __nonzero__ = __bool__

        def __str__(self):
            return "<%s %r>" % (self.__class__.__name__, self.value)

    class B(A):
        pass

    class C(A):
        pass

    print("Two arguments, A or B:")
    for a in range(2):
        for b in range(2):
            print("Case %d or %d" % (a, b))
            r = A(a) or B(b)
            print(r)
            del r

    # TODO: The order of deletion does not exactly match, which we accept for
    # now.
    if True:
        print("Three arguments, A or B or C:")
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    print("Case %d or %d or %d" % (a, b, c))
                    r = A(a) or B(b) or C(c)
                    print(r)
                    del r

    print("Two arguments, A and B:")
    for a in range(2):
        for b in range(2):
            print("Case %d and %d" % (a, b))
            r = A(a) and B(b)
            print(r)
            del r

    # See above
    if True:
        print("Three arguments, A and B and C:")
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    print("Case %d and %d and %d" % (a, b, c))
                    r = A(a) and B(b) and C(c)
                    print(r)
                    del r


def comparisonChainOrderCheck():
    print("Checking order of comparison chains:")

    class A(int):
        def __init__(self, value):
            self.value = value

        def __del__(self):
            print("Doing del of %s" % self)

        def __le__(self, other):
            print("Test of %s <= %s" % (self, other))
            return self.value <= other.value

        def __str__(self):
            return "<%s %r>" % (self.__class__.__name__, self.value)

    class B(A):
        pass

    class C(A):
        pass

    # See above, not really doing it right.
    if False:
        print("Three arguments, A <= B <= C:")
        for a in range(3):
            for b in range(3):
                for c in range(3):
                    print("Case %d <= %d <= %d" % (a, b, c))
                    r = A(a) <= B(b) <= C(c)
                    print(r)
                    del r


dictOrderCheck()
separator()
listOrderCheck()
separator()
subscriptOrderCheck()
separator()
attributeOrderCheck()
separator()
operatorOrderCheck()
separator()
compareOrderCheck()
separator()
sliceOrderCheck()
separator()
generatorOrderCheck()
separator()
classOrderCheck()
separator()
inOrderCheck()
separator()
unpackOrderCheck()
separator()
superOrderCheck()
separator()
isinstanceOrderCheck()
separator()
rangeOrderCheck()
separator()
importOrderCheck()
separator()
hasattrOrderCheck()
separator()
getattrOrderCheck()
separator()
typeOrderCheck()
separator()
iterOrderCheck()
separator()
openOrderCheck()
separator()
unicodeOrderCheck()
separator()
nextOrderCheck()
separator()
longOrderCheck()
separator()
intOrderCheck()
separator()
callOrderCheck()
separator()
boolOrderCheck()
separator()
comparisonChainOrderCheck()
