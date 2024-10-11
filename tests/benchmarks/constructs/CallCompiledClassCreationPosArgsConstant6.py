#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import itertools


class C(object):
    def __init__(self, a, b, c, d, e, f):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f


def calledRepeatedly():
    # Avoid module variable access speed to play a role
    local_C = C

    # This is supposed to make a call to a compiled method, which is
    # being optimized separately.
    # construct_begin
    x1 = local_C("some", "random", "values", "to", "check", "call")
    x2 = local_C("some", "other", "values", "to", "check", "call")
    x3 = local_C("some", "new", "values", "to", "check", "call")
    # construct_end


for x in itertools.repeat(None, 10000):
    calledRepeatedly()

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
