#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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


# nuitka-skip-unless-imports: cachetools

from cachetools import TTLCache
from sched import scheduler

cache = TTLCache(maxsize=128, ttl=5)

runner = scheduler()

cache["abc"] = 42

def display_cached_value(cache_key):
    try:
        cached_value = cache[cache_key]
        print("{0}={1}".format(cache_key, cached_value))
    except KeyError:
        print("{0}=Not in cache".format(cache_key))

runner.enter(2, 1, display_cached_value, argument=("abc",))
runner.enter(6, 1, display_cached_value, argument=("abc",))
runner.run()


from cachetools import LRUCache

cache = LRUCache(maxsize=128)

runner = scheduler()

cache["abc"] = 50

def display_cached_value(cache_key):
    try:
        cached_value = cache[cache_key]
        print("{0}={1}".format(cache_key, cached_value))
    except KeyError:
        print("{0}=Not in cache".format(cache_key))

runner.enter(2, 1, display_cached_value, argument=("abc",))
runner.enter(6, 1, display_cached_value, argument=("abc",))
runner.run()
