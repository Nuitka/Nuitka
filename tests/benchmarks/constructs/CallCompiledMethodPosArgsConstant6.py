#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
from __future__ import print_function

class C:
    def compiled_method(self, a,b,c,d,e,f):
        return a, b, c, d, e, f

def calledRepeatedly():
    inst = C()

    # This is supposed to make a call to a non-compiled function, which is
    # being optimized separately.
# construct_begin
    inst.compiled_method("some", "random", "values", "to", "check", "call")
    inst.compiled_method("some", "other", "values", "to", "check", "call")
    inst.compiled_method("some", "new", "values", "to", "check", "call")

# construct_alternative
    pass
# construct_end

for x in xrange(50000):
    calledRepeatedly()

print("OK.")
