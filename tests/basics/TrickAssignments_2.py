#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
def someFunctionThatReturnsDeletedValueViaLong():
    class C:
        def __int__(self):
            a.append(2)

            return False

    c = C()

    a = [1]
    long(c)
    return a


if someFunctionThatReturnsDeletedValueViaLong()[-1] == 2:
    print("OK, object long correctly modified an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaNot():
    class C:
        def __nonzero__(self):
            a.append(2)

            return False

    c = C()

    a = [1]
    not c
    return a


if someFunctionThatReturnsDeletedValueViaNot()[-1] == 2:
    print("OK, object bool correctly modified an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaCompare():
    class C:
        def __cmp__(self, other):
            a.append(2)

            return 0

    c = C()

    a = [1]
    c < None
    return a


if someFunctionThatReturnsDeletedValueViaCompare()[-1] == 2:
    print("OK, object compare correctly modified an item.")
else:
    print("Ouch.!")
