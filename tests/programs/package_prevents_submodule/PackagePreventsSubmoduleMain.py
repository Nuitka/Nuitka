#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import os
import sys

ORIG = None
attemptImports = None

# Nuitka gives warnings, that even if disabled touch this.
__warningregistry__ = {}


def diff(dct):
    print("globals diff", ORIG.symmetric_difference(dct))
    mdiff = START.symmetric_difference(sys.modules)

    # Python2 does strange thing with relative imports, that we do not.
    if str is bytes:
        if "some_package.os" in mdiff:
            mdiff.remove("some_package.os")

    # Sets are not ordered and can differ otherwise
    mdiff = tuple(sorted(mdiff))

    print("Modules diff", mdiff)


START = set(sys.modules)
ORIG = set(globals())


def attemptImports(prefix):
    print(prefix, "GO1:")
    try:
        import some_package
    except BaseException as e:
        print("Exception occurred", e)
    else:
        print("Import success.", some_package.__name__)

    diff(globals())

    print(prefix, "GO2:")
    try:
        from some_package.some_module import Class4
    except BaseException as e:
        print("Exception occurred", e)
    else:
        print("Import success.", Class4)
    diff(globals())

    print(prefix, "GO3:")
    try:
        from some_package import some_module
    except BaseException as e:
        print("Exception occurred", e)
    else:
        print("Import success.", some_module.__name__)
    diff(globals())

    print(prefix, "GO4:")
    try:
        from some_package import raiseError
    except BaseException as e:
        print("Exception occurred", e)
    else:
        print("Import success.", raiseError.__name__)
    diff(globals())

    print(prefix, "GO5:")
    try:
        from some_package import Class5
    except BaseException as e:
        print("Exception occurred", e)
    else:
        print("Import success.", Class5)
    diff(globals())

    print(prefix, "GO6:")
    try:
        from some_package import Class3
    except BaseException as e:
        print("Exception occurred", e)
    else:
        print("Import success.", Class3)
    diff(globals().keys())


os.environ["TEST_SHALL_RAISE_ERROR"] = "1"
attemptImports("With expected errors")
os.environ["TEST_SHALL_RAISE_ERROR"] = "0"
attemptImports("With error resolved")
del sys.modules["some_package"]
attemptImports("With deleted module")

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
