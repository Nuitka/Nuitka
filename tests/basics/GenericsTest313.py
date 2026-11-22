#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Generic tests for Python 3.13+ type parameter defaults and error paths."""

from typing import Callable, NoDefault

print("Generic class with defaulted TypeVar after TypeVarTuple:")

try:

    class InvalidDefaultAfterTypeVarTuple[*Ts, T = int]:
        pass

    print("unexpectedly created:", InvalidDefaultAfterTypeVarTuple)
except Exception as e:
    print("caught:", type(e).__name__, e)


print("Generic class with valid TypeVar default:")


class ValidTypeVarDefault[T = int]:
    pass


print(
    "valid:",
    ValidTypeVarDefault.__type_params__,
    ValidTypeVarDefault.__type_params__[0].__default__,
)

print("Testing TypeVar, TypeVarTuple, and ParamSpec defaults (PEP 696):")


def makeTracker(label, value):
    events.append(label)
    return value


events = []


class LazyDefaultsClass[
    T = makeTracker("class_T", int),
    U = None,
    V: (int, str) = makeTracker("class_V", str),
    *Ts = *makeTracker("class_Ts", tuple[int, str]),
]:
    pass


class LazyParamSpecClass[
    T = makeTracker("ps_T", float),
    **P = [makeTracker("ps_P", int), str],
]:
    pass


def lazyDefaultsFunc[
    T: int = makeTracker("func_T", bool),
    **P = [makeTracker("func_P", str)],
    *Ts = *makeTracker("func_Ts", tuple[bytes, ...]),
](
    x: T,
) -> T:
    return x


type LazyDefaultsAlias[
    T = makeTracker("alias_T", int),
    **P = ...,
    *Ts = *makeTracker("alias_Ts", tuple[int, ...]),
] = tuple[T, Callable[P, None], *Ts]


print("events after definitions (must be empty):", events)

for label, obj in (
    ("LazyDefaultsClass", LazyDefaultsClass),
    ("LazyParamSpecClass", LazyParamSpecClass),
    ("lazyDefaultsFunc", lazyDefaultsFunc),
    ("LazyDefaultsAlias", LazyDefaultsAlias),
):
    for tp in obj.__type_params__:
        print(label, type(tp).__name__, tp, "has_default:", tp.has_default())
        print("  __default__:", repr(tp.__default__))

print("events after accessing __default__:", events)


class NoDefaultsClass[T, *Ts]:
    pass


class NoDefaultParamSpecClass[**P]:
    pass


for tp in NoDefaultsClass.__type_params__ + NoDefaultParamSpecClass.__type_params__:
    print(
        "no default:",
        type(tp).__name__,
        tp,
        tp.has_default(),
        tp.__default__ is NoDefault,
    )


print("Testing forward references in defaults:")


class ForwardRefDefaults[
    T = DefinedLaterA,
    *Ts = *tuple[DefinedLaterA, DefinedLaterB],
]:
    pass


class ForwardRefParamSpec[**P = [DefinedLaterA, DefinedLaterB]]:
    pass


class DefinedLaterA:
    pass


class DefinedLaterB:
    pass


print(
    "ForwardRefDefaults:",
    ForwardRefDefaults.__type_params__[0].__default__,
    ForwardRefDefaults.__type_params__[1].__default__,
)
print(
    "ForwardRefParamSpec:",
    ForwardRefParamSpec.__type_params__[0].__default__,
)


print("Testing undefined names in defaults (lazy NameError):")


type UndefinedDefaults[
    T = NeverDefinedT,
    **P = [NeverDefinedP],
    *Ts = *tuple[NeverDefinedTs],
] = tuple[T, *Ts]


for tp in UndefinedDefaults.__type_params__:
    try:
        _ = tp.__default__
        print("unexpectedly resolved:", tp)
    except Exception as e:
        print("lazy NameError:", type(tp).__name__, type(e).__name__, e)


print("Testing TypeVarTuple non-starred and invalid starred defaults:")


class NonStarredTupleDefault[*Ts = int]:
    pass


class TooManyStarredTupleDefault[*Ts = *(1, 2)]:
    pass


class EmptyStarredTupleDefault[*Ts = *()]:
    pass


class NonIterableStarredTupleDefault[*Ts = *42]:
    pass


print("NonStarredTupleDefault:", NonStarredTupleDefault.__type_params__[0].__default__)

for label, cls in (
    ("too_many", TooManyStarredTupleDefault),
    ("empty", EmptyStarredTupleDefault),
    ("non_iterable", NonIterableStarredTupleDefault),
):
    try:
        _ = cls.__type_params__[0].__default__
        print("unexpectedly resolved:", label)
    except Exception as e:
        print("starred error:", label, type(e).__name__, e)


print("Testing inter-parameter default reference and generic specialization:")


class DependentDefault[T, U = list[T]]:
    pass


print(
    "DependentDefault:",
    DependentDefault.__type_params__[1].__default__,
    DependentDefault.__type_params__[1].__default__.__args__[0]
    is DependentDefault.__type_params__[0],
    DependentDefault[int],
)


class ClassNamespaceDefault:
    LocalType = str

    type Alias[T = LocalType, *Ts = *tuple[LocalType, ...]] = tuple[T, *Ts]
    type ParamAlias[**P = [LocalType]] = Callable[P, LocalType]


print(
    "ClassNamespaceDefault:",
    ClassNamespaceDefault.Alias.__type_params__[0].__default__,
    ClassNamespaceDefault.Alias.__type_params__[1].__default__,
    ClassNamespaceDefault.ParamAlias.__type_params__[0].__default__,
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
