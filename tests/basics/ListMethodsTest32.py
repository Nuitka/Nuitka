#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""List methods 'insert' and 'index' with bad and extreme index values."""

from __future__ import print_function

import sys


class BadIndex(object):
    def __index__(self):
        raise ValueError("bad index")


def check(description, func, *args):
    try:
        result = func(*args)
    except Exception as e:  # pylint: disable=broad-except
        result = "%s: %s" % (type(e).__name__, e)
    print(description, "->", result)


def insertFloatConstant():
    a = [1, 2]
    a.insert(1.5, "x")
    return a


def insertVariable(index):
    a = [1, 2]
    a.insert(index, "x")
    return a


def indexStart(values, start):
    a = list(values)
    return a.index(2, start)


def indexStartStop(values, start, stop):
    a = list(values)
    return a.index(2, start, stop)


def insertBadIndex():
    a = [1, 2]
    a.insert(BadIndex(), "x")
    return a


def indexBadStart(values):
    a = list(values)
    return a.index(2, BadIndex())


def indexBadStopValue(values):
    a = list(values)
    return a.index(2, 0, BadIndex())


def indexBadStop(values, start, stop):
    a = list(values)
    for _i in range(3):
        try:
            a.index(2, start, stop)
        except TypeError:
            pass
    return sys.getrefcount(start) > 0


# Values not known at compile time.
big = int(str(len(sys.argv)) + "0" * 20)

check("insert(1.5) constant", insertFloatConstant)
check("insert(None)", insertVariable, None)
check("insert(1.5)", insertVariable, 1.5)
check("insert(-big)", insertVariable, -big)
check("index(2, big)", indexStart, [1, 2], big)
check("index(2, -big)", indexStart, [1, 2], -big)
check("index(2, -big, big)", indexStartStop, [1, 2], -big, big)
check("index(2, 0, None)", indexStartStop, [1, 2], 0, None)
check("insert bad __index__", insertBadIndex)
check("index bad __index__ start", indexBadStart, [1, 2])
check("index bad __index__ stop", indexBadStopValue, [1, 2])
check("index bad stop", indexBadStop, [1, 2], big, None)

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
