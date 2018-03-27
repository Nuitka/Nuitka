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

# Python2 will fallback to this variable, which Python3 will ignore.
__class__ = "Using module level __class__ variable, would be wrong for Python3"  # @ReservedAssignment

class ClassWithUnderClassClosure:
    def g(self):
        def h():
            print("Variable __class__ in ClassWithUnderClassClosure is", __class__)

        h()

        try:
            print("ClassWithUnderClassClosure: Super in ClassWithUnderClassClosure is", super())
        except Exception as e:
            print("ClassWithUnderClassClosure: Occurred during super call", repr(e))


print("Class with a method that has a local function accessing __class__:")
ClassWithUnderClassClosure().g()

class ClassWithoutUnderClassClosure:
    def g(self):
        __class__ = "Providing __class__ ourselves, then it must be used"  # @ReservedAssignment
        print(__class__)

        try:
            print("ClassWithoutUnderClassClosure: Super", super())
        except Exception as e:
            print("ClassWithoutUnderClassClosure: Occurred during super call", repr(e))


ClassWithoutUnderClassClosure().g()

# For Python2 only.
__class__ = "Global __class__"  # @ReservedAssignment

def deco(C):
    print("Decorating", repr(C))

    class D(C):
        pass

    return D

@deco
class X:
    __class__ = "some string"

    def f1(self):
        print("f1", locals())

        try:
            print("f1", __class__)
        except Exception as e:
            print("Accessing __class__ in f1 gave", repr(e))

    def f2(self):
        print("f2", locals())

    def f4(self):
        print("f4", self)
        self = X()
        print("f4", self)

        try:
            print("f4", super())
            print("f4", super().__self__)
        except TypeError:
            import sys
            assert sys.version_info < (3,)

    f5 = lambda x: __class__

    def f6(self_by_another_name):  # @NoSelf
        try:
            print("f6", super())
        except TypeError:
            import sys
            assert sys.version_info < (3,)

    def f7(self):
        try:
            yield super()
        except TypeError:
            import sys
            assert sys.version_info < (3,)

    print("Early pre-class calls begin")
    print("Set in class __class__", __class__)
    # f1(1)
    f2(2)
    print("Early pre-class calls end")

    del __class__

x = X()
x.f1()
x.f2()
x.f4()
print("f5", x.f5())
x.f6()
print("f7", list(x.f7()))
