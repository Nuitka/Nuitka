#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests for coroutine throw() and cancel/await bridge handling."""

import asyncio
import sys


class AwaitException(Exception):
    pass


throw_namespace = {"AwaitException": AwaitException}

exec(
    """\
import types

@types.coroutine
def awaitable():
    yield ("throw",)

async def leaf():
    try:
        await awaitable()
    except AwaitException:
        return b"payload"

async def mid():
    body = await leaf()
    return {"body": body}

async def leaf_empty():
    try:
        await awaitable()
    except AwaitException:
        return

async def mid_empty():
    body = await leaf_empty()
    return {"body": body}
""",
    throw_namespace,
)

mid = throw_namespace["mid"]
mid_empty = throw_namespace["mid_empty"]


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


async def top():
    return await mid()


async def top_empty():
    return await mid_empty()


print(run_until_complete(top()))
print(run_until_complete(top_empty()))

send_namespace = {}

exec(
    """\
import types

@types.coroutine
def resume_with_value():
    result = yield ("send",)
    return result
""",
    send_namespace,
)


def run_until_complete_with_send(coro, value):
    first = coro.send(None)
    assert first == ("send",), first

    try:
        coro.send(value)
    except StopIteration as ex:
        return ex.args[0] if ex.args else None

    assert False, "coroutine should have completed"


async def top_send_value_bridge():
    result = await send_namespace["resume_with_value"]()
    print(type(result).__module__, type(result).__name__, repr(result))


run_until_complete_with_send(top_send_value_bridge(), {"sent": 17})

# Keep the inner coroutine uncompiled so the await path crosses the
# compiled/uncompiled coroutine boundary during cancellation handling.
bridge_namespace = {}

exec(
    """\
import asyncio

def get_current_task(loop):
    if hasattr(asyncio, "current_task"):
        return asyncio.current_task()

    return asyncio.Task.current_task(loop=loop)

def create_future(loop):
    if hasattr(loop, "create_future"):
        return loop.create_future()

    return asyncio.Future(loop=loop)

def create_task(loop, coro):
    if hasattr(asyncio, "create_task"):
        return asyncio.create_task(coro)

    return asyncio.ensure_future(coro, loop=loop)

async def run_inner():
    loop = asyncio.get_event_loop()
    current_task = get_current_task(loop)
    result_future = create_future(loop)

    async def request_cancel():
        current_task.cancel()

    cancel_task = create_task(loop, request_cancel())

    def deliver_result(_task):
        if not result_future.done():
            result_future.set_result(42)

    cancel_task.add_done_callback(deliver_result)

    try:
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        return await result_future
""",
    bridge_namespace,
)


async def top_cancel_await_bridge():
    result = await bridge_namespace["run_inner"]()
    print(type(result).__module__, type(result).__name__, repr(result))


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    finally:
        asyncio.set_event_loop(None)
        loop.close()


run_async(top_cancel_await_bridge())

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
