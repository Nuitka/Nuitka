#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Comparison chains are multiple comparisons in one expression.

"""

from __future__ import print_function

# pylint: disable=redefined-outer-name


def simple_comparisons(x, y):
    if "a" <= x <= y <= "z":
        print("One")

    if "a" <= x <= "z":
        print("Two")

    if "a" <= x > "z":
        print("Three")


print("Simple comparisons:")

simple_comparisons("c", "d")


def side_effect():
    print("<side_effect>")

    return 7


def side_effect_comparisons():
    print("Should have side effect:")
    print(1 < side_effect() < 9)

    print("Should not have side effect due to short circuit:")
    print(3 < 2 < side_effect() < 9)


print("Check for expected side effects only:")

side_effect_comparisons()


def function_torture_is():
    a = (1, 2, 3)

    for x in a:
        for y in a:
            for z in a:
                print(x, y, z, ":", x is y is z, x is not y is not z)


function_torture_is()

print("Check if lambda can have expression chains:", end="")


def function_lambda_with_chain():

    a = (1, 2, 3)

    x = lambda x: x[0] < x[1] < x[2]

    print("lambda result is", x(a))


function_lambda_with_chain()

print("Check if generators can have expression chains:", end="")


def generator_function_with_chain():
    x = (1, 2, 3)

    yield x[0] < x[1] < x[2]


print(list(generator_function_with_chain()))

print("Check if list contractions can have expression chains:", end="")


def contraction_with_chain():
    return [x[0] < x[1] < x[2] for x in [(1, 2, 3)]]


print(contraction_with_chain())

print("Check if generator expressions can have expression chains:", end="")


def genexpr_with_chain():
    return (x[0] < x[1] < x[2] for x in [(1, 2, 3)])


print(list(genexpr_with_chain()))

print("Check if class bodies can have expression chains:", end="")


class ClassWithComparisonChainInBody:
    x = (1, 2, 3)
    print(x[0] < x[1] < x[2])


x = (1, 2, 3)
print(x[0] < x[1] < x[2])


class CustomOps(int):
    def __lt__(self, other):
        print("enter <", self, other)

        return True

    def __gt__(self, other):
        print("enter >", self, other)

        return False


print("Custom ops, to enforce chain eval order and short circuit:", end="")
print(CustomOps(7) < CustomOps(8) > CustomOps(6))

print("Custom ops, doing short circuit:", end="")
print(CustomOps(8) > CustomOps(7) < CustomOps(6))


def inOperatorChain():
    print("In operator chains:")
    print(3 in [3, 4] in [[3, 4]])
    print(3 in [3, 4] not in [[3, 4]])

    if 3 in [3, 4] in [[3, 4]]:
        print("Yes")
    else:
        print("No")

    if 3 in [3, 4] not in [[3, 4]]:
        print("Yes")
    else:
        print("No")


inOperatorChain()

# Make sure the values are called and order is correct:


class TracingLessThan(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return "<Value %s %d>" % (self.name, self.value)

    def __lt__(self, other):
        print(
            "less than called for:",
            self,
            other,
            self.value,
            other.value,
            self.value < other.value,
        )

        if self.value < other.value:
            print("good")
            return 7
        else:
            print("bad")
            return 0


a = TracingLessThan("a", 1)
b = TracingLessThan("b", 2)
c = TracingLessThan("c", 0)

print(a < b < c)
print("*" * 80)

a = TracingLessThan("a", 2)
b = TracingLessThan("b", 1)
c = TracingLessThan("c", 0)

print(a < b < c)

# Partial type knowledge:
print("*" * 80)
print("Partial type knowledge in comparisons:")


def compareDigitsSuccess(x):
    return 2 < len(x) < 1000


def compareDigitsFirstFalse(x):
    return 3 < len(x) < 1000


def compareDigitsSecondFalse(x):
    return 2 < len(x) < 3


v = [20] * 3

print(compareDigitsSuccess(v))
print(compareDigitsFirstFalse(v))
print(compareDigitsSecondFalse(v))
