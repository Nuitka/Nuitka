#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Reference counting tests for Python3.6 or higher.

These contain functions that do specific things, where we have a suspect
that references may be lost or corrupted. Executing them repeatedly and
checking the reference count is how they are used.

These are Python3.6 specific constructs, that will give a SyntaxError or
not be relevant on older versions.
"""

import os
import sys

# While we use that for comparison code, no need to compile that.
# nuitka-project: --nofollow-import-to=nuitka

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    ),
)

# isort:start

from nuitka.tools.testing.Common import executeReferenceChecked


def simpleFunction1():
    class Parent[T]:
        value: T

    return Parent


def no_simpleFunction2():
    class Parent[T]:
        value: T

    class Child[T](Parent[T]):
        another_value: int

    return Child


# These need stderr to be wrapped.
tests_stderr = ()

# Disabled tests
tests_skipped = {}

result = executeReferenceChecked(
    prefix="simpleFunction",
    names=globals(),
    tests_skipped=tests_skipped,
    tests_stderr=tests_stderr,
    explain=False,
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
