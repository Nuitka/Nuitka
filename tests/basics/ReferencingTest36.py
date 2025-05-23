#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reference counting tests for Python3.6 or higher.

These contain functions that do specific things, where we have a suspect
that references may be lost or corrupted. Executing them repeatedly and
checking the reference count is how they are used.

These are Python3.6 specific constructs, that will give a SyntaxError or
not be relevant on older versions.
"""

import os
import sys

# While we use that for comparison code, no need to compile that.
# nuitka-project: --nofollow-import-to=nuitka

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

import asyncio
import types

from nuitka.tools.testing.Common import (
    async_iterate,
    executeReferenceChecked,
    run_async,
)


class AwaitException(Exception):
    pass


def run_until_complete(coro):
    exc = False
    while True:
        try:
            if exc:
                exc = False
                fut = coro.throw(AwaitException)
            else:
                fut = coro.send(None)
        except StopIteration as ex:
            return ex.args[0] if ex.args else None

        if fut == ("throw",):
            exc = True


def simpleFunction1():
    async def gen1():
        try:
            yield
        except:  # pylint: disable=bare-except
            pass

    async def run():
        g = gen1()
        await g.asend(None)
        await g.asend(2772)

    try:
        run_async(run())
    except StopAsyncIteration:
        pass


def simpleFunction2():
    async def async_gen():
        try:
            yield 1
            yield 1.1
            1 / 0  # pylint: disable=pointless-statement
        finally:
            yield 2
            yield 3

        yield 100

    async_iterate(async_gen())


@types.coroutine
def awaitable(*, throw=False):
    if throw:
        yield ("throw",)
    else:
        yield ("result",)


async def gen2():
    await awaitable()
    a = yield 123
    assert a is None
    await awaitable()
    yield 456
    await awaitable()
    yield 789


def simpleFunction3():
    def to_list(gen):
        async def iterate():
            res = []
            async for i in gen:
                res.append(i)
            return res

        return run_until_complete(iterate())

    async def run2():
        return to_list(gen2())

    run_async(run2())


def simpleFunction4():
    g = gen2()
    ai = g.__aiter__()
    an = ai.__anext__()
    an.__next__()

    try:
        ai.__anext__().__next__()
    except StopIteration as _ex:
        pass
    except RuntimeError:
        # Python 3.8 doesn't like this anymore
        assert sys.version_info >= (3, 8)

    try:
        ai.__anext__().__next__()
    except RuntimeError:
        # Python 3.8 doesn't like this anymore
        assert sys.version_info >= (3, 8)


def simpleFunction5():
    t = 2

    class C:  # pylint: disable=invalid-name
        exec("u=2")  # pylint: disable=exec-used
        x: int = 2
        y: float = 2.0

        z = x + y + t * u  # pylint: disable=undefined-variable

        rawdata = b"The quick brown fox jumps over the lazy dog.\r\n"
        # Be slow so we don't depend on other modules
        rawdata += bytes(range(256))

    return C()


async def funcTrace1():
    return [await awaitable() for _i in range(50)]


def simpleFunction6():
    run_async(funcTrace1())


async def funcTrace2():
    result = []

    for _i in range(50):
        value = await awaitable()
        result.append(value)

    return result


def simpleFunction7():
    run_async(funcTrace2())


def simpleFunction8():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(None)

    async def waiter(timeout):
        await asyncio.sleep(timeout)
        yield 1

    async def wait():
        async for _ in waiter(1):
            pass

    t1 = loop.create_task(wait())
    t2 = loop.create_task(wait())

    loop.run_until_complete(asyncio.sleep(0.01))

    t1.cancel()
    t2.cancel()

    try:
        loop.run_until_complete(t1)
    except asyncio.CancelledError:
        pass
    try:
        loop.run_until_complete(t2)
    except asyncio.CancelledError:
        pass

    loop.run_until_complete(loop.shutdown_asyncgens())

    loop.close()


def simpleFunction9():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(None)

    async def gen():
        raise ZeroDivisionError
        yield 1

    async def to_list(gen):
        res = []
        async for i in gen:
            res.append(i)
        return res

    task = to_list(gen())

    try:
        loop.run_until_complete(task)
    except ZeroDivisionError:
        # print("GOT ZeroDivisionError from asyncgen")
        pass

    loop.close()


async def asyncgen_to_close():
    try:
        yield 1
    finally:
        await asyncio.sleep(0.001)


async def run_close_test():
    gen = asyncgen_to_close()
    it = gen.__aiter__()
    await it.__anext__()
    await gen.aclose()


def simpleFunction10():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(None)

    loop.run_until_complete(run_close_test())

    loop.close()


# These need stderr to be wrapped.
tests_stderr = ()

# Disabled tests
tests_skipped = {}

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
