#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Keyword argument handling of built-in methods called on constant values."""

from __future__ import print_function


def check(description, func):
    try:
        result = func()
    except TypeError as e:
        print(description, "TypeError:", e)
    else:
        print(description, "->", repr(result))


def checkRejected(description, func):
    # Only the exception type, method names in messages are not exact.
    try:
        func()
    except TypeError:
        print(description, "TypeError")


check("dict.get key=", lambda: {"a": 1}.get(key="a"))
check("dict.get default=", lambda: {"a": 1}.get("z", default=3))
check("dict.pop key=", lambda: {"a": 1}.pop(key="a"))
check("dict.pop default=", lambda: {"a": 1}.pop("z", default=3))
check("dict.setdefault key=", lambda: {"a": 1}.setdefault(key="b"))
check("dict.fromkeys iterable=", lambda: dict.fromkeys(iterable="ab"))
check("dict.fromkeys positional", lambda: dict.fromkeys("ab", 1))

check("str.replace count=", lambda: "aaa".replace("a", "x", count=1))
checkRejected("str.replace old=", lambda: "aaa".replace(old="a", new="x"))
check("str.replace positional", lambda: "aaa".replace("a", "x", 2))

check("bytes.translate delete=", lambda: b"abc".translate(None, delete=b"a"))
checkRejected("bytes.translate table=", lambda: b"abc".translate(table=None))
check("bytes.translate positional", lambda: b"abc".translate(None, b"b"))

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
