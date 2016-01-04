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
module_value1 = 1000
module_value2 = None
module_value3 = None

def calledRepeatedly():
    # Force frame and eliminate forward propagation (currently).
    module_value1

    local_value = module_value1

    # Use writing to global variable as access method.
    global module_value2, module_value3

# construct_begin
    module_value2 = local_value
# construct_end

    module_value3 = local_value

for x in xrange(50000):
    calledRepeatedly()

print("OK.")
