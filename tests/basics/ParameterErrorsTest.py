#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

import sys


def functionNoParameters():
    pass


print("Call a function with no parameters with a plain argument:")

try:
    functionNoParameters(1)
except TypeError as e:
    print(repr(e))

print("Call a function with no parameters with a keyword argument:")

try:
    functionNoParameters(z=1)
except TypeError as e:
    print(repr(e))


def functionOneParameter(a):
    print(a)


print("Call a function with one parameter with two plain arguments:")

try:
    functionOneParameter(1, 1)
except TypeError as e:
    print(repr(e))

print("Call a function with one parameter too many, and duplicate arguments:")
try:
    functionOneParameter(6, a=4, *(1, 2, 3))
except TypeError as e:
    print(repr(e))

print("Call a function with two parameters with three plain arguments:")


def functionTwoParameters(a, b):
    print(a, b)


try:
    functionTwoParameters(1, 2, 3)
except TypeError as e:
    print(repr(e))

print("Call a function with two parameters with one plain argument:")

try:
    functionTwoParameters(1)
except TypeError as e:
    print(repr(e))

print("Call a function with two parameters with three plain arguments:")

try:
    functionTwoParameters(1, 2, 3)
except TypeError as e:
    print(repr(e))


print("Call a function with two parameters with one keyword argument:")

try:
    functionTwoParameters(a=1)
except TypeError as e:
    print(repr(e))

print("Call a function with two parameters with three keyword arguments:")

try:
    functionTwoParameters(a=1, b=2, c=3)
except TypeError as e:
    print(repr(e))


class MethodContainer:
    def methodNoParameters(self):
        pass

    def methodOneParameter(self, a):
        print(a)

    def methodTwoParameters(self, a, b):
        print(a, b)


obj = MethodContainer()

print("Call a method with no parameters with a plain argument:")

try:
    obj.methodNoParameters(1)
except TypeError as e:
    print(repr(e))

print("Call a method with no parameters with a keyword argument:")

try:
    obj.methodNoParameters(z=1)
except TypeError as e:
    print(repr(e))

print("Call a method with one parameter with two plain arguments:")

try:
    obj.methodOneParameter(1, 1)
except TypeError as e:
    print(repr(e))

print("Call a method with two parameters with three plain arguments:")

try:
    obj.methodTwoParameters(1, 2, 3)
except TypeError as e:
    print(repr(e))

print("Call a method with two parameters with one plain argument:")

try:
    obj.methodTwoParameters(1)
except TypeError as e:
    print(repr(e))

print("Call a method with two parameters with one keyword argument:")

try:
    obj.methodTwoParameters(a=1)
except TypeError as e:
    print(repr(e))

print("Call a method with two parameters with three keyword arguments:")

try:
    obj.methodTwoParameters(a=1, b=2, c=3)
except TypeError as e:
    print(repr(e))


def functionPosBothStarArgs(a, b, c, *l, **d):
    print(a, b, c, l, d)


l = [2]
d = {"other": 7}

print("Call a function with both star arguments and too little arguments:")

try:
    functionPosBothStarArgs(1, *l, **d)
except TypeError as e:
    print(repr(e))

print("Call a function with defaults with too little arguments:")


def functionWithDefaults(a, b, c, d=3):
    print(a, b, c, d)


try:
    functionWithDefaults(1)
except TypeError as e:
    print(repr(e))

print("Call a function with defaults with too many arguments:")

try:
    functionWithDefaults(1)
except TypeError as e:
    print(repr(e))

print("Complex calls with both invalid star list and star arguments:")

try:
    a = 1
    b = 2.0

    functionWithDefaults(1, c=3, *a, **b)
except TypeError as e:
    # Workaround Python 3.9 shortcoming
    print(repr(e).replace("Value", "__main__.functionWithDefaults() argument"))

try:
    a = 1
    b = 2.0

    functionWithDefaults(1, *a, **b)
