#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


from __future__ import print_function

import itertools


def compiled_func(a=1, b=2, c=3, d=4, e=5, f=6):
    return a, b, c, d, e, f


def calledRepeatedly():
    # This is supposed to make a call to a compiled function, which is
    # being optimized separately.
    compiled_f = compiled_func

    # construct_begin
    compiled_f()
    compiled_f()
    compiled_f()
    # construct_alternative
    pass
    # construct_end

    return compiled_f


for x in itertools.repeat(None, 50000):
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
