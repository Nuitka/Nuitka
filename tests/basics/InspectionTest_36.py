#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Tests uncompiled functions and compiled functions responses to inspect and isistance.  """

import inspect
import types

# nuitka-project: --python-flag=no_warnings


async def compiledAsyncgen():
    yield 1


print(type(compiledAsyncgen()))

assert inspect.isfunction(compiledAsyncgen) is True
assert inspect.isgeneratorfunction(compiledAsyncgen) is False
assert inspect.iscoroutinefunction(compiledAsyncgen) is False
assert inspect.isasyncgenfunction(compiledAsyncgen) is True

assert isinstance(compiledAsyncgen(), types.GeneratorType) is False
assert isinstance(compiledAsyncgen(), types.CoroutineType) is False
assert isinstance(compiledAsyncgen(), types.AsyncGeneratorType) is True
assert type(compiledAsyncgen()) == types.AsyncGeneratorType, type(compiledAsyncgen())
assert isinstance(compiledAsyncgen, types.AsyncGeneratorType) is False

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
