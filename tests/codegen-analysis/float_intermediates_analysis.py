#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function


def add_tree(flag):
    # Interior helpers cover FLOAT/FLOAT, FLOAT/CFLOAT, CFLOAT/FLOAT and CFLOAT/CFLOAT.
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return ((a + b) + (a + 2.0)) + ((3.0 + b) + (a + b))


def sub_tree(flag):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return ((a - b) - (a - 2.0)) - ((3.0 - b) - (a - b))


def mult_tree(flag):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return ((a * b) * (a * 2.0)) * ((3.0 * b) * (a * b))


def object_float_results(flag):
    # These roots retain FLOAT/FLOAT operands and OBJECT results.
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return a + b, a - b, a * b


def left_native_results(flag):
    # Each root has CFLOAT/FLOAT operands and an OBJECT result.
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return (a + b) + a, (a - b) - a, (a * b) * a


def right_native_results(flag):
    # Each root has FLOAT/CFLOAT operands and an OBJECT result.
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return a + (a + b), a - (a - b), a * (a * b)


def unknown_boundary(flag, unknown):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return (a + b) * unknown


def comparison_boundary(flag):
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return (a + b) < (a * b)


def comparison_with_interior(flag):
    # The comparison receives objects, but the addition remains an interior candidate.
    a = 1.25 if flag else -2.5
    b = 3.5 if flag else 4.25
    return ((a + b) * b) < a


def normal_assignment_loop(flag):
    value = 1.25 if flag else -2.5
    for unused in range(5):
        value = (value + 0.5) * 0.25
    return value


for test_flag in (False, True):
    print(add_tree(test_flag))
    print(sub_tree(test_flag))
    print(mult_tree(test_flag))
    print(object_float_results(test_flag))
    print(left_native_results(test_flag))
    print(right_native_results(test_flag))
    print(unknown_boundary(test_flag, 2.0))
    print(comparison_boundary(test_flag))
    print(comparison_with_interior(test_flag))
    print(normal_assignment_loop(test_flag))

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
