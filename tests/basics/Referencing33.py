#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
import sys, os, types

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            ".."
        )
    )
)
from nuitka.tools.testing.Common import (
    executeReferenceChecked,
    someGenerator,
    someGeneratorRaising,
    checkDebugPython
)

checkDebugPython()


def simpleFunction1():
    def g():
        for a in range(20):
            yield a

    def h():
        yield 4
        yield 5
        yield 6

    def f():
        yield from g()
        yield from h()

    x = list( f() )


def simpleFunction2():
    def g():
        for a in range(20):
            yield a

    def h():
        yield 4
        yield 5
        yield 6

        raise TypeError

    def f():
        yield from g()
        yield from h()

    try:
        x = list( f() )
    except TypeError:
        pass

# Broken iterator class.
class Broken:
    def __iter__(self):
        return self
    def __next__(self):
        return 1
    def __getattr__(self, attr):

        1/0

def simpleFunction3():
    def g():
        yield from Broken()

    try:
        gi = g()
        next(gi)
    except Exception:
        pass

def simpleFunction4():
    def g():
        yield from Broken()

    try:
        gi = g()
        next(gi)
        gi.throw(AttributeError)
    except Exception:
        pass


def simpleFunction5():
    def g():
        yield from (2,3)

    return list( g() )


def simpleFunction6():
    def g():
        yield from (2,3)

        return 9

    return list( g() )

def simpleFunction7():
    def g():
        yield from (2,3)

        return 9, 8

    return list( g() )


def simpleFunction8():
    def g():
        x = someGenerator()
        assert type(x) is types.GeneratorType

        yield from x

    gen = g()
    next(gen)

    try:
        gen.throw(ValueError)
    except ValueError:
        pass


def simpleFunction9():
    def g():
        x = someGeneratorRaising()
        assert type(x) is types.GeneratorType

        yield from x

    gen = g()
    next(gen)

    try:
        next(gen)
    except TypeError:
        pass


class ClassIteratorBrokenClose:
    def __init__(self):
        self.my_iter = iter(range(2))

    def __iter__(self):
        return self

    def next(self):
        return next(self.my_iter)

    def close(self):
        raise TypeError(3)

    __next__ = next

def simpleFunction10():
    def g():
        x = ClassIteratorBrokenClose()

        yield from x

    gen = g()
    next(gen)

    try:
        gen.throw(GeneratorExit)
    except GeneratorExit:
        pass
    except TypeError:
        pass

class ClassIteratorBrokenThrow:
    def __init__(self):
        self.my_iter = iter(range(2))

    def __iter__(self):
        return self

    def next(self):
        return next(self.my_iter)

    def throw(self, *args):
        raise TypeError(3)

    __next__ = next


def simpleFunction11():
    def g():
        x = ClassIteratorBrokenThrow()

        yield from x

    gen = g()
    next(gen)

    try:
        gen.throw(ValueError)
    except GeneratorExit:
        pass
    except TypeError:
        pass


class ClassIteratorRejectingThrow:
    def __init__(self):
        self.my_iter = iter(range(2))

    def __iter__(self):
        return self

    def next(self):
        return next(self.my_iter)

    def throw(self, *args):
        # Some Python3.4 versions do normalize exceptions.
        assert len(args) == 1 or sys.version_info < (3,5)

    __next__ = next


# Lets have an exception that must not be instantiated.
class MyError(Exception):
    def __init__(self):
        assert False

def simpleFunction12():
    def g():
        x = ClassIteratorRejectingThrow()

        yield from x

    gen = g()
    next(gen)

    gen.throw(MyError)


# These need stderr to be wrapped.
tests_stderr = (3, 4)

# Disabled tests
tests_skipped = {}

result = executeReferenceChecked(
    prefix        = "simpleFunction",
    names         = globals(),
    tests_skipped = tests_skipped,
    tests_stderr  = tests_stderr
)

sys.exit(0 if result else 1)
