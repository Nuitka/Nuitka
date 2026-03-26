#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# TODO: Make these work

if False:

    class GenericInInstanceMethod:
        @property
        def get[T](self):
            print(f"GenericInInstanceMethod:get -> {T}")

        def method[T](self):
            print(f"GenericInInstanceMethod:method -> {T}")

    class GenericInStaticMethod:
        @staticmethod
        def method[T]():
            print(f"GenericInStaticMethod:method -> {T}")

    class GenericInClassMethod:
        @classmethod
        def method[T](cls):
            print(f"GenericInClassMethod:method -> {T}")

    GenericInInstanceMethod().get
    GenericInInstanceMethod().method()
    GenericInStaticMethod.method()
    GenericInClassMethod.method()


class Parent[T]:
    value: T
    print(T)


class Child[T](Parent[T]):
    another_value: int
    print(T)


class MultiTypeVarGeneric[T1, T2]:
    generic_value_1: T1
    generic_value_2: T2
    print(T1)
    print(T2)


class MultiParamSpecGeneric[**P1, **P2]:
    generic_value_1: P1
    generic_value_2: P2
    print(P1)
    print(P2)


try:
    print(T)
    print(T1)
    print(T2)
    print(P1)
    print(P2)
except NameError:
    print("!!!")


class Base[T, V]: ...


class Sub[Silly](Base[Silly, str]): ...


print("Base parameters", Base.__parameters__)
print("Base bases", Base.__bases__, Base.__orig_bases__)
print("Subclass parameters", Sub.__parameters__)
print("Subclass bases", Sub.__bases__, Sub.__orig_bases__)
print("Subclass with param", Sub[int], type(Sub[int]))

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
