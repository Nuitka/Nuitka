#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

def a():
    x = 1
    class A:
        print(x)

    print("Called", a)

    return A

def b():
    class B:
        pass

    print("Called", b)

    return B

from collections import OrderedDict

def m():
    class M(type):
        # @classmethod
        def __new__(cls, class_name, bases, attrs, **over):
            print("Metaclass M.__new__ cls", cls, "name", class_name, "bases", bases, "dict", attrs, "extra class defs", over)

            return type.__new__(cls, class_name, bases, attrs)

        def __init__(self, name, bases, attrs, **over):
            print("Metaclass M.__init__", name, bases, attrs, over)
            super().__init__(name, bases, attrs)

        # TODO: Removing this
        # @classmethod
        def __prepare__(name, bases, **over):
            print("Metaclass M.__prepare__", name, bases, over)
            return OrderedDict()

    print("Called", m)

    return M

def d():
    print( "Called", d )

    return 1

def e():
    print( "Called", e )

    return 2


class C1(a(), b(), other = d(), metaclass = m(), yet_other = e()):
    pass

print(type(C1.__dict__))
