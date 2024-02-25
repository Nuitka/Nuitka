#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


def someFunctionThatReturnsDeletedValueViaAttributeLookup():
    class C:
        def __getattr__(self, attr_name):
            nonlocal a
            del a

    c = C()

    a = 1
    c.something
    return a


try:
    someFunctionThatReturnsDeletedValueViaAttributeLookup()
except UnboundLocalError:
    print("OK, object attribute look-up correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaAttributeSetting():
    class C:
        def __setattr__(self, attr_name, value):
            nonlocal a
            del a

    c = C()

    a = 1
    c.something = 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaAttributeSetting()
except UnboundLocalError:
    print("OK, object attribute setting correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaAttributeDel():
    class C:
        def __delattr__(self, attr_name):
            nonlocal a
            del a

            return True

    c = C()

    a = 1
    del c.something
    return a


try:
    someFunctionThatReturnsDeletedValueViaAttributeDel()
except UnboundLocalError:
    print("OK, object attribute del correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaItemLookup():
    class C:
        def __getitem__(self, attr_name):
            nonlocal a
            del a

    c = C()

    a = 1
    c[2]
    return a


try:
    someFunctionThatReturnsDeletedValueViaItemLookup()
except UnboundLocalError:
    print("OK, object subscript look-up correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaItemSetting():
    class C:
        def __setitem__(self, attr_name, value):
            nonlocal a
            del a

    c = C()

    a = 1
    c[2] = 3
    return a


try:
    someFunctionThatReturnsDeletedValueViaItemSetting()
except UnboundLocalError:
    print("OK, object subscript setting correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaItemDel():
    class C:
        def __delitem__(self, attr_name):
            nonlocal a
            del a

    c = C()

    a = 1
    del c[2]
    return a


try:
    someFunctionThatReturnsDeletedValueViaItemDel()
except UnboundLocalError:
    print("OK, object subscript del correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaCall():
    class C:
        def __call__(self):
            nonlocal a
            del a

    c = C()

    a = 1
    c()
    return a


try:
    someFunctionThatReturnsDeletedValueViaCall()
except UnboundLocalError:
    print("OK, object call correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaAdd():
    class C:
        def __add__(self, other):
            nonlocal a
            del a

    c = C()

    a = 1
    c + 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaAdd()
except UnboundLocalError:
    print("OK, object add correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaSub():
    class C:
        def __sub__(self, other):
            nonlocal a
            del a

    c = C()

    a = 1
    c - 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaSub()
except UnboundLocalError:
    print("OK, object sub correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaMul():
    class C:
        def __mul__(self, other):
            nonlocal a
            del a

            return 7

    c = C()

    a = 1
    c * 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaMul()
except UnboundLocalError:
    print("OK, object mul correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaRemainder():
    class C:
        def __mod__(self, other):
            nonlocal a
            del a

            return 7

    c = C()

    a = 1
    c % 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaRemainder()
except UnboundLocalError:
    print("OK, object remainder correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaDivmod():
    class C:
        def __divmod__(self, other):
            nonlocal a
            del a

            return 7

    c = C()

    a = 1
    divmod(c, 1)
    return a


try:
    someFunctionThatReturnsDeletedValueViaDivmod()
except UnboundLocalError:
    print("OK, object divmod correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaPower():
    class C:
        def __pow__(self, other):
            nonlocal a
            del a

            return 7

    c = C()

    a = 1
    c**1
    return a


try:
    someFunctionThatReturnsDeletedValueViaPower()
except UnboundLocalError:
    print("OK, object power correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaUnaryMinus():
    class C:
        def __neg__(self):
            nonlocal a
            del a

            return 7

    c = C()

    a = 1
    -c
    return a


try:
    someFunctionThatReturnsDeletedValueViaUnaryMinus()
except UnboundLocalError:
    print("OK, object unary minus correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaUnaryPlus():
    class C:
        def __pos__(self):
            nonlocal a
            del a

            return 7

    c = C()

    a = 1
    +c
    return a


try:
    someFunctionThatReturnsDeletedValueViaUnaryPlus()
except UnboundLocalError:
    print("OK, object unary plus correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaNot():
    class C:
        def __bool__(self):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    not c
    return a


try:
    someFunctionThatReturnsDeletedValueViaNot()
except UnboundLocalError:
    print("OK, object bool correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInvert():
    class C:
        def __invert__(self):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    ~c
    return a


try:
    someFunctionThatReturnsDeletedValueViaInvert()
except UnboundLocalError:
    print("OK, object invert correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaLshift():
    class C:
        def __lshift__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c << 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaLshift()
except UnboundLocalError:
    print("OK, object lshift correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaRshift():
    class C:
        def __rshift__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c >> 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaRshift()
except UnboundLocalError:
    print("OK, object rshift correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaBitwiseAnd():
    class C:
        def __and__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c & 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaBitwiseAnd()
except UnboundLocalError:
    print("OK, object bitwise and correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaBitwiseOr():
    class C:
        def __or__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c | 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaBitwiseOr()
except UnboundLocalError:
    print("OK, object bitwise or correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaBitwiseXor():
    class C:
        def __xor__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c ^ 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaBitwiseXor()
except UnboundLocalError:
    print("OK, object bitwise xor correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInt():
    class C:
        def __int__(self):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    int(c)
    return a


try:
    someFunctionThatReturnsDeletedValueViaInt()
except UnboundLocalError:
    print("OK, object int correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaFloat():
    class C:
        def __float__(self):
            nonlocal a
            del a

            return 0.0

    c = C()

    a = 1
    float(c)
    return a


try:
    someFunctionThatReturnsDeletedValueViaFloat()
except UnboundLocalError:
    print("OK, object float correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaComplex():
    class C:
        def __complex__(self):
            nonlocal a
            del a

            return 0j

    c = C()

    a = 1
    complex(c)
    return a


try:
    someFunctionThatReturnsDeletedValueViaComplex()
except UnboundLocalError:
    print("OK, object complex correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceAdd():
    class C:
        def __iadd__(self, other):
            nonlocal a
            del a

    c = C()

    a = 1
    c += 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceAdd()
except UnboundLocalError:
    print("OK, object inplace add correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceSub():
    class C:
        def __isub__(self, other):
            nonlocal a
            del a

    c = C()

    a = 1
    c -= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceSub()
except UnboundLocalError:
    print("OK, object inplace sub correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceMul():
    class C:
        def __imul__(self, other):
            nonlocal a
            del a

    c = C()

    a = 1
    c *= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceMul()
except UnboundLocalError:
    print("OK, object inplace mul correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceRemainder():
    class C:
        def __imod__(self, other):
            nonlocal a
            del a

    c = C()

    a = 1
    c %= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceRemainder()
except UnboundLocalError:
    print("OK, object inplace remainder correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplacePower():
    class C:
        def __ipow__(self, other):
            nonlocal a
            del a

            return 7

    c = C()

    a = 1
    c **= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplacePower()
except UnboundLocalError:
    print("OK, object inplace power correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceAnd():
    class C:
        def __iand__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c &= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceAnd()
except UnboundLocalError:
    print("OK, object inplace and correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceFloordiv():
    class C:
        def __ifloordiv__(self, other):
            nonlocal a
            del a

            return 7

    c = C()

    a = 1
    c //= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceFloordiv()
except UnboundLocalError:
    print("OK, object inplace floordiv correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceLshift():
    class C:
        def __ilshift__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c <<= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceLshift()
except UnboundLocalError:
    print("OK, object inplace lshift correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceRshift():
    class C:
        def __irshift__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c >>= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceRshift()
except UnboundLocalError:
    print("OK, object inplace rshift correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceOr():
    class C:
        def __ior__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c |= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceOr()
except UnboundLocalError:
    print("OK, object inplace or correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceTrueDiv():
    class C:
        def __itruediv__(self, other):
            nonlocal a
            del a

            return 7

    c = C()

    a = 1
    c /= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceTrueDiv()
except UnboundLocalError:
    print("OK, object inplace truediv correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceXor():
    class C:
        def __ixor__(self, other):
            nonlocal a
            del a

            return False

    c = C()

    a = 1
    c ^= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceXor()
except UnboundLocalError:
    print("OK, object inplace xor correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaIndex():
    class C:
        def __index__(self):
            nonlocal a
            del a

            return 0

    c = C()

    a = 1
    [1][c]
    return a


try:
    someFunctionThatReturnsDeletedValueViaIndex()
except UnboundLocalError:
    print("OK, object index correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaLen():
    class C:
        def __len__(self):
            nonlocal a
            del a

            return 0

    c = C()

    a = 1
    len(c)
    return a


try:
    someFunctionThatReturnsDeletedValueViaLen()
except UnboundLocalError:
    print("OK, object len correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaRepr():
    class C:
        def __repr__(self):
            nonlocal a
            del a

            return "<some_repr>"

    c = C()

    a = 1
    repr(c)
    return a


try:
    someFunctionThatReturnsDeletedValueViaRepr()
except UnboundLocalError:
    print("OK, object repr correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaStr():
    class C:
        def __str__(self):
            nonlocal a
            del a

            return "<some_repr>"

    c = C()

    a = 1
    str(c)
    return a


try:
    someFunctionThatReturnsDeletedValueViaStr()
except UnboundLocalError:
    print("OK, object str correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaCompare():
    class C:
        def __lt__(self, other):
            nonlocal a
            del a

            return "<some_repr>"

    c = C()

    a = 1
    c < None
    return a


try:
    someFunctionThatReturnsDeletedValueViaCompare()
except UnboundLocalError:
    print("OK, object compare correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaDel():
    class C:
        def __del__(self):
            nonlocal a
            del a

            return "<some_repr>"

    c = C()

    a = 1
    del c
    return a


try:
    someFunctionThatReturnsDeletedValueViaDel()
except UnboundLocalError:
    print("OK, object del correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaHash():
    class C:
        def __hash__(self):
            nonlocal a
            del a

            return 42

    c = C()

    a = 1
    {}[c] = 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaHash()
except UnboundLocalError:
    print("OK, object hash correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaIter():
    class C:
        def __iter__(self):
            nonlocal a
            del a

            return iter(range(2))

    c = C()

    a = 1
    x, y = c
    return a, x, y


try:
    someFunctionThatReturnsDeletedValueViaIter()
except UnboundLocalError:
    print("OK, object iter correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaBytes():
    class C:
        def __bytes__(self):
            nonlocal a
            del a

            return bytes(range(2))

    c = C()

    a = 1
    bytes(c)
    return a, x, y


try:
    someFunctionThatReturnsDeletedValueViaBytes()
except UnboundLocalError:
    print("OK, object bytes correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaEq():
    class C:
        def __eq__(self, other):
            nonlocal a
            del a
            return False

    c = C()

    a = 1
    c == 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaEq()
except UnboundLocalError:
    print("OK, object eq correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaLe():
    class C:
        def __le__(self, other):
            nonlocal a
            del a
            return False

    c = C()

    a = 1
    c <= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaEq()
except UnboundLocalError:
    print("OK, object le correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaGt():
    class C:
        def __gt__(self, other):
            nonlocal a
            del a
            return False

    c = C()

    a = 1
    c > 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaEq()
except UnboundLocalError:
    print("OK, object gt correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaGe():
    class C:
        def __ge__(self, other):
            nonlocal a
            del a
            return False

    c = C()

    a = 1
    c >= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaEq()
except UnboundLocalError:
    print("OK, object ge correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaNe():
    class C:
        def __ne__(self, other):
            nonlocal a
            del a
            return False

    c = C()

    a = 1
    c != 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaEq()
except UnboundLocalError:
    print("OK, object ne correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaContains():
    class C:
        def __contains__(self, item):
            nonlocal a
            del a
            return False

    c = C()

    a = 1
    1 in c
    return a


try:
    someFunctionThatReturnsDeletedValueViaContains()
except UnboundLocalError:
    print("OK, object contains correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInit():
    class C:
        def __init__(self):
            nonlocal a
            del a

    a = 1
    c = C()

    return a


try:
    someFunctionThatReturnsDeletedValueViaInit()
except UnboundLocalError:
    print("OK, object init correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaNew():
    class C:
        def __new__(self):
            nonlocal a
            del a

    a = 1
    c = C()

    return a


try:
    someFunctionThatReturnsDeletedValueViaNew()
except UnboundLocalError:
    print("OK, object new correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaDir():
    class C:
        def __dir__(self):
            nonlocal a
            del a
            return []

    c = C()

    a = 1
    dir(c)
    return a


try:
    someFunctionThatReturnsDeletedValueViaDir()
except UnboundLocalError:
    print("OK, object dir correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaReversed():
    class C:
        def __reversed__(self):
            nonlocal a
            del a
            return None

    a = 1
    c = C()

    reversed(c)
    return a


try:
    someFunctionThatReturnsDeletedValueViaReversed()
except UnboundLocalError:
    print("OK, object reversed correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaFormat():
    class C:
        def __format__(self, string):
            nonlocal a
            del a
            return "formatted string"

    c = C()

    a = 1
    format(c, "some string")
    return a


try:
    someFunctionThatReturnsDeletedValueViaFormat()
except UnboundLocalError:
    print("OK, object format correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaAbs():
    class C:
        def __abs__(self):
            nonlocal a
            del a
            return abs(10)

    a = 1
    c = C()

    abs(c)
    return a


try:
    someFunctionThatReturnsDeletedValueViaAbs()
except UnboundLocalError:
    print("OK, object abs correctly deleted an item.")
else:
    print("Ouch.!")

# TODO: There must be way more than these.

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
