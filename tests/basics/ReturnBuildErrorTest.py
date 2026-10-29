#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Returning a list, tuple or dict being built, where building it raises."""

from __future__ import print_function


def raiser(value):
    raise KeyError(value)


def returnList(value):
    return [value, raiser(value)]


def returnTuple(value):
    return (value, raiser(value))


def returnDict(value):
    return {1: value, 2: raiser(value)}


def returnDictKey(value):
    return {value: 1, raiser(value): 2}


def returnListTryFinally(value):
    try:
        return [value, raiser(value)]
    finally:
        print("finally", value)


def returnTupleTryExcept(value):
    try:
        return (value, raiser(value))
    except IndexError:
        return None


def returnListLoop(value):
    for _i in range(3):
        return [value, raiser(value)]


def returnListWhile(value):
    while True:
        return [value, raiser(value)]


def returnListWith(value):
    class Manager(object):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            print("exit", args[0].__name__)

    with Manager():
        return [value, raiser(value)]


def lambdaList(value):
    return (lambda: [value, raiser(value)])()


def nestedList(value):
    return [[value], [value, raiser(value)]]


for func in (
    returnList,
    returnTuple,
    returnDict,
    returnDictKey,
    returnListTryFinally,
    returnTupleTryExcept,
    returnListLoop,
    returnListWhile,
    returnListWith,
    lambdaList,
    nestedList,
):
    for count in range(3):
        try:
            func(count)
        except KeyError as e:
            print(func.__name__, "KeyError", e)

print("done")

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
