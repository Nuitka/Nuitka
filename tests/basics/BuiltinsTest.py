#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
from __future__ import print_function

def someFunctionWritingLocals():
    x = 1
    r = locals()

    # This is without effect on r. It doesn't mention y at all
    y = 2

    # This adds z to the locals, but only that.
    r[ 'z' ] = 3
    del x

    try:
        z
    except Exception as e:
        print("Accessing z writing to locals gives Exception", e)

    return r, y

def someFunctionWritingLocalsContainingExec():
    x = 1
    r = locals()

    # This is without effect on r. It doesn't mention y at all
    y = 2

    # This adds z to the locals, but only that.
    r[ 'z' ] = 3

    try:
        z
    except Exception as e:
        print("Accessing z writing to locals in exec function gives Exception", e)

    return r, y

    # Note: This exec is dead code, and still changes the behaviour of
    # CPython, because it detects exec during parse already.
    exec("")

print("Testing locals():")
print(someFunctionWritingLocals())
print(someFunctionWritingLocalsContainingExec())

def displayDict(d):
    if "__loader__" in d:
        d = dict(d)
        d["__loader__"] = "<__loader__ removed>"

    if "__file__" in d:
        d = dict(d)
        d["__file__"] = "<__file__ removed>"

    import pprint
    return pprint.pformat(d)

print("Vars on module level", displayDict(vars()))

module_locals = locals()

# Patch away "__file__" path in a hard to detect way. This will make sure,
# repeated calls to locals really get the same dictionary.
import os
module_locals["__file__"] = os.path.basename(module_locals[ "__file__" ])
del module_locals

print("Use of locals on the module level", displayDict(locals()))

def someFunctionUsingGlobals():
    g = globals()

    g["hallo"] = "du"

    global hallo
    print("hallo", hallo)


print("Testing globals():")
someFunctionUsingGlobals()

print("Testing dir():")

print("Module dir", end = ' ')

def someFunctionUsingDir():
    x = someFunctionUsingGlobals()

    print("Function dir", dir())

    return x

someFunctionUsingDir()

print("Making a new type, with type() and 3 args:", end = ' ')
new_class = type("Name", (object,), {})
print(new_class, new_class())

print("None has type", type(None))

print("Constant ranges", range(2), range(1, 6), range(3, 0, -1), range(3, 8, 2), range(5, -5, -3))
print("Border cases", range(0), range(-1), range(-1, 1))

print("Corner case large negative value", range(-2**100))
print("Corner case with large start/end values in small range", range(2**100,2**100+2))

try:
    print("Range with 0 step gives:", end = ' ')
    print(range(3, 8, 0))
except ValueError as e:
    print(repr(e))

try:
    print("Range with float:", end = ' ')
    print(range(1.0))
except TypeError as e:
    print("Gives exception:", repr(e))

try:
    print("Empty range call", end = ' ')
    print(range())
except TypeError as e:
    print("Gives exception:", e)

print("List from iterable", list("abc"), list())
try:
    print("List from sequence", end = ' ')
    print(list(sequence = (0, 1, 2)))
except TypeError as e:
    print("Gives exception:", e)
print("Tuple from iterable", tuple("cda"), tuple())
try:
    print("Tuple from sequence", end = ' ')
    print(tuple(sequence = (0, 1, 2)))
except TypeError as e:
    print("Gives exception:", e)

print("Dictionary from iterable and keywords", displayDict(dict(("ab", (1, 2)), f = 1, g = 1)))
print("More constant dictionaries", {"two": 2, "one": 1}, {}, dict())
g = {"two": 2, "one": 1}
print("Variable dictionary", dict(g))
print("Found during optimization", dict(dict({"le": 2, "la": 1}), fu = 3), dict(named = dict({"le": 2, "la": 1})))

print("Floats from constants", float("3.0"), float())
try:
    print("Float keyword arg", end = ' ')
except TypeError as e:
    print(float(x = 9.0))

print("Found during optimization", float(float("3.2")), float(float(11.0)))