except TypeError as e:
    # Workaround Python 3.9 shortcoming
    print(repr(e).replace("Value", "__main__.functionWithDefaults() argument"))

try:
    a = 1
    b = 2.0

    functionWithDefaults(c=1, *a, **b)
except TypeError as e:
    print(repr(e))

try:
    a = 1
    b = 2.0

    functionWithDefaults(*a, **b)
except TypeError as e:
    print(repr(e))

print("Complex call with both invalid star list argument:")

try:
    a = 1

    functionWithDefaults(*a)
except TypeError as e:
    print(repr(e))


try:
    a = 1

    MethodContainer(*a)
except TypeError as e:
    print(repr(e))


try:
    a = 1

    MethodContainer()(*a)
except TypeError as e:
    print(repr(e))

try:
    a = 1

    MethodContainer.methodTwoParameters(*a)
except TypeError as e:
    print(repr(e))

try:
    a = 1

    None(*a)
except TypeError as e:
    print(repr(e))


try:
    a = 1

    None(**a)
except TypeError as e:
    print(repr(e))

print("Call object with name as both keyword and in star dict argument:")
try:
    a = {"a": 3}

    None(a=2, **a)
except TypeError as e:
    print(repr(e))

print("Call function with only defaulted value given as keyword argument:")


def functionwithTwoArgsOneDefaulted(a, b=5):
    pass


try:
    functionwithTwoArgsOneDefaulted(b=12)
except TypeError as e:
    print(repr(e))


print("Call built-in methods with keyword arguments:")


def checkBuiltinMethodCall(description, func):
    try:
        result = func()
    except (AttributeError, TypeError) as e:
        print("%s: %s: %s" % (description, type(e).__name__, e))
    else:
        print("%s -> %r" % (description, result))


def checkBuiltinMethodRejected(description, func):
    # Only the exception type, method names in messages are not exact.
    try:
        func()
    except TypeError:
        print("%s: TypeError" % description)


checkBuiltinMethodCall("dict.get key=", lambda: {"a": 1}.get(key="a"))
checkBuiltinMethodCall("dict.get default=", lambda: {"a": 1}.get("z", default=3))
checkBuiltinMethodCall("dict.pop key=", lambda: {"a": 1}.pop(key="a"))
checkBuiltinMethodCall("dict.pop default=", lambda: {"a": 1}.pop("z", default=3))
checkBuiltinMethodCall("dict.setdefault key=", lambda: {"a": 1}.setdefault(key="b"))
checkBuiltinMethodCall("dict.fromkeys iterable=", lambda: dict.fromkeys(iterable="ab"))
checkBuiltinMethodCall("dict.fromkeys positional", lambda: dict.fromkeys("ab", 1))
checkBuiltinMethodCall("dict.has_key key=", lambda: {"a": 1}.has_key(key="a"))
checkBuiltinMethodCall("dict.has_key positional", lambda: {"a": 1}.has_key("a"))

checkBuiltinMethodCall("str.replace count=", lambda: "aaa".replace("a", "x", count=1))
checkBuiltinMethodRejected("str.replace old=", lambda: "aaa".replace(old="a", new="x"))
checkBuiltinMethodCall("str.replace positional", lambda: "aaa".replace("a", "x", 2))

checkBuiltinMethodCall(
    "bytes.translate delete=", lambda: b"abc".translate(None, delete=b"a")
)
checkBuiltinMethodRejected(
    "bytes.translate table=", lambda: b"abc".translate(table=None)
)

if sys.version_info[0] < 3:
    # Python2 "str.translate" has an optional second "deletechars" argument,
    # which the specialized node does not support yet.
    checkBuiltinMethodCall("bytes.translate positional", lambda: b"abc".translate(None))
else:
    checkBuiltinMethodCall(
        "bytes.translate positional", lambda: b"abc".translate(None, b"b")
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
