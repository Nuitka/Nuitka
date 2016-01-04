#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
    c += 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaAdd()
except UnboundLocalError:
    print("OK, object add correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaSub():
    class C:
        def __add__(self, other):
            nonlocal a
            del a
    c = C()


    a = 1
    c += 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaSub()
except UnboundLocalError:
    print("OK, object sub correctly deleted an item.")
else:
    print("Ouch.!")


# TODO: There is a whole lot more operations to cover.

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
    print("OK, object not correctly deleted an item.")
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


# TODO: The "del" operation may surrect a variable value by "__del__".

# TODO: There must be way more than these.
