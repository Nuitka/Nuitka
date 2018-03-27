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

def func(arg1, arg2, arg3, **star):
    """ Some documentation. """

    pass

print("Starting out: func, __name__:", func, func.__name__)

print("Changing its name:")
func.__name__ = "renamed"

print("With new name: func, __name__:", func, func.__name__)

print("Documentation initially:",  func.__doc__)

print("Changing its doc:")
func.__doc__ = "changed doc" + chr(0) + " with 0 character"

print("Documentation updated:",  repr(func.__doc__))

print("Setting its dict")
func.my_value = "attached value"
print("Reading its dict", func.my_value)

print("__code__ dir")
print(dir(func.__code__))

def func2(arg1, arg2 = "default_arg2", arg3 = "default_arg3"):
    x = arg2 + arg3
    return x

print("func __defaults__", func2.__defaults__)

print("function varnames", func2.__code__.co_varnames)
