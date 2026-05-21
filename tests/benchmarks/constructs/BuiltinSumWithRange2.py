#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


import itertools

empty = ()
start = 5
stop = 1005


def test():
    assert sum(range(0, 0)) == 0
    assert sum(range(0, 1)) == 0
    assert sum(range(0, 2)) == 1
    assert sum(range(1, 5)) == 10
    assert sum(range(-5, 5)) == -5
    assert sum(range(5, 0)) == 0
    assert sum(range(0, 100)) == 4950
    assert sum(range(0, 10000000)) == 49999995000000

    # Genexpr identity: sum(x for x in range(start, stop))
    assert sum(x for x in range(0, 0)) == 0
    assert sum(x for x in range(1, 5)) == 10
    assert sum(x for x in range(-5, 5)) == -5


def calledRepeatedly(start, stop, empty):
    # Force frame
    itertools

    # We measure sum(range(start, stop)) fused to closed-form arithmetic vs. empty baseline.
    # At runtime BUILTIN_SUM_RANGE2 fires - O(1) arithmetic series.

    # construct_begin
    y = sum(range(start, stop))
    # construct_alternative
    y = sum(x for x in range(start, stop))
    # construct_alternative
    y = sum(empty)
    # construct_end

    return y


test()

for x in itertools.repeat(None, 50000):
    calledRepeatedly(start, stop, empty)

print("OK.")

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
