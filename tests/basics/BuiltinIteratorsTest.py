#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Calls of iterator related built-ins, with values known and unknown at compile time."""

from __future__ import print_function

import sys


class BadBool(object):
    def __bool__(self):
        raise ValueError("no truth value")

    __nonzero__ = __bool__


def enumerateConstant():
    return enumerate("ab")


def enumerateConstantStart():
    return enumerate("ab", 2)


def enumerateBadStart():
    return enumerate("ab", b"x")


def zipEmpty():
    return zip()


def zipConstants():
    return zip("ab", (1, 2))


def zipStrictBadBool(value):
    return zip("ab", strict=value)


def nextNotIterator(value):
    return next(value, "default")


def nextIterator(value):
    return next(iter(value), "default")


def check(description, func, *args):
    try:
        result = func(*args)
        if not isinstance(result, str):
            result = list(result)
    except Exception as e:  # pylint: disable=broad-except
        result = type(e).__name__
    print(description, result)


check("enumerate constant", enumerateConstant)
check("enumerate constant start", enumerateConstantStart)
check("enumerate bad start", enumerateBadStart)
check("zip empty", zipEmpty)
check("zip constants", zipConstants)
if sys.version_info >= (3, 10):
    check("zip strict bad bool", zipStrictBadBool, BadBool())
check("next of int with default", nextNotIterator, int("5"))
check("next of list with default", nextNotIterator, list("ab"))
check("next of empty iterator with default", nextIterator, ())

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
