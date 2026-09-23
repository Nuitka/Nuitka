#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""PGO test for 'type.__prepare__' results of custom metaclasses."""

# nuitka-project: --pgo-python


class Meta(type):
    @classmethod
    def __prepare__(metacls, class_name, bases, **kwargs):
        return {}

    def __new__(metacls, class_name, bases, namespace, **kwargs):
        return type.__new__(metacls, class_name, bases, namespace)


class Constants(metaclass=Meta):
    a = 1
    b = 2
    c = a + b


class Meta2(Meta):
    pass


class Other(metaclass=Meta2):
    d = 4


print(Constants.a, Constants.b, Constants.c, Other.d)
print("OK.")

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
