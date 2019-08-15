#     Copyright 2019, Tommy Li, mailto:tommyli3318@gmail.com
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


# nuitka-skip-unless-imports: decorator

from decorator import decorate
import time

def _memoize(func, *args, **kw):
    if kw:
        key = args, frozenset(kw.items())
    else:
        key = args
    cache = func.cache
    if key in cache:
        return "cached"
    result = func(*args, **kw)
    cache[key] = result
    return result

def memoize(f):
    f.cache = {}
    return decorate(f, _memoize)

@memoize
def some_function():
    return "not cached"

print(some_function())
print(some_function())