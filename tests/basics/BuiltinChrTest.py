#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""The 'chr' built-in with values out of range and not usable as an index."""

from __future__ import print_function

import sys


class Index(object):
    def __index__(self):
        return 65


def check(value):
    try:
        result = repr(chr(value))
    except Exception as e:  # pylint: disable=broad-except
        result = "%s: %s" % (type(e).__name__, e)
    print(repr(value)[:24], "->", result)


# Values not known at compile time.
base = len(sys.argv)

for value in (
    65 * base,
    0x10FFFF * base,
    0x110000 * base,
    -base,
    2**31 * base,
    2**63 * base,
    -(2**63) * base,
    1.5 * base,
    None,
    Index(),
    True,
):
    check(value)

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
