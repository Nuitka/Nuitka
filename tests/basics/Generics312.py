#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Generic tests, cover most important forms of them."""

# Tests are dirty on purpose.
#
# pylint: disable=redefined-outer-name,used-before-assignment


def someGenericFunction[T]():
    print("hello", T)


someGenericFunction()

# Verify the name didn't leak.
try:
    print(T)
except NameError:
    print("not found")

T = 1


def someGenericFunctionShadowingGlobal[T]():
    print(T)


someGenericFunctionShadowingGlobal()
print(T)


print("Function in a class with private name")


class someClassWithPrivateArgumentNames:
    def f(self, *, __kw: 1):
        pass


print(someClassWithPrivateArgumentNames.f.__annotations__)


def simpleExample[T](test: T) -> T:
    print(test)
    return test


simpleExample(42)

try:
    print(T)
except NameError:
    print("good")

try:

    def weirdExample[T](a: T = T):
        print(a)

except NameError as err:
    print(err)

try:

    def weirdExample[*Ts](a: Ts = Ts):
        print(a)

except NameError as err:
    print(err)

try:

    def weirdExample[**P](a: P = P):
        print(a)

except NameError as err:
    print(err)


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
