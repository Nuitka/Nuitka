#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --experimental=optimize-dual-int

from __future__ import print_function

# Large integers exceeding C long range, forcing NILONG dual-type path
a = 10**100
b = 10**50

# BINARY_OPERATION_SUB_NILONG_NILONG_NILONG
print(a - b)
print(b - a)

# BINARY_OPERATION_ADD_NILONG_NILONG_NILONG
print(a + b)

# Negative large integers
c = -(10**100)
d = -(10**50)
print(c - d)
print(c + d)

# BINARY_OPERATION_SUB_NILONG_NILONG_DIGIT / ADD_NILONG_NILONG_DIGIT
print(a - 1)
print(a + 1)

# BINARY_OPERATION_SUB_NILONG_DIGIT_NILONG / ADD_NILONG_DIGIT_NILONG
print(1 - a)
print(1 + a)

# Overflow scenario: values fit in C long but overflow on operation
# 2**62 is 4611686018427387904, fits in long (2**63-1 on 64-bit)
# Subtracting -2**62 gives 2**63 which exceeds LONG_MAX
e = 2**62
f = -(2**62)
print(e - f)
print(e + f)

# Mixed large/small
print(-a)
print(+a)

# Large int comparisons
print(a == b)
print(a != b)
print(a > b)
print(a < b)
print(a >= b)
print(a <= b)

# Subtraction with zero
print(a - 0)
print(0 - a)

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
