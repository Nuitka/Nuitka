#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests for close() of generators and coroutines."""


def gen_return():
    try:
        yield
    except GeneratorExit:
        return "closed"


def gen_none():
    try:
        yield
    except GeneratorExit:
        pass


g = gen_return()
next(g)
print("Generator close return:", repr(g.close()))

g = gen_none()
next(g)
print("Generator close none:", repr(g.close()))

g = gen_return()
print("Generator close unstarted:", repr(g.close()))

g = gen_return()
next(g)
try:
    next(g)
except StopIteration:
    pass
print("Generator close exhausted:", repr(g.close()))


class Suspend:
    def __await__(self):
        yield None


async def coro_return():
    try:
        await Suspend()
    except GeneratorExit:
        return "closed"


async def coro_none():
    try:
        await Suspend()
    except GeneratorExit:
        pass


for factory in (coro_return, coro_none):
    coro = factory()
    coro.send(None)
    print("Coroutine close %s:" % factory.__name__, repr(coro.close()))

coro = coro_return()
print("Coroutine close unstarted:", repr(coro.close()))

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
