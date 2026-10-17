"""Check dict.fromkeys exception exits for runtime iterables."""

from __future__ import print_function


def fromkeys2(values):
    return list(dict.fromkeys(values))


def fromkeys3(values):
    return list(dict.fromkeys(values, 42))


def raisingIterator():
    yield 1
    raise ValueError("iterator failure")


class BrokenIterable(object):
    def __iter__(self):
        raise RuntimeError("iter failure")


class BrokenHash(object):
    def __hash__(self):
        raise RuntimeError("hash failure")


for operation in (fromkeys2, fromkeys3):
    assert sorted(operation([2, 1, 2])) == [1, 2]
    assert operation([]) == []
    for values, expected in (
        ([[]], TypeError),
        (raisingIterator(), ValueError),
        (BrokenIterable(), RuntimeError),
        ([BrokenHash()], RuntimeError),
    ):
        try:
            operation(values)
        except expected:
            print(operation.__name__, expected.__name__)
        else:
            raise AssertionError("dict.fromkeys did not propagate the exception")

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
