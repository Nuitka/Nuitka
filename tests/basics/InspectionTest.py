#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""Tests uncompiled functions and compiled functions responses to inspect and isistance.  """

from __future__ import print_function

import inspect
import pprint
import sys
import types


def displayDict(d, remove_keys=()):
    if "__loader__" in d:
        d = dict(d)
        if str is bytes:
            del d["__loader__"]
        else:
            d["__loader__"] = "<__loader__ removed>"

    if "__file__" in d:
        d = dict(d)
        d["__file__"] = "<__file__ removed>"

    if "__compiled__" in d:
        d = dict(d)
        del d["__compiled__"]

    for remove_key in remove_keys:
        if remove_key in d:
            d = dict(d)
            del d[remove_key]

    return pprint.pformat(d)


def compiledFunction(a, b):
    pass


print("Function inspect.isfunction:", inspect.isfunction(compiledFunction))
print(
    "Function isinstance types.FunctionType:",
    isinstance(compiledFunction, types.FunctionType),
)
print(
    "Function isinstance tuple containing types.FunctionType:",
    isinstance(compiledFunction, (int, types.FunctionType)),
)


# Even this works.
assert type(compiledFunction) == types.FunctionType


class CompiledClass:
    def __init__(self):
        pass

    def compiledMethod(self):
        pass


assert inspect.isfunction(CompiledClass) is False
assert isinstance(CompiledClass, types.FunctionType) is False

assert inspect.ismethod(compiledFunction) is False
assert inspect.ismethod(CompiledClass) is False

assert inspect.ismethod(CompiledClass.compiledMethod) == (sys.version_info < (3,))
assert inspect.ismethod(CompiledClass().compiledMethod) is True

assert bool(type(CompiledClass.compiledMethod) == types.MethodType) == (
    sys.version_info < (3,)
)


def compiledGenerator():
    yield 1


assert inspect.isfunction(compiledGenerator) is True
assert inspect.isgeneratorfunction(compiledGenerator) is True

assert isinstance(compiledGenerator(), types.GeneratorType) is True
assert type(compiledGenerator()) == types.GeneratorType
assert isinstance(compiledGenerator, types.GeneratorType) is False

assert inspect.ismethod(compiledGenerator()) is False
assert inspect.isfunction(compiledGenerator()) is False

assert inspect.isgenerator(compiledFunction) is False
assert inspect.isgenerator(compiledGenerator) is False
assert inspect.isgenerator(compiledGenerator()) is True


def someFunction(a):
    assert inspect.isframe(sys._getframe())
    # print("Running frame getframeinfo()", inspect.getframeinfo(sys._getframe()))

    # TODO: The locals of the frame are not updated.
    # print("Running frame arg values", inspect.getargvalues(sys._getframe()))


someFunction(2)


class C:
    print(
        "Class locals",
        displayDict(
            sys._getframe().f_locals, remove_keys=("__qualname__", "__locals__")
        ),
    )
    print("Class flags", sys._getframe().f_code.co_flags)


def f():
    print("Func locals", sys._getframe().f_locals)
    print("Func flags", sys._getframe().f_code.co_flags)


f()


def g():
    yield ("Generator object locals", sys._getframe().f_locals)
    yield ("Generator object flags", sys._getframe().f_code.co_flags)


for line in g():
    print(*line)

print("Generator function flags", g.__code__.co_flags)

print("Module frame locals", displayDict(sys._getframe().f_locals))
print("Module flags", sys._getframe().f_code.co_flags)
print("Module code name", sys._getframe().f_code.co_name)

print("Module frame dir", dir(sys._getframe()))
