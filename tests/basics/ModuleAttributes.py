#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Some module documentation.

With newline and stuff."""

from __future__ import print_function

import os
import sys

print("doc:", __doc__)
print("filename:", os.path.basename(__file__))
print("builtins:", __builtins__)
print("debug", __debug__)
print("debug in builtins", __builtins__.__debug__)

print("__initializing__", end=" ")
try:
    print(__initializing__)
except NameError:
    print("not found")


def checkFromFunction():
    frame = sys._getframe(1)  # pylint: disable=protected-access

    def displayDict(d):
        if "__loader__" in d:
            d = dict(d)
            d["__loader__"] = "<__loader__ removed>"

        if "__file__" in d:
            d = dict(d)
            d["__file__"] = "<__file__ removed>"

        if "__compiled__" in d:
            d = dict(d)
            del d["__compiled__"]

        import pprint

        return pprint.pformat(d)

    print("Globals", displayDict(frame.f_globals))
    print("Locals", displayDict(frame.f_locals))
    print("Is identical", frame.f_locals is frame.f_globals)


checkFromFunction()
