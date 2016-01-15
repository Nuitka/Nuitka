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

def run_async(coro):
    values = []
    result = None
    while True:
        try:
            values.append(coro.send(None))
        except StopIteration as ex:
            result = ex.args[0] if ex.args else None
            break
    return values, result

def raisy():
    raise TypeError


def simpleFunction1():
    async def foo():
        return

    run_async(foo())

####################################

class AsyncIteratorWrapper:
    def __init__(self, obj):
        self._it = iter(obj)

    async def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            value = next(self._it)
        except StopIteration:
            raise StopAsyncIteration
        return value


def simpleFunction3():
    async def f():
        result = []

        async for letter in AsyncIteratorWrapper("abcdefg"):
            result.append(letter)

        return result

    run_async(f())

####################################

def simpleFunction2():
    async def foo():
        return 7

    run_async(foo())

def simpleFunction4():
    async def foo():
        raise StopIteration

    try:
        run_async(foo())
    except RuntimeError:
        pass

####################################

class ClassWithAsyncMethod:
    async def async_method(self):
        return self

def simpleFunction5():
    run_async(ClassWithAsyncMethod().async_method())

####################################

class BadAsyncIter:
    def __init__(self):
        self.weight = 1

    async def __aiter__(self):
        return self

    def __anext__(self):
        return ()

def simpleFunction7():
    async def foo():
        async for i in BadAsyncIter():
            print('never going to happen')

    try:
        run_async(foo())
    except TypeError:
        pass


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
