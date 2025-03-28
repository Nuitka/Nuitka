#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


def displayDict(d):
    result = "{"
    first = True
    for key, value in sorted(d.items()):
        if not first:
            result += ","

        result += "%s: %s" % (repr(key), repr(value))
        first = False
    result += "}"

    return result


def kw_only_simple(*, a):
    return a


print("Keyword only function case: ", kw_only_simple(a=3))


def kw_only_simple_defaulted(*, a=5):
    return a


print("Keyword only function, using default value: ", kw_only_simple_defaulted())


def default1():
    print("Called", default1)
    return 1


def default2():
    print("Called", default2)

    return 2


def default3():
    print("Called", default3)
    return 3


def default4():
    print("Called", default4)

    return 4


def annotation1():
    print("Called", annotation1)

    return "a1"


def annotation2():
    print("Called", annotation2)

    return "a2"


def annotation3():
    print("Called", annotation3)

    return "a3"


def annotation4():
    print("Called", annotation4)

    return "a4"


def annotation5():
    print("Called", annotation5)

    return "a5"


def annotation6():
    print("Called", annotation6)

    return "a6"


def annotation7():
    print("Called", annotation7)

    return "a7"


def annotation8():
    print("Called", annotation8)

    return "a8"


def annotation9():
    print("Called", annotation9)

    return "a9"


print("Defining function with annotations, and defaults as functions for everything:")


def kw_only_func(
    x: annotation1(),
    y: annotation2() = default1(),
    z: annotation3() = default2(),
    *,
    a: annotation4(),
    b: annotation5() = default3(),
    c: annotation6() = default4(),
    d: annotation7(),
    **kw: annotation8()
) -> annotation9():
    print(x, y, z, a, b, c, d)


print("__kwdefaults__", displayDict(kw_only_func.__kwdefaults__))

print("Keyword only function called:")
kw_only_func(7, a=8, d=12)
print("OK.")

print("Annotations come out as", sorted(kw_only_func.__annotations__))
kw_only_func.__annotations__ = {}
print("After updating to None it is", kw_only_func.__annotations__)

kw_only_func.__annotations__ = {"k": 9}
print("After updating to None it is", kw_only_func.__annotations__)


def kw_only_star_func(*, a, b, **d):
    return a, b, d


print("kw_only_star_func:", kw_only_star_func(a=8, b=12, k=9, j=7))


def deeplyNestedNonLocalWrite():
    x = 0
    y = 0

    def f():
        def g():
            nonlocal x

            x = 3

            return x

        return g()

    return f(), x


print("Deeply nested non local writing function:", deeplyNestedNonLocalWrite())


def deletingClosureVariable():
    try:
        x = 1

        def g():
            nonlocal x

            del x

        g()
        g()
    except Exception as e:
        return repr(e)


print("Using deleted non-local variable:", deletingClosureVariable())

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
