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

# Keep the inner coroutine uncompiled so the await path crosses the
# compiled/uncompiled coroutine boundary during cancellation handling.
bridge_namespace = {}

exec(
    """\
import asyncio

async def run_inner():
    current_task = asyncio.current_task()
    loop = asyncio.get_running_loop()
    result_future = loop.create_future()

    async def request_cancel():
        current_task.cancel()

    cancel_task = asyncio.create_task(request_cancel())

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


asyncio.run(top_cancel_await_bridge())

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
