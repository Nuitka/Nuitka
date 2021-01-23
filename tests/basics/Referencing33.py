#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Reference counting tests.

These contain functions that do specific things, where we have a suspect
that references may be lost or corrupted. Executing them repeatedly and
checking the reference count is how they are used.

These are Python3 specific constructs, that will give a SyntaxError or
not be relevant on Python2.
"""

import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

import types

from nuitka.tools.testing.Common import (
    executeReferenceChecked,
    someGenerator,
    someGeneratorRaising,
)


def simpleFunction1():
    def abc(*, _exc=IOError):
        pass

    for _ in range(100):
        abc()


def simpleFunction2():
    def abc(*, exc=IOError):
        raise ValueError from None

    try:
        abc()
    except (ValueError, TypeError):
        pass


def simpleFunction3():
    try:

        class ClassA(Exception):
            pass

        class ClassB(Exception):
            pass

        try:
            raise ClassA("foo")
        except ClassA as e1:
            raise ClassB(str(e1)) from e1
    except Exception:  # different to Nuitka, pylint: disable=broad-except
        pass


def simpleFunction4():
    a = 1

    def nonlocal_writer():
        nonlocal a

        for a in range(10):  # false alarm, pylint: disable=unused-variable
            pass

    nonlocal_writer()

    assert a == 9, a


def simpleFunction5():
    x = 2

    def local_func(_a: int, _b: x * x):
        pass

    local_func(x, x)


def simpleFunction6():
    # Make sure exception state is cleaned up as soon as the except
    # block is left.

    class MyException(Exception):
        def __init__(self, obj):
            # This is on purpose not called, pylint: disable=super-init-not-called
            self.obj = obj

    class MyObj:
        pass

    def inner_raising_func():
        local_ref = obj
        raise MyException(obj)

    # "except" block raising another exception
    obj = MyObj()

    try:
        try:
            inner_raising_func()
        except:
            raise KeyError
    except KeyError as e:  # on purpose, pylint: disable=unused-variable
        pass


range_low = 0
range_high = 256
range_step = 13


def simpleFunction7():
    # Make sure xranges work nicely
    return range(range_low, range_high, range_step)


def simpleFunction8():
    # Make sure xranges work nicely
    return range(range_low, range_high)


def simpleFunction9():
    # Make sure xranges work nicely
    return range(range_high)


def simpleFunction10():
    def f(_x: int) -> int:
        pass

    return f


def simpleFunction11():
    try:
        raise ImportError(path="lala", name="lele")
    except ImportError as e:
        assert e.name == "lele"
        assert e.path == "lala"


def simpleFunction12():
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

    _x = list(f())


def simpleFunction13():
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
        _x = list(f())
    except TypeError:
        pass


# Broken iterator class.
class Broken:
    def __iter__(self):
        return self

    def __next__(self):
        return 1

    def __getattr__(self, attr):

        1 / 0  # pylint: disable=pointless-statement


def simpleFunction14():
    def g():
        yield from Broken()

    try:
        gi = g()
        next(gi)
    except Exception:  # pylint: disable=broad-except
        pass


def simpleFunction15():
    def g():
        yield from Broken()

    try:
        gi = g()
        next(gi)
        gi.throw(AttributeError)
    except Exception:  # pylint: disable=broad-except
        pass


def simpleFunction16():
    def g():
        yield from (2, 3)

    return list(g())


def simpleFunction17():
    def g():
        yield from (2, 3)

        return 9

    return list(g())


def simpleFunction18():
    def g():
        yield from (2, 3)

        return 9, 8

    return list(g())


def simpleFunction19():
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


def simpleFunction20():
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


def simpleFunction21():
    def g():
        x = ClassIteratorBrokenClose()

        yield from x

    gen = g()
    next(gen)

    try:
        gen.throw(GeneratorExit)
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


def simpleFunction22():
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
        # This should not be subject normalize exceptions.
        assert len(args) == 1, args

    __next__ = next


# Lets have an exception that must not be instantiated.
class MyError(Exception):
    def __init__(self):
        # pylint: disable=super-init-not-called
        assert False


def simpleFunction23():
    def g():
        x = ClassIteratorRejectingThrow()

        yield from x

    gen = g()
    next(gen)

    gen.throw(MyError)


# These need stderr to be wrapped.
tests_stderr = (14, 15)

# Disabled tests
tests_skipped = {}

result = executeReferenceChecked(
    prefix="simpleFunction",
    names=globals(),
    tests_skipped=tests_skipped,
    tests_stderr=tests_stderr,
)

sys.exit(0 if result else 1)
