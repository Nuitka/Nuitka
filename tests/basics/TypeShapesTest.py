#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Operations where type shape knowledge must match what CPython does."""

from __future__ import print_function

import sys


def bytesAddBytearray(value):
    b = value.encode("ascii")
    r = b + bytearray(value, "ascii")

    print("bytes + bytearray type:", type(r))

    try:
        r.append(65)
    except AttributeError as e:
        print("bytes + bytearray append:", repr(e))
    else:
        print("bytes + bytearray append worked:", r)


def typeLessThanType(left, right):
    try:
        type(left) < type(right)
    except TypeError as e:
        print("type < type:", repr(e))
    else:
        print("type < type: no exception")


def typeLessThanTypeValue(left, right):
    try:
        result = type(left) < type(right)
    except TypeError as e:
        print("type < type value:", repr(e))
    else:
        print("type < type value:", result)


class OrderedMeta(type):
    def __lt__(cls, other):
        return cls.__name__ < other.__name__


class OrderedA(OrderedMeta("OrderedBase", (object,), {})):
    pass


class OrderedB(OrderedMeta("OrderedBase", (object,), {})):
    pass


def numberFromBytearray(value):
    ba = bytearray(value, "ascii")

    print("int(bytearray):", int(ba))
    print("float(bytearray):", float(ba))

    if sys.version_info[0] < 3:
        print("long(bytearray):", long(ba))


def noneOrType(value):
    n = None

    try:
        r = n | type(value)
    except TypeError as e:
        print("None | type:", repr(e))
    else:
        print("None | type:", r)


def typeOrNone(value):
    try:
        r = type(value) | None
    except TypeError as e:
        print("type | None:", repr(e))
    else:
        print("type | None:", r)


class NonBoolTruth(object):
    def __bool__(self):
        print("NonBoolTruth truth check")
        return False

    __nonzero__ = __bool__


class NonBoolEq(object):
    def __eq__(self, other):
        print("NonBoolEq equality check")
        return NonBoolTruth()

    def __ne__(self, other):
        print("NonBoolEq inequality check")
        return "inequality"

    __hash__ = None


class WeirdContains(object):
    def __contains__(self, other):
        print("WeirdContains containment check")
        return []


def negationOfComparisons():
    obj = object()

    print("not is:", not (obj is obj), not (obj is None))
    print("not is not:", not (obj is not None), not (obj is not obj))
    print("not in:", not (1 in [1]), not (2 in [1]))
    print("not not in:", not (1 not in [1]), not (2 not in [1]))
    print("not eq:", not (1 == 1), not (1 == 2))
    print("not lt:", not (1 < 2), not (2 < 1))
    print("not chain:", not (1 < 2 < 3), not (1 < 2 > 3))

    print("not non-bool eq:", not (NonBoolEq() == 1))
    print("not weird contains:", not (1 in WeirdContains()))


def loopCompleteAlternativeComparisons(steps):
    it = iter(steps)
    x = 1
    y = None
    results = []
    while True:
        results.append(
            (
                None == x,
                None != x,
                x == None,  # pylint: disable=singleton-comparison
                x != None,  # pylint: disable=singleton-comparison
                not (None == x),  # pylint: disable=unneeded-not
                y == 1,
                y != 1,
                not (y == 1),  # pylint: disable=unneeded-not
                y == x,
                y != x,
            )
        )
        if next(it):
            x = "a"
            y = 1
        else:
            break

    print("loop eq/neq:", results)


