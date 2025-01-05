#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reference counting tests for features of Python3.5 or higher.

These contain functions that do specific things, where we have a suspect
that references may be lost or corrupted. Executing them repeatedly and
checking the reference count is how they are used.

These are Python3.5 specific constructs, that will give a SyntaxError or
not be relevant on older versions.
"""

# While we use that for comparison code, no need to compile that.
# nuitka-project: --nofollow-import-to=nuitka

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

# Tests do all bad things:
# pylint: disable=not-an-iterable

import asyncio
import types

from nuitka.PythonVersions import python_version
from nuitka.tools.testing.Common import executeReferenceChecked, run_async

# Tests do bad stuff, pylint: disable=redefined-outer-name


def raisy():
    raise TypeError


def simpleFunction1():
    async def someCoroutine():
        return

    run_async(someCoroutine())


####################################


def simpleFunction2():
    async def someCoroutine():
        return 7

    run_async(someCoroutine())


####################################


class AsyncIteratorWrapper:
    def __init__(self, obj):
        self._it = iter(obj)

    def __aiter__(self):
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

        # Python 3.5 before 3.5.2 won't allow this.
        try:
            async for letter in AsyncIteratorWrapper("abcdefg"):
                result.append(letter)
        except TypeError:
            assert sys.version_info < (3, 5, 2)

        return result

    run_async(f())


####################################


def simpleFunction4():
    async def someCoroutine():
        raise StopIteration

    try:
        run_async(someCoroutine())
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
    async def someCoroutine():
        async for _i in BadAsyncIter():
            print("never going to happen")

    try:
        run_async(someCoroutine())
    except TypeError:
        pass


def simpleFunction8():
    async def someCoroutine():
        return ("some", "thing")

    @types.coroutine
    def someDecoratorCoroutine():
        yield from someCoroutine()

    run_async(someDecoratorCoroutine())


def simpleFunction9():
    a = {"a": 1, "b": 2}
    b = {"c": 3, **a}

    return b


def sync_rmtree(path):
    raise FileNotFoundError


async def rmtree(path):
    return await asyncio.get_event_loop().run_in_executor(None, sync_rmtree, path)


async def execute():
    try:
        await rmtree("/tmp/test1234.txt")
    except FileNotFoundError:
        pass

    return 10**10


async def run():
    await execute()


def simpleFunction10():
    asyncio.get_event_loop().run_until_complete(run())


def simpleFunction11():
    async def someCoroutine():
        return 10

    coro = someCoroutine()

    def someGenerator():
        yield from coro

    try:
        list(someGenerator())
    except TypeError:
        pass

    coro.close()


def simpleFunction12():
    def func(x):
        x = [5, *x, 8]

        return x

    func([2, 3, 4])


# These need stderr to be wrapped.
tests_stderr = ()

# Disabled tests
tests_skipped = {}

if python_version < 0x380:
    tests_skipped[10] = "Incompatible refcount bugs of asyncio with python prior 3.8"

result = executeReferenceChecked(
    prefix="simpleFunction",
    names=globals(),
    tests_skipped=tests_skipped,
    tests_stderr=tests_stderr,
    explain=False,
)

print("OK." if result else "FAIL.")
sys.exit(0 if result else 1)

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
