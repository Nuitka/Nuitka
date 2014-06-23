#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#

# In this test we show that return in try/finally executes the finally part
# just fine.

from __future__ import print_function


def eight():
    return 8

def nine():
    return 9

def returnInTried():
    try:
        return eight()
    finally:
        print("returnInTried", end = " ")

def returnInFinally():
    try:
        print("returnInFinally tried", end = " ")
    finally:
        return nine()

print(returnInTried())
print(returnInFinally())
