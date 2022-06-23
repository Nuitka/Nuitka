#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

module_value1 = list()
module_value2 = 3000

def calledRepeatedly():
    # Force frame and eliminate forward propagation (currently).
    module_value1

    local_value = module_value1

    s = module_value1
    s.append
# construct_begin
    s.append
# construct_end
    s.append

    return s, local_value

import itertools
for x in itertools.repeat(None, 25000):
    calledRepeatedly()

print("OK.")
