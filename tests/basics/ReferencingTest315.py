#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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


def simpleFunction1():
    print([*i for i in [[1, 2, 3], [4, 5, 6]]])
    print({*i for i in [[1, 2, 3], [4, 5, 6]]})
    print(list((*i for i in [[1, 2, 3], [4, 5, 6]])))
    print({**a for a in [{1: 2}, {3: 4}]})


class _SimpleMapping(object):
    def __init__(self, data):
        self.data = data

    def keys(self):
        return (k for k in self.data)

    def __getitem__(self, key):
        return self.data[key]


class _NonIterableKeys(object):
    def keys(self):
        return object()


def simpleFunction2():
    m1 = _SimpleMapping({"a": 1, "b": 2})
    m2 = _SimpleMapping({"b": 3, "c": 4})
    res = {**m for m in [m1, m2]}
    assert res == {"a": 1, "b": 3, "c": 4}

    for bad in ([("a", 1)], _NonIterableKeys()):
        try:
            {**m for m in [m1, bad]}
        except TypeError:
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
