#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


def someFunctionThatReturnsDeletedValueViaMaxtrixMult():
    class C:
        def __matmul__(self, other):
            nonlocal a
            del a

    c = C()

    a = 1
    c @ 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaMaxtrixMult()
except UnboundLocalError:
    print("OK, object matrix mult correctly deleted an item.")
else:
    print("Ouch.!")


def someFunctionThatReturnsDeletedValueViaInplaceMaxtrixMult():
    class C:
        def __imatmul__(self, other):
            nonlocal a
            del a

    c = C()

    a = 1
    c @= 1
    return a


try:
    someFunctionThatReturnsDeletedValueViaInplaceMaxtrixMult()
except UnboundLocalError:
    print("OK, object inplace matrix mult correctly deleted an item.")
else:
    print("Ouch.!")

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