print("Complex from constants", complex("3.0j"), complex(real = 9.0), complex(imag = 9.0), complex(1,2), complex())
print("Found during optimization", complex(float("3.2")), complex(real = float(11.0)), complex(imag = float(11.0)))

print("Strs from constants", str("3.3"), str(object = 9.1), str())
print("Found during optimization", str(float("3.3")), str(object = float(12.0)))

print("Bools from constants", bool("3.3"), bool(0), bool())
print("Found during optimization", bool(float("3.3")), bool(range(0)))

print("Ints from constants", int('3'), int('f', 16), int("0101", base = 2), int(0), int())
try:
    print("Int keyword arg1", end = ' ')
    print(int(x = '9'))
    print(int(x = 'e', base = 16))
except TypeError as e:
    print("Gives exception:", e)
print("Found ints during optimization", int(int('3')), int(int(0.0)))

try:
    print("Longs from constants", long('3'), long(x = '9'), long('f', 16), long(x = 'e', base = 16), long("0101", base = 2), long(0), long())
    print("Found longs during optimization", long(long('3')), long(x = long(0.0)))
except NameError:
    print("Python3 has no long type.")
    pass


try:
    print("Int with only base", int(base = 2), end = ' ')
except Exception as e:
    print("Caused", repr(e))
else:
    print("Worked")

try:
    print("Int with large base", int(2, 37), end = ' ')
except Exception as e:
    print("Caused", repr(e))
else:
    print("Worked")

try:
    print("Long with only base", int(base = 2), end = ' ')
except Exception as e:
    print("Caused", repr(e))
else:
    print("Worked")


print("Oct from constants", oct(467), oct(0))
print("Found during optimization", oct(int('3')))

print("Hex from constants", hex(467), hex(0))
print("Found during optimization", hex(int('3')))


print("Bin from constants", bin(467), bin(0))
print("Found during optimization", bin(int('3')))

try:
    int(1,2,3)
except Exception as e:
    print("Too many args gave", repr(e))

try:
    int(y = 1)
except Exception as e:
    print("Wrong arg", repr(e))

f = 3
print("Unoptimized call of int", int('0' * f, base = 16))

try:
    d = { 'x' : "12", "base" : 8 }
    print("Dict star argument call of int", end = ' ')
    print(int(**d))
except TypeError as e:
    print("Gives exception:", e)

base = 16

try:
    value = unicode("20")
except NameError:
    print("Python3: Has unicode by default.")
    value = "20"

print("Unoptimized calls of int with unicode args", int(value, base), int(value))

base = 37
try:
    print("Int with large base", int(2, base), end = ' ')
except Exception as e:
    print("Caused", repr(e))
else:
    print("Worked")


try:
    print(chr())
except Exception as e:
    print("Disallowed without args", repr(e))

try:
    print(ord())
except Exception as e:
    print("Disallowed without args", repr(e))

try:
    print(ord(s = 1))
except Exception as e:
    print("Disallowed keyword args", repr(e))

try:
    print(ord(1, 2))
except Exception as e:
    print("Too many plain args", repr(e))

try:
    print(ord(1, s = 2))
except Exception as e:
    print("Too many args, some keywords", repr(e))

try:
    print(sum())
except Exception as e:
    print("Disallowed without args", repr(e))

x = range(17)
print("Sum of range(17) is", sum(x))
print("Sum of range(17) starting with 5 is", sum(x, 5))

try:
    print(str('1', offer = 2))
except Exception as e:
    print("Too many args, some keywords", repr(e))

# TODO: This is calls, not really builtins.
a = 2

print("Can optimize the star list argness away", int(*(a,)), end = ' ')
print("Can optimize the empty star list arg away", int(*tuple()), end = ' ')
print("Can optimize the empty star dict arg away", int(**dict()))

print("Dict building with keyword arguments", dict(), dict(a = f))
print(
    "Dictionary entirely from constant args",
    displayDict(
        dict(q = "Guido", w = "van", e = "Rossum", r = "invented", t = "Python", y = "")
    )
)

a = 5
print("Instance check recognises", isinstance(a, int))

try:
    print("Instance check with too many arguments", isinstance(a, long, int))
except Exception as e:
    print("Too many args", repr(e))

