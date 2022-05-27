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
module_value1 = module_value2 = module_value3 = module_value4 = 1000
module_key1 = module_key2 = module_key3 = module_key4 = 1000

def calledRepeatedly():
    # Force frame and eliminate forward propagation (currently), and use local
    # variables to avoid impact of global variable access.
    dict_key1 = module_value1
    dict_key2 = module_value2
    dict_key3 = module_value3
    dict_key4 = module_value4

    dict_val1 = module_value1
    dict_val2 = module_value2
    dict_val3 = module_value3
    dict_val4 = module_value4

# construct_begin
    l = {
        dict_key1 : dict_val1,
        dict_key2 : dict_val2,
        dict_key3 : dict_val3,
        dict_key4 : dict_val4
    }
# construct_alternative
    l = 1
# construct_end

    return l, dict_val1, dict_val2, dict_val3, dict_val4, dict_key1, dict_key2, dict_key3, dict_key4

import itertools
for x in itertools.repeat(None, 50000):
    calledRepeatedly()

print("OK.")
