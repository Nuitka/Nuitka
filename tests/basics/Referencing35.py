#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

# Find common code relative in file system. Not using packages for test stuff.
sys.path.insert(
    0,
    os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            ".."
        )
    )
)
from test_common import (
    executeReferenceChecked,
    my_print,
)

if not hasattr(sys, "gettotalrefcount"):
    my_print("Warning, using non-debug Python makes this test ineffective.")
    sys.gettotalrefcount = lambda : 0

def run_async(coro):
    buffer = []
    result = None
    while True:
        try:
            buffer.append(coro.send(None))
        except StopIteration as ex:
            result = ex.args[0] if ex.args else None
            break
    return buffer, result

class I:
    async def __aiter__(self):
        return self

    def __anext__(self):
        return ()

def raisy():
    raise TypeError

def simpleFunction1():
    aiter = I()

    async def foo():
        # TODO: This is not yet releasing it all, why
        raisy()

        async for i in aiter:
            print('never going to happen')

    try:
        run_async(foo())
    except TypeError:
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
