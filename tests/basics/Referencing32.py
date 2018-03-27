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
import sys, os

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
    checkDebugPython
)

checkDebugPython()


def simpleFunction1():
    def abc(*, exc=IOError):
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

        class A(Exception):
            pass

        class B(Exception):
            pass

        try:
            raise A('foo')
        except A as e1:
            raise B(str(e1)) from e1
    except Exception:
        pass

def simpleFunction4():
    a = 1

    def nonlocal_writer():
        nonlocal a

        for a in range(10):
            pass

    nonlocal_writer()

    assert a == 9, a

def simpleFunction5():
    x = 2

    def local_func(a: int, b: x*x):
        pass

    local_func(x, x)


def simpleFunction6():
    # Make sure exception state is cleaned up as soon as the except
    # block is left.

    class MyException(Exception):
        def __init__(self, obj):
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
    except KeyError as e:
        pass

range_low = 0
range_high = 256
range_step = 13


def simpleFunction7():
    # Make sure xranges work nicely
    return range(range_low,range_high,range_step)

def simpleFunction8():
    # Make sure xranges work nicely
    return range(range_low,range_high)

def simpleFunction9():
    # Make sure xranges work nicely
    return range(range_high)


# These need stderr to be wrapped.
tests_stderr = ()

# Disabled tests
tests_skipped = {}

result = executeReferenceChecked(
    prefix        = "simpleFunction",
    names         = globals(),
    tests_skipped = tests_skipped,
    tests_stderr  = tests_stderr
)

sys.exit(0 if result else 1)
