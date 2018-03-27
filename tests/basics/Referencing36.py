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
    checkDebugPython,
    async_iterate,
    run_async
)

checkDebugPython()


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
            return ex.args[0]

        if fut == ('throw',):
            exc = True


def simpleFunction1():
    async def gen1():
        try:
            yield
        except:
            pass

    async def run():
            g = gen1()
            await g.asend(None)
            await g.asend(None)

    try:
        run_async(run())
    except StopAsyncIteration:
        pass


def simpleFunction2():
    async def async_gen():
        try:
            yield 1
            yield 1.1
            1 / 0
        finally:
            yield 2
            yield 3

        yield 100

    async_iterate(async_gen())


@types.coroutine
def awaitable(*, throw=False):
    if throw:
        yield ('throw',)
    else:
        yield ('result',)


async def gen2():
    await awaitable()
    a = yield 123
    # self.assertIs(a, None)
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
    except StopIteration as ex:
        pass

    ai.__anext__().__next__()

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
