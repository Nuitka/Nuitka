#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import sys

x = 2


def someFunction1():
    x = 3

    return x


def someFunction2():
    global x

    x = 4

    return x


def someFunction3():
    return x


def someNestedGlobalUser1():
    z = 1

    # Nested function that uses a global z doesn't affect the local variable z at all.
    def setZ():
        global z

        z = 3

    setZ()

    return z


def someNestedGlobalUser2():
    z = 1

    # Nested function that uses a global z doesn't affect the local variable z at
    # all. This doesn't change if it's done inside an exec block.
    exec(
        """
def setZ():
    global z

    z = 3

setZ()
"""
    )

    return z


def someNestedGlobalUser3a():
    # Nested function that uses a exec variable scope z and a global z, changes z to be
    # the global one only. We verify that by looking at locals. This means that the global
    # statement inside the function of exec changes the effect of the z.

    exec(
        """
z = 1

def setZ():
    global z

    z = 3

setZ()
"""
    )

    return z, locals().keys() == ["setZ"]


def someNestedGlobalUser3b():
    # Nested function that uses a exec variable scope z and a global z, changes
    # z to be the global one only. We verify that by looking at locals.

    exec(
        """
z = 1
"""
    )

    if sys.version_info[0] < 3:
        return z, locals().keys() == ["z"]
    else:
        return locals().keys() == []


def someNestedGlobalUser4():
    z = 1

    # This one proves that the local variable z is entirely ignored, and that the global z
    # has the value 2 inside setZ().

    exec(
        """
z = 2

def setZ():
    global z

    z = 3*z

setZ()
"""
    )
    return z


def someNestedGlobalUser5():
    z = 1

    # Without a global statement, z affects the local variable z.

    exec(
        """
z = 3

"""
    )
    return z


def someNestedGlobalUser6():
    # Without a global statement, a local variable z is created.

    exec(
        """
z = 7

"""
    )
    return z


print("Function that shadows a global variable with a local variable")
print(someFunction1())
print(
    "Function that accesses and changes a global variable declared with a global statement"
)
print(someFunction2())
print("Function that uses a global variable")
print(someFunction3())
print("Functions that uses a global variable in a nested function in various ways:")
print(someNestedGlobalUser1, someNestedGlobalUser1())
del z
print(someNestedGlobalUser2, someNestedGlobalUser2())
del z
print(someNestedGlobalUser3a, someNestedGlobalUser3a())
del z
print(someNestedGlobalUser3b, someNestedGlobalUser3b())
print(someNestedGlobalUser4, (someNestedGlobalUser4(), z))
del z
print(someNestedGlobalUser5, someNestedGlobalUser5())
z = 9
print(someNestedGlobalUser6, (someNestedGlobalUser6(), z))


x = 7


def f():
    x = 1

    def g():
        global x

        def i():
            def h():
                return x

            return h()

        return i()

    return g()


print(f())

global global_already
global_already = 1

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
