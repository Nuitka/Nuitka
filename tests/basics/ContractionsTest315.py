#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


import collections.abc
import types

print([*i for i in [[1, 2, 3], [4, 5, 6]]])
print({*i for i in [[1, 2, 3], [4, 5, 6]]})
print(list((*i for i in [[1, 2, 3], [4, 5, 6]])))
print({**a for a in [{1: 2}, {3: 4}]})


async def numbers():
    yield [1, 2, 3]
    yield [4, 5, 6]


async def listComp():
    print([*i async for i in numbers()])


async def setComp():
    print({*i async for i in numbers()})


async def genExp():
    async for i in (*i async for i in numbers()):
        print(i)


async def dictComp():
    async def dicts():
        yield {1: 2}
        yield {3: 4}

    for i in {**d async for d in dicts()}.items():
        print(i)


def run_coro(coro):
    while True:
        try:
            coro.send(None)
        except StopIteration:
            break


run_coro(listComp())
run_coro(setComp())
run_coro(genExp())
run_coro(dictComp())


class CustomMapping(collections.abc.Mapping):
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class BadKeysError:
    def keys(self):
        raise AttributeError("inside keys")


class BadGetItemError:
    def keys(self):
        return ["a"]

    def __getitem__(self, _key):
        raise AttributeError("inside getitem")


class KeysPropertyError:
    @property
    def keys(self):
        raise AttributeError("keys property")


class KeysNotIterable:
    def keys(self):
        return 42


print(
    "Mappings unpacked:",
    sorted(
        {
            **m
            for m in [
                {"a": 1, "b": 2},
                types.MappingProxyType({"b": 20, "c": 30}),
                CustomMapping({"c": 300, "d": 400}),
            ]
        }.items()
    ),
)

bad_mappings = (
    123,
    [("a", 1)],
    collections.UserList(),
    KeysPropertyError(),
    BadKeysError(),
    BadGetItemError(),
    KeysNotIterable(),
)

for bad in bad_mappings:
    try:
        res = {**m for m in [{"ok": 1}, bad]}
    except Exception as exc:
        print(
            "comprehension",
            type(bad).__name__,
            "->",
            type(exc).__name__,
            str(exc),
            type(exc.__context__).__name__,
        )
    else:
        print("comprehension", type(bad).__name__, "-> no error", res)

for bad in bad_mappings:
    try:
        res = {**bad}
    except Exception as exc:
        print(
            "display",
            type(bad).__name__,
            "->",
            type(exc).__name__,
            str(exc),
            type(exc.__context__).__name__,
        )
    else:
        print("display", type(bad).__name__, "-> no error", res)


def clonedFinallySetContraction(flag):
    try:
        if flag:
            return "returned"

        print("body")
    finally:
        values = {x for x in range(3)}
        print("finally", sorted(values))


def clonedFinallyDictContraction(flag):
    try:
        if flag:
            return "returned"

        print("body")
    finally:
        values = {x: x * 2 for x in range(3)}
        print("finally", sorted(values.items()))


print(clonedFinallySetContraction(False))
print(clonedFinallySetContraction(True))
print(clonedFinallyDictContraction(False))
print(clonedFinallyDictContraction(True))

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
