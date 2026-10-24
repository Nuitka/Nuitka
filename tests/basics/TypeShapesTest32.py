#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Operations where type shape knowledge must match what CPython does."""

from __future__ import print_function


def bytesAddBytearray(value):
    b = bytes(value, "ascii")
    r = b + bytearray(value, "ascii")

    print("bytes + bytearray type:", type(r))

    try:
        r.append(65)
    except AttributeError as e:
        print("bytes + bytearray append:", repr(e))
    else:
        print("bytes + bytearray append worked:", r)


def typeLessThanType(left, right):
    try:
        type(left) < type(right)
    except TypeError as e:
        print("type < type:", repr(e))
    else:
        print("type < type: no exception")


def typeLessThanTypeValue(left, right):
    try:
        result = type(left) < type(right)
    except TypeError as e:
        print("type < type value:", repr(e))
    else:
        print("type < type value:", result)


class OrderedMeta(type):
    def __lt__(cls, other):
        return cls.__name__ < other.__name__


class OrderedA(OrderedMeta("OrderedBase", (object,), {})):
    pass


class OrderedB(OrderedMeta("OrderedBase", (object,), {})):
    pass


def numberFromBytearray(value):
    ba = bytearray(value, "ascii")

    print("int(bytearray):", int(ba))
    print("float(bytearray):", float(ba))


def noneOrType(value):
    n = None

    try:
        r = n | type(value)
    except TypeError as e:
        print("None | type:", repr(e))
    else:
        print("None | type:", r)


bytesAddBytearray("12")
typeLessThanType(1, 2)
typeLessThanType(OrderedA(), OrderedB())
typeLessThanTypeValue(1, 2)
typeLessThanTypeValue(OrderedA(), OrderedB())
typeLessThanTypeValue(OrderedB(), OrderedA())
numberFromBytearray("12")
noneOrType(1)

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
