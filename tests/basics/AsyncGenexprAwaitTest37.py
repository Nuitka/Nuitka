#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Async genexpr: sync-for with await vs async-for.

* Sync ``for`` plus ``await`` in the element must not treat the outer
  list iterator as awaitable (would surface as Task got bad yield).
* ``async for`` genexpr must still work when created in a normal ``def``,
  where getting the async iterator is deferred until the asyncgen runs
  (cannot await at construction time in a sync function).
"""

import asyncio


async def val(x):
    return x


async def arange(n):
    for i in range(n):
        yield i


def make_arange(n):
    return (i async for i in arange(n))


async def main():
    agen = (await val(x) for x in [1])
    print(await agen.__anext__())

    agen2 = make_arange(3)
    print(await agen2.__anext__())


asyncio.run(main())

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
