#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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
