#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Operations on numbers with edge case values, using specialized helpers."""

from __future__ import print_function

import sys

# Values not known at compile time, but with known types after conversion.
values = {
    "inf": "inf",
    "-inf": "-inf",
    "nan": "nan",
    "1.0": "1.0",
    "-1.0": "-1.0",
    "-2.5": "-2.5",
    "0.5": "0.5",
    "-8": "-8",
    "min_ssize": str(-sys.maxsize - 1),
    "below_min_ssize": str(-sys.maxsize - 2),
    "above_max_ssize": str(sys.maxsize + 1),
    "-1": "-1",
}


def check(description, func, *args):
    try:
        result = func(*args)
    except Exception as e:  # pylint: disable=broad-except
        print(description, type(e).__name__)
    else:
        print(description, "->", type(result).__name__, repr(result))


def floatPowInplaceNanRefcount(value):
    a = float(value)
    nan = float(values["nan"])
    before = sys.getrefcount(nan)
    for _i in range(1000):
        a = float(value)
        a **= nan
    del a
    return before == sys.getrefcount(nan)


def constantBasePow(value):
    return 2.0 ** float(value)


def constantZeroBasePow(value):
    return 0.0 ** float(value)


def floatFloorDivInplace(left, right):
    a = float(left)
    a //= float(right)
    return a


def constantFloatFloorDiv(value):
    return 2.0 // float(value)


def sequenceRepeatMinimum(value):
    return "ab" * int(value), int(value) * (1,), [1] * int(value)


def complexPowBoolInplace(value):
    a = complex(float(value), 0)
    a **= True
    return a


def floatPowFractionalInplace(left, right):
    a = float(left)
    a **= float(right)
    return a + 1


def intPowFractional(left, right):
    return int(left) ** float(right) + 1


check("float **= nan keeps references", floatPowInplaceNanRefcount, values["1.0"])
check("float **= nan keeps references", floatPowInplaceNanRefcount, values["0.5"])
check("2.0 ** inf", constantBasePow, values["inf"])
check("0.0 ** -inf", constantZeroBasePow, values["-inf"])
check("1.0 //= -2.5", floatFloorDivInplace, values["1.0"], values["-2.5"])
check("2.0 // -2.5", constantFloatFloorDiv, values["-2.5"])
check("sequence * minimum index", sequenceRepeatMinimum, values["min_ssize"])
check(
    "sequence * below minimum index", sequenceRepeatMinimum, values["below_min_ssize"]
)
check(
    "sequence * above maximum index", sequenceRepeatMinimum, values["above_max_ssize"]
)
check("sequence * -1", sequenceRepeatMinimum, values["-1"])
check("complex(inf) **= True", complexPowBoolInplace, values["inf"])
check("-1.0 **= 0.5", floatPowFractionalInplace, values["-1.0"], values["0.5"])
check("-8 ** 0.5", intPowFractional, values["-8"], values["0.5"])

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
