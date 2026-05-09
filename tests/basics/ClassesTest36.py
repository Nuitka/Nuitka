#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Covers Python 3.6+ class '__init_subclass__' support with 'super()'."""

print("Testing class __init_subclass__ with class decorator requiring __classcell__:")


def makeClassDecorator(cls):
    def __init__(self):
        cls.__self_init__(self)

    cls.__init__ = __init__
    return cls


class ClassWithInitSubclassSuperParent:
    def __init__(self):
        print("ClassWithInitSubclassSuper Parent Initialized")

    def __init_subclass__(cls, decorator):
        decorator(cls)()


class ClassWithInitSubclassSuperChild(
    ClassWithInitSubclassSuperParent,
    decorator=makeClassDecorator,
):
    def __self_init__(self):
        super().__init__()


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
