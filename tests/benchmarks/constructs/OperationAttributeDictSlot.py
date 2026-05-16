#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

import itertools


class Bench:
    def __init__(self):
        self.a = 1


obj = Bench()


def calledRepeatedly(cond):
    if cond:
        obj.__dict__
    else:
        pass


for x in itertools.repeat(None, 50000):
    # construct_begin
    calledRepeatedly(True)
    # construct_alternative
    calledRepeatedly(False)
    # construct_end

print("OK.")

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
