#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Reference counting tests for Python2 specific features.

These contain functions that do specific things, where we have a suspect
that references may be lost or corrupted. Executing them repeatedly and
checking the reference count is how they are used.
"""

# While we use that for comparison code, no need to compile that.
# nuitka-project: --nofollow-import-to=nuitka

import os
import sys

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

from nuitka.tools.testing.Common import executeReferenceChecked

x = 17


# Python2.7 or higher syntax things are here.
def simpleFunction1():
    return {i: x for i in range(x)}


def simpleFunction2():
    try:
        return {y: i for i in range(x)}
    except NameError:
        pass


def simpleFunction3():
    return {i for i in range(x)}


def simpleFunction4():
    try:
        return {y for i in range(x)}
    except NameError:
        pass


# These need stderr to be wrapped.
tests_stderr = ()

# Disabled tests
tests_skipped = {}

result = executeReferenceChecked(
    prefix="simpleFunction",
    names=globals(),
    tests_skipped=tests_skipped,
    tests_stderr=tests_stderr,
)

print("OK." if result else "FAIL.")
sys.exit(0 if result else 1)

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
