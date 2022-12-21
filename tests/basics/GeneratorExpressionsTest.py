#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" Generator expression tests

"""

from __future__ import print_function

import inspect

print("Generator expression that demonstrates the timing:")


def iteratorCreationTiming():
    def getIterable(x):
        print("Getting iterable", x)
        return Iterable(x)

    class Iterable:
        def __init__(self, x):
            self.x = x  # pylint: disable=invalid-name
            self.values = list(range(x))
            self.count = 0

        def __iter__(self):
            print("Giving iterator now", self.x)

            return self

        def __next__(self):
            print("Next of", self.x, "is", self.count)

            if len(self.values) > self.count:
                self.count += 1

                return self.values[self.count - 1]
            else:
                print("Raising StopIteration for", self.x)

                raise StopIteration

        # Python2/3 compatibility.
        next = __next__

        def __del__(self):
            print("Deleting", self.x)

    gen = ((y, z) for y in getIterable(3) for z in getIterable(2))

    print("Using generator", gen)
    next(gen)
    res = tuple(gen)
    print(res)

    print("*" * 20)

    try:
        next(gen)
    except StopIteration:
        print("Usage past end gave StopIteration exception as expected.")

        try:
            print("Generator state then is", inspect.getgeneratorstate(gen))
        except AttributeError:
            pass

        print("Its frame is now", gen.gi_frame)

    print("Early aborting generator:")

    gen2 = ((y, z) for y in getIterable(3) for z in getIterable(2))
    del gen2


iteratorCreationTiming()

print("Generator expressions that demonstrate the use of conditions:")

print(tuple(x for x in range(8) if x % 2 == 1))
print(tuple(x for x in range(8) if x % 2 == 1 for z in range(8) if z == x))

print(tuple(x for (x, y) in zip(list(range(2)), list(range(4)))))

print("Directory of generator expressions:")
for_dir = (x for x in [1])

gen_dir = dir(for_dir)

print(sorted(g for g in gen_dir))


def genexprSend():
    x = (x for x in range(9))

    print("Sending too early:")
    try:
        x.send(3)
    except TypeError as e:
        print("Gave expected TypeError with text:", e)

    try:
        z = next(x)
    except StopIteration as e:
        print("Gave expected (3.10.0/1 only) StopIteration with text:", repr(e))
    else:
        print("Next return value (pre 3.10)", z)

    try:
        y = x.send(3)
    except StopIteration as e:
        print("Gave expected (3.10.0/1 only) StopIteration with text:", repr(e))
    else:
        print("Send return value", y)

    try:
        print("And then next gave", next(x))
    except StopIteration as e:
        print("Gave expected (3.10.0/1 only) StopIteration with text:", repr(e))

    print("Throwing an exception to it.")
    try:
        x.throw(2)
        assert False
    except TypeError as e:
        print("Gave expected TypeError:", e)

    print("Throwing an exception to it.")
    try:
        x.throw(ValueError(2))
    except ValueError as e:
        print("Gave expected ValueError:", e)

    try:
        next(x)
        print("Next worked even after thrown error")
    except StopIteration as e:
        print("Gave expected stop iteration after throwing exception in it:", e)

    print("Throwing another exception from it.")
    try:
        x.throw(ValueError(5))
    except ValueError as e:
        print("Gave expected ValueError with text:", e)


print("Generator expressions have send too:")

genexprSend()


def genexprClose():
    x = (x for x in range(9))

    print("Immediate close:")

    x.close()
    print("Closed once")

    x.close()
    print("Closed again without any trouble")


genexprClose()


def genexprThrown():
    def checked(z):
        if z == 3:
            raise ValueError

        return z

    x = (checked(x) for x in range(9))

    try:
        for count, value in enumerate(x):
            print(count, value)
    except ValueError:
        print(count + 1, ValueError)

    try:
        next(x)

        print(
            "Allowed to do next() after raised exception from the generator expression"
        )
    except StopIteration:
        print("Exception in generator, disallowed next() afterwards.")


genexprThrown()


def nestedExpressions():
    a = [x for x in range(10)]
    b = (x for x in (y for y in a))

    print("nested generator expression", list(b))


nestedExpressions()


def lambdaGenerators():
    a = 1

    x = lambda: (yield a)

    print("Simple lambda generator", x, x(), list(x()))

    y = lambda: ((yield 1), (yield 2))

    print("Complex lambda generator", y, y(), list(y()))


lambdaGenerators()


def functionGenerators():
    # Like lambdaGenerators, to show how functions behave differently if at all.

    a = 1

    def x():
        yield a

    print("Simple function generator", x, x(), list(x()))

    def y():
        yield ((yield 1), (yield 2))

    print("Complex function generator", y, y(), list(y()))


functionGenerators()
