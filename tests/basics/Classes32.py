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
try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict

print("Call order of Python3 metaclasses:")


def a():
    x = 1

    class A:
        print("Class body a.A is evaluating closure x", x)

    print("Called", a)

    return A


def b():
    class B:
        pass

    print("Called", b)

    return B


def displayable(dictionary):
    return sorted(dictionary.items())


def m():
    class M(type):
        def __new__(cls, class_name, bases, attrs, **over):
            print(
                "Metaclass M.__new__ cls",
                cls,
                "name",
                class_name,
                "bases",
                bases,
                "dict",
                displayable(attrs),
                "extra class defs",
                displayable(over),
            )

            return type.__new__(cls, class_name, bases, attrs)

        def __init__(self, name, bases, attrs, **over):
            print(
                "Metaclass M.__init__",
                name,
                bases,
                displayable(attrs),
                displayable(over),
            )
            super().__init__(name, bases, attrs)

        def __prepare__(metacls, bases, **over):  # @NoSelf
            print("Metaclass M.__prepare__", metacls, bases, displayable(over))
            return OrderedDict()

    print("Called", m)

    return M


def d():
    print("Called", d)

    return 1


def e():
    print("Called", e)

    return 2


class C1(a(), b(), other=d(), metaclass=m(), yet_other=e()):
    import sys

    # TODO: Enable this.
    # print("C1 locals type is", type(sys._getframe().f_locals))


print("OK, class created", C1)

print("Attribute C1.__dict__ has type", type(C1.__dict__))


print("Function local classes can be made global and get proper __qualname__:")


def someFunctionWithLocalClassesMadeGlobal():
    # Affects __qualname__ only in Python3.4 or higher, not in Python3.2
    global C

    class C:
        pass

        class D:
            pass

        try:
            print("Nested class qualname is", D.__qualname__)
        except AttributeError:
            # Python3.2
            pass

    try:
        print("Local class made global qualname is", C.__qualname__)
    except AttributeError:
        pass


someFunctionWithLocalClassesMadeGlobal()

print("Function in a class with private name")


class someClassWithPrivateArgumentNames:
    def f(self, *, __kw: 1):
        pass


print(someClassWithPrivateArgumentNames.f.__annotations__)
print("OK.")
