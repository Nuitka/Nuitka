#     Copyright 2019, Tommy Li, mailto:tommyli3318@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#


# nuitka-skip-unless-imports: asn1crypto

from asn1crypto.core import ObjectIdentifier

class MyType(ObjectIdentifier):
    _map = {
        '1.8.2.1.23': 'value_name',
        '1.8.2.1.24': 'other_value',
    }

# Will print: "value_name"
print(MyType('1.8.2.1.23').native)

# Will print: "1.8.2.1.23"
print(MyType('1.8.2.1.23').dotted)

# Will print: "1.8.2.1.25"
print(MyType('1.8.2.1.25').native)

# Will print "value_name"
print(MyType.map('1.8.2.1.23'))

# Will print "1.8.2.1.23"
print(MyType.unmap('value_name'))


from asn1crypto.core import BitString
b1 = BitString((1, 0, 1))

class MyFlags(BitString):
    _map = {
        0: 'edit',
        1: 'delete',
        2: 'manage_users',
    }

permissions = MyFlags({'edit', 'delete'})

if permissions['edit'] and permissions['delete']:
    print('Can edit and delete')

if 'manage_users' in permissions.native:
    print('Is admin')


from asn1crypto.core import OctetBitString, IntegerBitString
bit = BitString((1, 0, 1, 1))
print(bit.native)

octet = bit.cast(OctetBitString)

print(octet.native)

i = bit.cast(IntegerBitString)

print(i.native)


from asn1crypto.core import Sequence, Choice, IA5String, UTCTime, ObjectIdentifier

class Person(Choice):
    _alternatives = [
        ('name', IA5String),
        ('email', IA5String, {'implicit': 0}),
    ]

class Record(Sequence):
    _fields = [
        ('id', ObjectIdentifier),
        ('created', UTCTime),
        ('creator', Person, {'explicit': 0, 'optional': True}),
    ]

person = Person(name='email', value='will@wbond.net')

print(person.implicit)

print(person.untag().implicit)

print(person.tag)
