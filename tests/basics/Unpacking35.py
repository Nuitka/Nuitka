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

def tupleUnpacking():
    return (*a, b, *c)

def listUnpacking():
    return [*a, b, *c]

def setUnpacking():
    return {*a, b, *c}

def dictUnpacking():
    return {"a" : 1, **d}

a = range(3)
b = 5
c = range(8,10)
d = {"a" : 2}

print("Tuple unpacked", tupleUnpacking())
print("List unpacked", listUnpacking())
print("Set unpacked", setUnpacking())
print("Dict unpacked", dictUnpacking())


non_iterable = 2.0

def tupleUnpackingError():
    try:
        return (*a,*non_iterable,*c)
    except Exception as e:
        return e

def listUnpackingError():
    try:
        return [*a,*non_iterable,*c]
    except Exception as e:
        return e

def setUnpackingError():
    try:
        return {*a,*non_iterable,*c}
    except Exception as e:
        return e

def dictUnpackingError():
    try:
        return {"a" : 1, **non_iterable}
    except Exception as e:
        return e


print("Tuple unpacked error:", tupleUnpackingError())
print("List unpacked error:", listUnpackingError())
print("Set unpacked error:", setUnpackingError())
print("Dict unpacked error:", dictUnpackingError())