def strOrUnicodeOperations(flag, arg):
    s = (b"hello %s" if flag else b"hi %s").decode("ascii")
    formatted = s % arg
    print("decoded mod upper:", formatted.upper())

    s_int = (b"num %d" if flag else b"n=%d").decode("ascii")
    formatted_int = s_int % 42
    print("decoded int mod upper:", formatted_int.upper())

    state = ["before"]

    class SideEffectArg(object):
        def __str__(self):
            state[0] = "after"
            return "val"

        def __unicode__(self):
            state[0] = "after"
            return "val"

    before = state[0]
    formatted_side = s % SideEffectArg()
    print("decoded mod side effect:", before, state[0], formatted_side)

    bad_s = (b"%d" if flag else b"%i").decode("ascii")
    try:
        print("decoded bad mod:", bad_s % "not-an-int")
    except TypeError as e:
        print("decoded bad mod TypeError:", type(e).__name__)

    try:
        print("decoded floordiv:", s // 2)
    except TypeError as e:
        print("decoded floordiv TypeError:", type(e).__name__)

    try:
        print("decoded div:", s / 2)
    except TypeError as e:
        print("decoded div TypeError:", type(e).__name__)

    try:
        print("decoded divmod:", divmod(s, 2))
    except TypeError as e:
        print("decoded divmod TypeError:", type(e).__name__)

    try:
        print("decoded pow:", s**2)
    except TypeError as e:
        print("decoded pow TypeError:", type(e).__name__)


clear_escape_state = "init"


class ClearFinalizer(object):
    def __del__(self):
        global clear_escape_state
        clear_escape_state = "finalized"


def dictClearKnowledgeAndEscape():
    global clear_escape_state

    d = {"a": 1}
    d.clear()
    print("dict.clear membership/truth:", "a" in d, bool(d), len(d))

    clear_escape_state = "before"
    d2 = {"k": ClearFinalizer()}
    before = clear_escape_state
    d2.clear()
    after = clear_escape_state
    print("dict.clear finalizer escape:", before, after, bool(d2))


def inAndFloatTypeErrorShapes(flag):
    x = 1 if flag else 2
    try:
        print("in int:", 1 in x)
    except TypeError as e:
        print("in int TypeError:", repr(e))

    try:
        print("not in int:", 1 not in x)
    except TypeError as e:
        print("not in int TypeError:", repr(e))

    y = 1 if flag else (1 << 100)
    try:
        print("in int_or_long:", 1 in y)
    except TypeError as e:
        print("in int_or_long TypeError:", repr(e))

    events = []

    def leftSideEffect():
        events.append("left")
        return 1

    def rightSideEffect():
        events.append("right")
        return 2

    try:
        print(
            "in side effects:",
            leftSideEffect() in (rightSideEffect() if flag else 3),
        )
    except TypeError as e:
        print("in side effects TypeError:", events, repr(e))

    float_events = []

    def listSideEffect():
        float_events.append("arg")
        return [1]

    try:
        print("float(list):", float(listSideEffect() if flag else [2]))
    except TypeError as e:
        print("float(list) TypeError:", float_events, repr(e))


def dictUnhashableOperations(flag):
    d = {"a": 1}
    k = [1] if flag else [2]

    for label, fn in (
        ("get2", lambda: d.get(k)),
        ("get3", lambda: d.get(k, 9)),
        ("pop3", lambda: d.pop(k, 9)),
    ):
        try:
            fn()
        except TypeError as e:
            print("dict unhashable", label, type(e).__name__)


bytesAddBytearray("12")
typeLessThanType(1, 2)
typeLessThanType(OrderedA(), OrderedB())
typeLessThanTypeValue(1, 2)
typeLessThanTypeValue(OrderedA(), OrderedB())
typeLessThanTypeValue(OrderedB(), OrderedA())
numberFromBytearray("12")
noneOrType(1)
typeOrNone(1)
negationOfComparisons()
loopCompleteAlternativeComparisons((False,))
loopCompleteAlternativeComparisons((True, False))
strOrUnicodeOperations(True, "world")
strOrUnicodeOperations(False, 42)
dictClearKnowledgeAndEscape()
inAndFloatTypeErrorShapes(True)
inAndFloatTypeErrorShapes(False)
dictUnhashableOperations(True)
dictUnhashableOperations(False)

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
