#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

import random

def getrandom():
    return random.random()

def optimizerCrashIssue13():
    try:
        print("Something with side effects that might raise.")
    except Exception as x:
        print("Caught it")
        raise
        print("Should not reach this")
        raise x

# Just so it won't be optimized away entirely, the run time has no issue.
optimizerCrashIssue13()

def codegeneratorCrashIssue15():
    f = float("nan")
    g = getrandom() # Prevent optimization of "nan"-constant

    return f+g

# Just so it won't be optimized away entirely.
codegeneratorCrashIssue15()

def codegeneratorCrashIssue30():
    f = getrandom()  # Prevent optimization

    f   # Will be optimized way in later versions of Nuitka.
    # TODO: May already be the case.


def runtimeCrashIssue():
    # Some C functions don't set an exception when called.
    from itertools import count
    import sys

    try:
        # This will set an error and return a value for at least Python3.2
        count(1, sys.maxsize+5)
    except TypeError:
        # For Python2.6, the two arguments variant didn't exist yet.
        assert sys.version_info < (2,7)

runtimeCrashIssue()
