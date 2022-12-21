#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Tests to cover default parameter behaviors.

"""

from __future__ import print_function

# nuitka-project: --nofollow-imports

# pylint: disable=dangerous-default-value,unused-argument

module_level = 1


def defaultValueTest1(no_default, some_default_constant=1):
    return some_default_constant


def defaultValueTest2(no_default, some_default_computed=module_level * 2):
    local_var = no_default
    return local_var, some_default_computed


def defaultValueTest3(no_default, func_defaulted=defaultValueTest1(module_level)):
    return [func_defaulted for _i in range(8)]


def defaultValueTest4(no_default, lambda_defaulted=lambda x: x**2):
    c = 1
    d = 1
    return (i + c + d for i in range(8))


def defaultValueTest5(no_default, tuple_defaulted=(1, 2, 3)):
    return tuple_defaulted


def defaultValueTest6(no_default, list_defaulted=[1, 2, 3]):
    list_defaulted.append(5)

    return list_defaulted


print(defaultValueTest1("ignored"))

# The change of the default variable doesn't influence the default
# parameter of defaultValueTest2, that means it's also calculated
# at the time the function is defined.
module_level = 7
print(defaultValueTest2("also ignored"))

print(defaultValueTest3("no-no not again"))

print(list(defaultValueTest4("unused")))

print(defaultValueTest5("unused"))

print(defaultValueTest6("unused"), end="")
print(defaultValueTest6("unused"))

print(defaultValueTest6.__defaults__)

defaultValueTest6.func_defaults = ([1, 2, 3],)
print(defaultValueTest6.__defaults__)

print(defaultValueTest6(1))
