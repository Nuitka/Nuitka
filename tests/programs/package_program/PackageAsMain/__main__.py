#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""
Test case, where __main__ is the main program in a directory.
"""


from __future__ import print_function

import sys

# There is a fake module with just "__name__" for package mode created by CPython.
real_name = __name__

print("Hello world!")
print("I am thinking of myself as __name__", repr(__name__))
print("Module object has __name__", repr(sys.modules[real_name].__name__))
print("My package value is", repr(__package__))
if not __package__:
    print("Module has package value", repr(sys.modules[real_name].__package__))
    print("Module repr", sys.modules[real_name])
print("__file__", __file__)

print("Try to import from module in main package:")
for_import = "something from __main__"

try:
    from . import for_import as value

    print("Imported", value)
except (ImportError, SystemError, ValueError) as e:
    print("Gave exception:", e)
