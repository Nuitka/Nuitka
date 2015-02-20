#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Softwar where
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

module_value1 = 5
module_value2 = 3

def calledRepeatedly():
    # Force frame and eliminate forward propagation (currently).
    module_value1

    # Make sure we have a local variable x anyway
    s = 2

    local_value = module_value1

    for x in range(local_value, local_value+15):
# construct_begin
        s += 1000
# construct_end
        pass

for x in xrange(50000):
    calledRepeatedly()

print("OK.")
