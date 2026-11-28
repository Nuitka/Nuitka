#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function


def setOrderCheck():
    print("Checking order of set literals:")

    def one():
        print("one")
        return "one"

    def two():
        print("two")
        return "two"

    return {one(), two()}


def raiseOrderCheck():
    print("Checking order of raises:")

    def exception_type():
        print("exception_type", end="")

        return ValueError

    def exception_value():
        print("exception_value", end="")

        return 1

    def exception_tb():
        print("exception_value", end="")

        return None

    print("1 args", end="")
    try:
        raise exception_type()
    except Exception as e:
        print("caught", repr(e))


setOrderCheck()
raiseOrderCheck()


def setTruthHashingSideEffects():
    events = []

    class CustomHashKey(object):
        def __init__(self, tag):
            self.tag = tag

        def __hash__(self):
            events.append(("hash", self.tag))
            return 42

        def __eq__(self, other):
            events.append(("eq", self.tag, other.tag))
            return False

    def notSet(value):
        return not {value}

    def boolSet(value):
        return bool({value})

    def ifSet(value):
        if {value}:
            return "truthy"
        return "falsy"

    def dropSet(value):
        {value}  # pylint: disable=pointless-statement

    def notSetPair(k1, k2):
        return not {k1, k2}

    for name, fn in (
        ("notSet", notSet),
        ("boolSet", boolSet),
        ("ifSet", ifSet),
        ("dropSet", dropSet),
    ):
        try:
            fn([])
        except TypeError:
            print(name, "unhashable raised TypeError")

    del events[:]
    print("notSet custom:", notSet(CustomHashKey("s1")), events)
    del events[:]
    print("boolSet custom:", boolSet(CustomHashKey("s2")), events)
    del events[:]
    print("ifSet custom:", ifSet(CustomHashKey("s3")), events)
    del events[:]
    dropSet(CustomHashKey("s4"))
    print("dropSet custom:", events)
    del events[:]
    print(
        "notSetPair custom:",
        notSetPair(CustomHashKey("sp1"), CustomHashKey("sp2")),
        events,
    )


setTruthHashingSideEffects()

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
