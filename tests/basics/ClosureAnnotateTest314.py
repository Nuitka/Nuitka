#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Python 3.14 deferred annotations that use closure variables."""

import annotationlib
import typing


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


def makeTypeParameterClassAnnotation():
    class Inner[T]:
        value: T

        def method(self, item: T) -> T:
            return item

    return Inner


def makeTypeParameterFunctionAnnotation():
    def inner[T](item: T) -> T:
        return item

    return inner


def makeShadowedParameterAnnotation():
    format = int

    def inner(x: format) -> format:
        return x

    return inner


def makeSharedCellAnnotation():
    Alias = int

    def annotate_user(x: Alias) -> Alias:
        return x

    def compiled_user():
        return Alias

    # Rebinding must be visible to both, they share the cell.
    Alias = str

    return annotate_user, compiled_user


def makeTypeParameterNamedTuple():
    class Inner[T]:
        class NT(typing.NamedTuple):
            value: T

    return Inner


def makeClosureNamedTuple():
    Alias = int

    class NT(typing.NamedTuple):
        value: Alias

    return NT


print("Function closure:", displayDict(makeFunctionAnnotation().__annotations__))
print("Class closure:", displayDict(makeClassAnnotation().__annotations__))
print("Method closure:", displayDict(makeMethodAnnotation().method.__annotations__))
print("Module level:", displayDict(makeModuleLevelAnnotation().__annotations__))

type_parameter_class = makeTypeParameterClassAnnotation()
type_parameter_function = makeTypeParameterFunctionAnnotation()

print("Type parameter class:", displayDict(type_parameter_class.__annotations__))
print(
    "Type parameter method:",
    displayDict(type_parameter_class.method.__annotations__),
)
print(
    "Type parameter function:",
    displayDict(type_parameter_function.__annotations__),
)
print(
    "Shadowed parameter:",
    displayDict(makeShadowedParameterAnnotation().__annotations__),
)

shared_annotate_user, shared_compiled_user = makeSharedCellAnnotation()

print("Shared cell compiled:", shared_compiled_user())
print(
    "Shared cell forwardref:",
    displayDict(
        annotationlib.call_annotate_function(
            shared_annotate_user.__annotate__,
            annotationlib.Format.FORWARDREF,
        )
    ),
)

type_parameter_named_tuple = makeTypeParameterNamedTuple()
closure_named_tuple = makeClosureNamedTuple()

print(
    "Type parameter NamedTuple:",
    displayDict(type_parameter_named_tuple.NT.__annotations__),
)
print(
    "Closure NamedTuple:",
    displayDict(closure_named_tuple.__annotations__),
)

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
