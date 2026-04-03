#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


class AwaitException(Exception):
    pass


namespace = {"AwaitException": AwaitException}

exec(
    'import types\n\n'
    '@types.coroutine\n'
    'def awaitable():\n'
    '    yield ("throw",)\n\n'
    'async def leaf():\n'
    '    try:\n'
    '        await awaitable()\n'
    '    except AwaitException:\n'
    '        return b"payload"\n\n'
    'async def mid():\n'
    '    body = await leaf()\n'
    '    return {"body": body}\n\n'
    'async def leaf_empty():\n'
    '    try:\n'
    '        await awaitable()\n'
    '    except AwaitException:\n'
    '        return\n\n'
    'async def mid_empty():\n'
    '    body = await leaf_empty()\n'
    '    return {"body": body}\n',
    namespace,
)

mid = namespace["mid"]
mid_empty = namespace["mid_empty"]


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

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
