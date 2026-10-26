#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test coroutine and async generator frame cache visibility for Python 3.6 and newer."""

from __future__ import print_function

import asyncio
import gc
import sys
import threading


def compiled_frame_names():
    result = []

    for obj in gc.get_objects():
        if type(obj).__name__ == "compiled_frame":
            result.append(obj.f_code.co_name)

    return result


def count_compiled_frames(name):
    return compiled_frame_names().count(name)


async def coro(event):
    await event.wait()
    return 1


async def agen():
    yield 1
    await asyncio.sleep(0)
    yield 2


def run_async(function):
    if sys.version_info >= (3, 7):
        asyncio.run(function())
    else:
        loop = asyncio.new_event_loop()

        try:
            loop.run_until_complete(function())
        finally:
            loop.close()


async def threaded_worker():
    for _ in range(100):
        event = asyncio.Event()
        coroutine = coro(event)
        task = asyncio.ensure_future(coroutine)

        await asyncio.sleep(0)
        await asyncio.sleep(0)

        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        asyncgen = agen()
        await asyncgen.__anext__()
        await asyncgen.aclose()


def threaded_stress():
    threads = [
        threading.Thread(target=run_async, args=(threaded_worker,)) for _ in range(4)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


async def check_coroutine():
    gc.collect()
    assert count_compiled_frames("coro") == 0

    event = asyncio.Event()
    coroutine = coro(event)
    task = asyncio.ensure_future(coroutine)

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert coroutine.cr_frame is not None

    if type(coroutine.cr_frame).__name__ == "compiled_frame":
        assert gc.is_tracked(coroutine.cr_frame)
        assert count_compiled_frames("coro") >= 1

    event.set()
    await task
    gc.collect()
    assert count_compiled_frames("coro") == 0

    # A closed suspended coroutine must not leave a cache-only frame.
    event = asyncio.Event()
    coroutine = coro(event)

    try:
        coroutine.send(None)
    except StopIteration:
        pass

    assert coroutine.cr_frame is not None
    coroutine.close()

    del coroutine
    gc.collect()
    assert count_compiled_frames("coro") == 0


async def check_asyncgen():
    gc.collect()
    assert count_compiled_frames("agen") == 0

    asyncgen = agen()

    assert await asyncgen.__anext__() == 1

    if type(asyncgen.ag_frame).__name__ == "compiled_frame":
        assert gc.is_tracked(asyncgen.ag_frame)
        assert count_compiled_frames("agen") >= 1

    assert await asyncgen.__anext__() == 2

    try:
        await asyncgen.__anext__()
    except StopAsyncIteration:
        pass

    del asyncgen
    gc.collect()
    assert count_compiled_frames("agen") == 0

    # A closed suspended async generator must not leave a cache-only frame.
    asyncgen = agen()
    assert await asyncgen.__anext__() == 1
    await asyncgen.aclose()

    del asyncgen
    gc.collect()
    assert count_compiled_frames("agen") == 0


async def main():
    await check_coroutine()
    await check_asyncgen()

    threaded_stress()

    print("OK")


if sys.version_info >= (3, 7):
    asyncio.run(main())
else:
    run_async(main)

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