try:
    print("Instance check with too many arguments", isinstance(a))
except Exception as e:
    print("Too few args", repr(e))

def usingIterToCheckIterable(a):
    try:
        iter(a)
    except TypeError:
        print("not iterable")
    else:
        print("ok")

usingIterToCheckIterable(1)

print("Nested constant, dict inside a list, referencing a built-in compile time constant", end = ' ')
print([dict(type = int)])

print("nan and -nan sign checks:")
from math import copysign
print(copysign(1.0, float("nan")))
print(copysign(1.0, float("-nan")))

print("Using != to detect nan floats:")
a = float("nan")
if a != a:
    print("is nan")
else:
    print("isn't nan")

class CustomStr(str): pass
class CustomBytes(bytes): pass
class CustomByteArray(bytearray): pass

values = [
    b'100',
    b'',
    bytearray(b'100'),
    CustomStr("100"),
    CustomBytes(b'100'),
    CustomByteArray(b'100')
]

for x in values:
    try:
        print("int", repr(x), int(x), int(x,2))
    except (TypeError, ValueError) as e:
        print("caught", repr(e))

    try:
        print("long", repr(x), long(x), long(x,2))
    except (TypeError, ValueError) as e:
        print("caught", repr(e))
    except NameError:
        print("Python3 has no long")


z = range(5)
try:
    next(z)
except TypeError as e:
    print("caught", repr(e))

try:
    open()
except TypeError as e:
    print("Open without arguments gives", repr(e))

print("Type of id values:", type(id(id)))


class OtherBytesSubclass(bytes):
    pass

class BytesOverload:
    def __bytes__(self):
        return OtherBytesSubclass()

b = BytesOverload()
v = bytes(b)

if type(v) is bytes:
    print("Bytes overload ineffective (expected for Python2)")
elif isinstance(v, bytes):
    print("Bytes overload successful.")
else:
    print("Oops, must not happen.")

class OtherFloatSubclass(float):
    pass

class FloatOverload:
    def __float__(self):
        return OtherFloatSubclass()

b = FloatOverload()
v = float(b)

if type(v) is float:
    print("Float overload ineffective (must not happen)")
elif isinstance(v, float):
    print("Float overload successful.")
else:
    print("Oops, must not happen.")

class OtherStrSubclass(str):
    pass

class StrOverload:
    def __str__(self):
        return OtherStrSubclass()

b = StrOverload()
v = str(b)

if type(v) is str:
    print("Str overload ineffective (must not happen)")
elif isinstance(v, str):
    print("Str overload successful.")
else:
    print("Oops, must not happen.")

if str is bytes:
    class OtherUnicodeSubclass(unicode):
        pass

    class UnicodeOverload:
        def __unicode__(self):
            return OtherUnicodeSubclass()

    b = UnicodeOverload()

    v = unicode(b)

    if type(v) is unicode:
        print("Unicode overload ineffective (must not happen)")
    elif isinstance(v, unicode):
        print("Unicode overload successful.")
    else:
        print("Oops, must not happen.")


class OtherIntSubclass(int):
    pass

class IntOverload:
    def __int__(self):
        return OtherIntSubclass()

b = IntOverload()
v = int(b)

if type(v) is int:
    print("Int overload ineffective (must not happen)")
elif isinstance(v, int):
    print("Int overload successful.")
else:
    print("Oops, must not happen.")


if str is bytes:
    class OtherLongSubclass(long):
        pass

    class LongOverload:
        def __long__(self):
            return OtherLongSubclass()

    b = LongOverload()
    v = long(b)

    if type(v) is long:
        print("Long overload ineffective (must not happen)")
    elif isinstance(v, long):
        print("Long overload successful.")
    else:
        print("Oops, must not happen.")


class OtherComplexSubclass(complex):
    pass

class ComplexOverload:
    def __complex__(self):
        return OtherComplexSubclass()

b = ComplexOverload()
v = complex(b)

if type(v) is complex:
    print("Complex overload ineffective (must happen)")
elif isinstance(v, complex):
    print("Oops, must not happen.")
else:
    print("Oops, must not happen.")
