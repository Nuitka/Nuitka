#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import binascii
import struct


def floatBits(value):
    return binascii.hexlify(struct.pack(">d", value)).decode("ascii")


def arithmeticTrees(flag):
    # Equal branch shapes prove exact floats without making their values constant.
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    c = -0.5 if flag else 2.0

    return (
        (a + b) + c,
        a + (b + c),
        ((a + b) + (a + 2.0)) + ((3.0 + b) + (a + c)),
        (a - b) - c,
        a - (b - c),
        ((a - b) - (a - 2.0)) - ((3.0 - b) - (a - c)),
        (a * b) * c,
        a * (b * c),
        ((a * b) * (a * 2.0)) * ((3.0 * b) * (a * c)),
        (a + b) * (a - c),
        (a * b) + (a - c),
        (a * b) - (a + c),
        (a - b) + (a * c),
        (a + b) - (a * c),
        (a - b) * (a + c),
    )


def numericEdges(flag):
    zero = -0.0 if flag else 0.0
    other_zero = 0.0 if flag else -0.0
    infinity = 1e400 if flag else -1e400
    nan = (1e400 - 1e400) if flag else -(1e400 - 1e400)
    smallest = 5e-324 if flag else 1e-323
    largest = 1.7976931348623157e308 if flag else 1e308

    return (
        (zero + zero) * 1.0,
        (zero - other_zero) * 1.0,
        (zero * -1.0) + other_zero,
        (smallest * 0.5) + smallest,
        (largest * 2.0) - largest,
        (infinity + 1.0) - infinity,
        (nan + 1.0) * 2.0,
        (1.0 + nan) * 2.0,
        (nan - 1.0) + zero,
        (1.0 - nan) + zero,
        (nan * smallest) - other_zero,
    )


def boxedAdd(a, b):
    return a + b


def boxedSubtract(a, b):
    return a - b


def boxedMultiply(a, b):
    return a * b


def roundingCases(flag):
    a = 1.0000000000000002 if flag else 1.0000000000000004
    b = 0.9999999999999999 if flag else 0.9999999999999998
    large = 9007199254740992.0 if flag else 18014398509481984.0

    fused_sensitive = (a * b) - 1.0
    separately_rounded = boxedSubtract(boxedMultiply(a, b), 1.0)
    assert floatBits(fused_sensitive) == floatBits(separately_rounded)

    cancellation = (large + 1.0) - large
    separate_cancellation = boxedSubtract(boxedAdd(large, 1.0), large)
    assert floatBits(cancellation) == floatBits(separate_cancellation)

    return fused_sensitive, cancellation


def recordCondition(events, label, failure):
    events.append(label)
    if label == failure:
        raise ValueError(label)
    return len(events) % 2


def sideEffectOperands(flag, failure):
    a = 1.25 if flag else -2.5
    events = []

    try:
        result = (
            (a + (1.0 if recordCondition(events, "left", failure) else 2.0))
            * (3.0 if recordCondition(events, "right", failure) else 4.0)
        ) - (5.0 if recordCondition(events, "last", failure) else 6.0)
    except ValueError as exception:
        return events, type(exception).__name__, str(exception)

    return events, floatBits(result)


def unknownValue(events, value):
    events.append("call")
    return value


def unknownRight(flag, value):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    events = []
    result = ((a + b) - a) * unknownValue(events, value)
    return events, result


def unknownLeft(flag, value):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    events = []
    result = unknownValue(events, value) * ((a + b) - a)
    return events, result


class FloatSubclass(float):
    def __mul__(self, other):
        return "subclass multiply", floatBits(other)

    def __rmul__(self, other):
        return "subclass reflected multiply", floatBits(other)


class FloatConvertible(object):
    def __float__(self):
        return 2.5


def conversionBoundary(flag, value):
    a = 1.25 if flag else -2.5
    return (a + float(value)) * a


def mixedIntegerBoundary(flag):
    a = 1.25 if flag else -2.5
    integer = 2 if flag else 2**54 + 1
    return (a + integer) * a, (integer - a) * a


def hugeIntegerBoundary(flag):
    a = 1.25 if flag else -2.5
    integer = 10**400 if flag else -(10**400)
    return (a + a) * integer


def divisionBoundary(flag):
    a = 1.25 if flag else -2.5
    divisor = -0.0 if flag else 2.0
    return ((a + a) * a) / divisor


def otherOperationBoundaries(flag):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return (a + b) // b, (a + b) % a, (a + b) ** 2.0, -(a + b)


def inplaceBoundary(flag):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    a += (b + 1.0) * (b - 2.0)
    a -= (b - 1.0) * (b + 2.0)
    a *= (b + 1.0) - (b - 2.0)
    return a


def comparisonBoundary(flag):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return (
        (a + b) == (a * b),
        (a + b) < (a * b),
        ((a + b) * b) >= ((a - b) * b),
        bool((a + b) * (a - b)),
    )


def identityBoundary(flag):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    value = (a + b) * (a - b)
    alias = value
    container = [value]
    local_values = locals()
    return (
        type(value) is float,
        value is alias,
        value is value,
        value is container[0],
        value is local_values["value"],
        alias is local_values["alias"],
    )


def normalAssignmentLoop(flag):
    value = 1.25 if flag else -2.5
    for unused in range(5):
        value = (value + 0.5) * 0.25
    return value


for test_flag in (False, True):
    print("Flag:", test_flag)
    print("Trees:", [floatBits(value) for value in arithmeticTrees(test_flag)])
    print("Numeric edges:", [floatBits(value) for value in numericEdges(test_flag)])
    print("Rounding:", [floatBits(value) for value in roundingCases(test_flag)])
    for failure_at in (None, "left", "right", "last"):
        print("Side effects:", failure_at, sideEffectOperands(test_flag, failure_at))
    for unknown in (2.5, 2, True, FloatSubclass(2.5)):
        print("Unknown right:", unknownRight(test_flag, unknown))
        print("Unknown left:", unknownLeft(test_flag, unknown))
    print("Conversion:", floatBits(conversionBoundary(test_flag, FloatConvertible())))
    print("Mixed integers:", mixedIntegerBoundary(test_flag))
    for exceptional_case in (hugeIntegerBoundary, divisionBoundary):
        try:
            print("Exceptional boundary:", exceptional_case(test_flag))
        except (OverflowError, ZeroDivisionError) as error:
            print("Exceptional boundary:", type(error).__name__)
    print("Other operations:", otherOperationBoundaries(test_flag))
    print("Inplace:", floatBits(inplaceBoundary(test_flag)))
    print("Comparisons:", comparisonBoundary(test_flag))
    print("Identity:", identityBoundary(test_flag))
    print("Normal assignment loop:", floatBits(normalAssignmentLoop(test_flag)))

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
