#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

These are Python3.5 specific constructs, that will give a SyntaxError or
not be relevant on older versions.
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
    checkDebugPython,
    executeReferenceChecked,
    run_async,
)

checkDebugPython()


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

        # Python 3.5 before 3.2 won't allow this.
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
        async for i in BadAsyncIter():
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


# These need stderr to be wrapped.
tests_stderr = ()

# Disabled tests
tests_skipped = {}

result = executeReferenceChecked(
    prefix="simpleFunction",
    names=globals(),
    tests_skipped=tests_skipped,
    tests_stderr=tests_stderr,
)

sys.exit(0 if result else 1)
