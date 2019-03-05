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

print(not bool)
print(not {})
print(not 7)
print(bool or len)
print(False or dict)
print(type(Ellipsis))
print("a" in "abba")
print("a" not in "abba")

# Added support for functions

x=100

#     x = 2
def assignment(x):
  x = 2
  return x
print(assignment(x))

#     x += 1
def selfIncrement(x):
  x += 1
  return x
print(selfIncrement(x))

#     x *= 2
def selfProduct(x):
  x *= 2
  return x
print(selfProduct(x))

#     x **= 2
def selfExponentiate(x):
  x **= 2
  return x
print(selfExponentiate(x))

#     x -= 8
def selfDecrement(x):
  x -= 8
  return x
print(selfDecrement(x))

#     x //= 5
def selfFloorDivison(x):
  x //= 5
  return x
print(selfFloorDivison(x))

#     x %= 3
def selfModulus(x):
  x %= 3
  return x
print(selfModulus(x))

#     x &= 2
def selfAnd(x):
  x &= 2
  return x
print(selfAnd(x))

#     x |= 5
def selfOr(x):
  x |= 5
  return x
print(selfOr(x))

#     x ^= 1
def selfXor(x):
  x ^= 1
  return x
print(selfXor(x))

#     x /= 2
def selfDivison(x):
  x /= 2
  return x
print(selfDivison(x))

print(len("a"*10000))
print(len(10000*"a"))
print(len((1,) *20000))
print(len(20000*(1,)))
print(len([1]*30000))
print(len(30000*[1]))
print(len(unicode("a")*40000))
print(len(40000*unicode("a")))
