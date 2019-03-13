#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#

# This test is SPECIAL. Everything in here, MUST be statically optimized,
# and be a print of a constant, or a function that becomes a return value
# that is constant.

print(not bool)
print(not {})
print(not 7)
print(bool or len)
print(False or dict)
print(type(Ellipsis))
print("a" in "abba")
print("a" not in "abba")
print(len("a"*10000))
print(len(10000*"a"))
print(len((1,) *20000))
print(len(20000*(1,)))
print(len([1]*30000))
print(len(30000*[1]))
print(len(unicode("a")*40000))
print(len(40000*unicode("a")))


# For operations, we use function return values of local variables that will
# have to become constant.
def simpleAssignment():
    x = 2
    return x

def inplaceOperationIncrement():
    x = 2
    x += 1
    return x

def inplaceOperationProduct():
    x = 2
    x *= 2
    return x

def inplaceOperationExponentiate():
    x = 2
    x **= 2
    return x

def inplaceOperationDecrement():
    x = 2
    x -= 8
    return x

#     x //= 5
def inplaceOperationFloorDivison():
    x = 2
    x //= 5
    return x

def inplaceOperationModulus():
    x = 2
    x %= 3
    return x

def inplaceOperationAnd():
    x = 2
    x &= 2
    return x

def inplaceOperationOr():
    x = 2
    x |= 5
    return x

def inplaceOperationXor():
    x = 2
    x ^= 1
    return x

def inplaceOperationDivison():
    x = 2
    x /= 2
    return x

