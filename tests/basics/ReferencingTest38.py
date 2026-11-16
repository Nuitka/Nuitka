#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Reference counting tests for Python3.8 or higher.

These contain functions that do specific things, where we have a suspect that
references may be lost or corrupted. Executing them repeatedly and checking the
reference count is how they are used.

These are Python3.8 specific constructs, that will give a SyntaxError or not be
relevant on older versions.
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
    value = "x" * 100
    value += (value := "y")


def simpleFunction2():
    value = [1] * 100
    value += (value := [2])


def simpleFunction3():
    value = [1] * 100
    value += ((value := item) for item in range(10))


def simpleFunction4():
    value = "x" * 100

    def inner():
        nonlocal value
        value += (value := "y")

    inner()


module_value = None


def simpleFunction5():
    global module_value

    module_value = "x" * 100
    module_value += (module_value := "y")


class Container:
    pass


def simpleFunction6():
    container = Container()
    container.value = "x" * 100
    container.value += (container := Container()).__class__.__name__


def simpleFunction7():
    for flag in (True, False):
        value = "x" * 100
        result = value if flag else (value := "y")
        result = result + (value := "z")


def simpleFunction8():
    value = "x" * 100
    result = ((value or "a") and (value := "b")) + (value := "c")


def simpleFunction9():
    for flag in (True, False):
        value = "x" * 100
        result = value + (value if flag else (value := "y"))


def simpleFunction10():
    data = bytes(range(256))
    cur = 1
    value = data[cur : (cur := cur + 2)]


module_genexpr_value = [1]


def simpleFunction11():
    global module_genexpr_value

    module_genexpr_value = [1]
    module_genexpr_value += ((module_genexpr_value := item) for item in range(3))


def simpleFunction12():
    value = [1]
    value += [(value := item) for item in range(3)]


def simpleFunction13():
    value = "x" * 100

    try:
        value += (value := "y") + 1
    except TypeError:
        pass


def simpleFunction14():
    mapping = {0: "x" * 100}
    key = 0
    mapping[key] += (key := "y")


def simpleFunction15():
    value = [1, 2]
    value += (item + value[0] for item in range(2))


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
