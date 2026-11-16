#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests for asynchronous generator exception state."""

import asyncio
import sys


def current_exception():
    return sys.exc_info()[1]


def run_async(awaitable):
    if hasattr(asyncio, "run"):
        asyncio.run(awaitable)
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(awaitable)


# Async generator athrow context, and state restored on a later resume.
async def agen_context():
    try:
        raise KeyError("agen handled")
    except KeyError:
        yield 1


async def run_agen_context():
    agen = agen_context()
    await agen.__anext__()
    try:
        await agen.athrow(ValueError("agen thrown"))
    except ValueError as e:
        print("Async generator throw context: %r" % (e.__context__,))


run_async(run_agen_context())


async def agen_leak():
    yield 0
    try:
        raise KeyError("agen in generator")
    except KeyError:
        yield 1
    yield 2


async def caller_agen_leak():
    agen = agen_leak()
    await agen.__anext__()
    try:
        raise ValueError("agen caller")
    except ValueError:
        await agen.__anext__()
    await agen.__anext__()
    try:
        await agen.__anext__()
    except StopAsyncIteration:
        pass
    print("Async generator after handler: %r" % (current_exception(),))


run_async(caller_agen_leak())

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
