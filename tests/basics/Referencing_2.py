#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
import sys, os

# Find nuitka package relative to us.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            ".."
        )
    )
)
from nuitka.tools.testing.Common import (
    executeReferenceChecked,
    checkDebugPython
)

checkDebugPython()


x = 17

# Python2 only syntax things are here.
def simpleFunction1():
    try:
        raise TypeError, (3,x,x,x)
    except TypeError:
        pass

def simpleFunction2():
    try:
        raise ValueError(1,2,3), ValueError(1,2,3)
    except Exception:
        pass

def simpleFunction3():
    try:
        raise ValueError, 2, None
    except Exception:
        pass

def simpleFunction4():
    try:
        raise ValueError, 2, 3
    except Exception:
        pass

def simpleFunction5():
    def nested_args_function((a,b), c):
        return a, b, c

    nested_args_function((1, 2), 3)

def simpleFunction6():
    def nested_args_function((a,b), c):
        return a, b, c

    try:
        nested_args_function((1,), 3)
    except ValueError:
        pass

def simpleFunction7():
    def nested_args_function((a,b), c):
        return a, b, c

    try:
        nested_args_function((1, 2, 3), 3)
    except ValueError:
        pass


# These need stderr to be wrapped.
tests_stderr = ()

# Disabled tests
tests_skipped = {}

result = executeReferenceChecked(
    prefix        = "simpleFunction",
    names         = globals(),
    tests_skipped = tests_skipped,
    tests_stderr  = tests_stderr
)

sys.exit(0 if result else 1)
