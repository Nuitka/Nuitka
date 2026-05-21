#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


import itertools

empty = ()


def test():
    assert any(range(0)) is False
    assert any(range(1)) is False
    assert any(range(2)) is True
    assert any(range(5)) is True
    assert any(range(-5)) is False


def calledRepeatedly(n, empty):
    # Force frame
    itertools

    # We measure any(range(n)) fused to n >= 2 vs. empty baseline.
    # After fusion: no range object, no iterator, just a comparison.

    # construct_begin
    y = any(range(n))
    # construct_alternative
    y = any(empty)
    # construct_end

    return y


test()

for x in itertools.repeat(None, 50000):
    calledRepeatedly(1000, empty)

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
