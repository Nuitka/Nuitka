#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
from __future__ import print_function


def displayDict(d):
    d = dict(d)

    del d["displayDict"]

    del d["__builtins__"]

    if "__loader__" in d:
        if str is bytes:
            del d["__loader__"]
        else:
            d["__loader__"] = "<__loader__ removed>"

    if "__file__" in d:
        d["__file__"] = "<__file__ removed>"

    if "__cached__" in d:
        d["__cached__"] = "<__cached__ removed>"

    if "__spec__" in d:
        d["__spec__"].loader = "loader removed"
        d["__spec__"].origin = "origin removed"
        d["__spec__"].submodule_search_locations = "submodule_search_locations removed"

    if "__compiled__" in d:
        del d["__compiled__"]

    import pprint

    return pprint.pformat(d)


print(displayDict(globals()))

print("__name__: ", __name__)
print("__package__: ", __package__)
