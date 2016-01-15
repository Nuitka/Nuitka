#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

def decorator1(f):
    print("Executing decorator 1")

    def deco_f():
        return f() + 2

    return deco_f

def decorator2(f):
    print("Executing decorator 2")

    def deco_f():
        return f() * 2

    return deco_f

# Result of function now depends on correct order of applying the decorators
@decorator1
@decorator2
def function1():
    return 3

print(function1())

def deco_returner1():
    print("Executing decorator returner D1")
    return decorator1

def deco_returner2():
    print("Executing decorator returner D2")
    return decorator2

@deco_returner1()
@deco_returner2()
def function2():
    return 3

print(function2())

# Same as function2, but without decorator syntax.
def function3():
    return 3

function3 = deco_returner1()(deco_returner2()(function3))

print(function3())
