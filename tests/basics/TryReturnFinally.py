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

# In this test we show that return in try/finally executes the finally part
# just fine.

from __future__ import print_function

import sys

def eight():
    return 8

def nine():
    return 9

def raisy1():
    return 1 / 0

def raisy2():
    return 1()

def raisy3(arg):
    raise TypeError(arg)

def returnInTried(for_call):
    try:
        print("returnInTried with exception info in tried block:", sys.exc_info())

        return for_call()
    finally:
        print("returnInTried with exception info in final block:", sys.exc_info())

def returnInFinally(for_call):
    try:
        print("returnInFinally with exception info in tried block:", sys.exc_info())
    finally:
        print("returnInFinally with exception info in final block:", sys.exc_info())

        return for_call()

print("Standard try finally with return in tried block:")
print("result", returnInTried(eight))

print('*' * 80)

print("Standard try finally with return in final block:")
print("result", returnInFinally(nine))

print('*' * 80)

print("Exception raising try finally with return in tried block:")
try:
    print("result", returnInTried(raisy1))
except Exception as e:
    print("Gave exception", repr(e))

print('*' * 80)

print("Exception raising try finally with return in final block:")
try:
    print("result", returnInFinally(raisy2))
except Exception as e:
    print("Gave exception", repr(e))

print('*' * 80)

try:
    raisy3("unreal 1")
except Exception as outer_e:
    print("Exception raising try finally with return in tried block:")
    try:
        print("result", returnInTried(raisy1))
    except Exception as e:
        print("Gave exception", repr(e))

    print("Handler exception remains:", repr(outer_e))

print('*' * 80)

try:
    raisy3("unreal 2")
except Exception as outer_e:
    print("Exception raising try finally with return in final block:")
    try:
        print("result", returnInFinally(raisy2))
    except Exception as e:
        print("Gave exception", repr(e))

    print("Handler exception remains:", repr(outer_e))

print('*' * 80)
