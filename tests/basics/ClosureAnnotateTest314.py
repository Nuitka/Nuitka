#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Python 3.14 deferred annotations that use closure variables."""


def displayDict(d):
    result = "{"
    first = True
    for key, value in sorted(d.items()):
        if not first:
            result += ","

        result += "%s: %s" % (repr(key), repr(value))
        first = False
    result += "}"

    return result


ModuleLevel = int


def makeFunctionAnnotation():
    Alias = int

    def inner(x: Alias) -> Alias:
        return x

    return inner


def makeClassAnnotation():
    Alias = str

    class Inner:
        y: Alias

    return Inner


def makeMethodAnnotation():
    Alias = float

    class Inner:
        def method(self, z: Alias) -> Alias:
            return z

    return Inner


def makeModuleLevelAnnotation():
    def inner(x: ModuleLevel) -> ModuleLevel:
        return x

    return inner


print("Function closure:", displayDict(makeFunctionAnnotation().__annotations__))
print("Class closure:", displayDict(makeClassAnnotation().__annotations__))
print("Method closure:", displayDict(makeMethodAnnotation().method.__annotations__))
print("Module level:", displayDict(makeModuleLevelAnnotation().__annotations__))

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
