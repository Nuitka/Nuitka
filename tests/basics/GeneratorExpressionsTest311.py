#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test cases for async comprehensions nested in generator expressions (Python 3.11+)."""

import asyncio
import inspect


async def async_val(x):
    return x * 10


async def async_list(x):
    return [x, x + 1]


async def async_iter(xs):
    for x in xs:
        yield x


def genexpr_with_setcomp_await(xs):
    return ({await async_val(y) for y in x} for x in xs)


def genexpr_with_setcomp_async_for(xs):
    return ({y async for y in async_iter(x)} for x in xs)


def genexpr_with_dictcomp_await_value(xs):
    return ({y: await async_val(y) for y in x} for x in xs)


def genexpr_with_dictcomp_await_key(xs):
    return ({await async_val(y): y for y in x} for x in xs)


def genexpr_with_dictcomp_async_for(xs):
    return ({y: y + 1 async for y in async_iter(x)} for x in xs)


def genexpr_with_multiclause_listcomp_await_iter(xs):
    return ([z for y in x for z in await async_list(y)] for x in xs)


def genexpr_with_multiclause_listcomp_async_for(xs):
    return ([z for y in x async for z in async_iter([y, y + 10])] for x in xs)


def genexpr_with_multiclause_listcomp_await_if(xs):
    return ([z for y in x for z in [y, y + 1] if await async_val(z) > 10] for x in xs)


def genexpr_multiclause_await_iter(xs):
    return (y for x in xs for y in await async_list(x))


def genexpr_target_subscript_await(xs, target_dict):
    return (x for target_dict[await async_val(1)] in xs for x in [target_dict[10]])


def genexpr_nested_async_genexpr(xs):
    return ((await async_val(y) for y in x) for x in xs)


def genexpr_nested_sync_genexpr_with_await_iter(xs):
    return ((y for y in await async_list(x)) for x in xs)


async def collect(agen):
    return [item async for item in agen]


async def main():
    g = genexpr_with_setcomp_await([[1, 2], [3]])
    print(
        "setcomp await:", inspect.isasyncgen(g), [sorted(s) for s in await collect(g)]
    )

    g = genexpr_with_setcomp_async_for([[1, 2], [3]])
    print(
        "setcomp async for:",
        inspect.isasyncgen(g),
        [sorted(s) for s in await collect(g)],
    )

    g = genexpr_with_dictcomp_await_value([[1, 2], [3]])
    print("dictcomp await value:", inspect.isasyncgen(g), await collect(g))

    g = genexpr_with_dictcomp_await_key([[1, 2], [3]])
    print("dictcomp await key:", inspect.isasyncgen(g), await collect(g))

    g = genexpr_with_dictcomp_async_for([[1, 2], [3]])
    print("dictcomp async for:", inspect.isasyncgen(g), await collect(g))

    g = genexpr_with_multiclause_listcomp_await_iter([[1, 2], [3]])
    print("listcomp multiclause await iter:", inspect.isasyncgen(g), await collect(g))

    g = genexpr_with_multiclause_listcomp_async_for([[1, 2], [3]])
    print("listcomp multiclause async for:", inspect.isasyncgen(g), await collect(g))

    g = genexpr_with_multiclause_listcomp_await_if([[1, 2], [3]])
    print("listcomp multiclause await if:", inspect.isasyncgen(g), await collect(g))

    g = genexpr_multiclause_await_iter([1, 3])
    print("genexpr multiclause await iter:", inspect.isasyncgen(g), await collect(g))

    target = {}
    g = genexpr_target_subscript_await([5, 6], target)
    print("genexpr target subscript await:", inspect.isasyncgen(g), await collect(g))

    g = genexpr_nested_async_genexpr([[1, 2], [3]])
    print(
        "nested async genexpr:",
        inspect.isgenerator(g),
        inspect.isasyncgen(g),
        [await collect(inner) for inner in g],
    )

    g = genexpr_nested_sync_genexpr_with_await_iter([1, 3])
    print(
        "nested sync genexpr await iter:",
        inspect.isasyncgen(g),
        [list(inner) for inner in await collect(g)],
    )


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
