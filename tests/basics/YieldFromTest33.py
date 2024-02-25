#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


def g():
    for a in range(3):
        yield a

    return 7


def h():
    yield 4
    yield 5


def f():
    print("Yielded from returner", (yield g()))
    print("Yielded from non-return value", (yield h()))


print("Result", list(f()))

print("Yielder with return value", list(g()))


# This will raise when looking up any attribute.
class Broken:
    def __iter__(self):
        return self

    def __next__(self):
        return 1

    def __getattr__(self, attr):
        1 / 0


def test_broken_getattr_handling():
    def g():
        yield from Broken()

    print("Next with send: ", end="")
    try:
        gi = g()
        next(gi)
        gi.send(1)
    except Exception as e:
        print("Caught", repr(e))

    print("Next with throw: ", end="")
    try:
        gi = g()
        next(gi)
        gi.throw(AttributeError)
    except Exception as e:
        print("Caught", repr(e))

    print("Next with close: ", end="")
    try:
        gi = g()
        next(gi)
        gi.close()

        print("All good")
    except Exception as e:
        print("Caught", repr(e))


test_broken_getattr_handling()


def test_throw_caught_subgenerator_handling():
    def g1():
        try:
            print("Starting g1")
            yield "g1 ham"
            yield from g2()
            yield "g1 eggs"
        finally:
            print("Finishing g1")

    def g2():
        try:
            print("Starting g2")
            yield "g2 spam"
            yield "g2 more spam"
        except LunchError:
            print("Caught LunchError in g2")
            yield "g2 lunch saved"
            yield "g2 yet more spam"

    class LunchError(Exception):
        pass

    g = g1()
    for i in range(2):
        x = next(g)
        print("Yielded %s" % (x,))
    e = LunchError("tomato ejected")
    print("Throw returned", g.throw(e))
    print("Sub thrown")

    for x in g:
        print("Yielded %s" % (x,))


test_throw_caught_subgenerator_handling()


def give_cpython_generator():
    # TODO: This relies on eval not being inlined, which will become untrue.
    return eval("(x for x in range(3))")


def gen_compiled():
    yield from give_cpython_generator()
    yield ...
    yield from range(7)


print("Mixing uncompiled and compiled yield from:")
print(list(gen_compiled()))

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
