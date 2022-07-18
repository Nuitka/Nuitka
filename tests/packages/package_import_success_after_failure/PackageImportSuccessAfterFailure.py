#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
from __future__ import print_function

# nuitka-project: --follow-import-to=variable_package

ORIG = None


def display_difference(dct):
    print(ORIG.symmetric_difference(dct))


# Python2 has this in globals() so force it there for Python3
# to have same ORIG.
if str is bytes:
    e = None
ORIG = set(globals())

print("Initial try on top level package:")
try:
    import variable_package
except BaseException as e:
    print("Occurred", str(e))

display_difference(globals())

print("Retry with submodule import:")

try:
    from variable_package.SomeModule import Class4
except BaseException as e:
    print("Occurred", str(e))
display_difference(globals())

print("Try with import from submodule:")
try:
    from variable_package import SomeModule
except BaseException as e:
    print("Occurred", str(e))
display_difference(globals())

print("Try with variable import from top level package assigned before raise:")
try:
    from variable_package import raisy
except BaseException as e:
    print("Occurred", str(e))

display_difference(globals())

print("Try with variable import from top level package assigned after raise:")
try:
    from variable_package import Class5
except BaseException as e:
    print("Occurred", str(e))
display_difference(globals())

print("Try with variable import from top level package assigned before raise:")
try:
    from variable_package import Class3
except BaseException as e:
    print("Occurred", str(e))
display_difference(globals().keys())
