#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
from __future__ import print_function

def local_function(a,z = 9):
    b = `a*a+1`

    c = (a,b,a**32,a+a)

    d = long('0')  # @UnusedVariable
    e = int("77")  # @UnusedVariable

    d = long(b)
    e = long(1+1)

    return a, b, c, d, e, z

print("Call function with many variables calculated and returned", local_function(1,z = 5))

print("Function with nested args:")
def nested_args_function((a,b), c):
    return a, b, c

print(nested_args_function((1, 2), 3))

try:
    nested_args_function((1, 2, 3), 3)
except ValueError, e:
    print("Calling nested with too long tuple gave:", e)

try:
    nested_args_function((1,), 3)
except ValueError, e:
    print("Calling nested with too short tuple gave:", e)

def deeply_nested_function(((a,), b, c,  (d, (e,f)))):
    return a, b, c, d, e, f

print("Deeply nested function", deeply_nested_function(((1,), 2, 3, (4, (5, 6)))))

print("Function with nested args that have defaults:")

def default_giver():
    class R:
        def __iter__(self):
            print("Giving iter")
            return iter(range(2))

    return R()

def nested_args_function_with_defaults((a,b) = default_giver(), c = 5):
    return a, b, c

print("Calling it.")
print(nested_args_function_with_defaults())

def comp_args1((a, b)):
    return a,b

def comp_args2((a, b) = (3, 4)):
    return a, b

def comp_args3(a, (b, c)):
    return a, b, c

def comp_args4(a = 2, (b, c) = (3, 4)):
    return a, b, c

print("Complex args functions", comp_args1((2, 1)), comp_args2(), comp_args2((7,9)), comp_args3(7, (8,9)), comp_args4())
