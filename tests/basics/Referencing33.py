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
import sys, os

# Find common code relative in file system. Not using packages for test stuff.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            ".."
        )
    )
)
from test_common import (
    executeReferenceChecked,
    my_print,
)

if not hasattr(sys, "gettotalrefcount"):
    my_print("Warning, using non-debug Python makes this test ineffective.")
    sys.gettotalrefcount = lambda : 0


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
