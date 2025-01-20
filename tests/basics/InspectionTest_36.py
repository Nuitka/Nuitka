#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests uncompiled functions and compiled functions responses to inspect and isistance.  """

import inspect
import types

# nuitka-project: --python-flag=no_warnings


async def someAsyncgen():
    yield 1


print("Function 'someAsyncgen' has result type:", type(someAsyncgen()))

assert inspect.isfunction(someAsyncgen) is True
assert inspect.isfunction(someAsyncgen()) is False
assert inspect.isgeneratorfunction(someAsyncgen) is False
assert inspect.isgeneratorfunction(someAsyncgen()) is False
assert inspect.iscoroutinefunction(someAsyncgen) is False
assert inspect.iscoroutinefunction(someAsyncgen()) is False
assert inspect.isasyncgenfunction(someAsyncgen) is True
assert inspect.isasyncgenfunction(someAsyncgen()) is False
assert inspect.isawaitable(someAsyncgen) is False
assert inspect.isawaitable(someAsyncgen()) is False

assert isinstance(someAsyncgen(), types.GeneratorType) is False
assert isinstance(someAsyncgen(), types.CoroutineType) is False
assert isinstance(someAsyncgen(), types.AsyncGeneratorType) is True
assert type(someAsyncgen()) == types.AsyncGeneratorType, type(someAsyncgen())
assert isinstance(someAsyncgen, types.AsyncGeneratorType) is False

print("OK.")

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
