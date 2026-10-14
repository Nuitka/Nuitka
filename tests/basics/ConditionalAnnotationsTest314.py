#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Python 3.14 conditional deferred annotations for classes and modules."""

import annotationlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    SetStr = set

condition_calls = [0]


def condition():
    condition_calls[0] += 1
    return True


if TYPE_CHECKING:
    module_conditional: SetStr

module_unconditional: int


class ConditionalAnnotations:
    unconditional: int

    if TYPE_CHECKING:
        checked_only: SetStr

    if condition():
        executed: str
    else:
        not_executed: bytes

    final: float = 1.0


class CheckedOnlyAnnotations:
    if TYPE_CHECKING:
        checked_only: SetStr
        checked_only_defined: SetStr = None


def displayDict(d):
    result = "{"
    first = True
    for key, value in sorted(d.items()):
        if not first:
            result += ","

        result += "%s: %s" % (repr(key), repr(value))
        first = False
    result += "}"

    return result


print(
    "Class conditional annotations:",
    displayDict(ConditionalAnnotations.__annotations__),
)
print(
    "Class checked only annotations:",
    displayDict(CheckedOnlyAnnotations.__annotations__),
)
print("Condition calls:", condition_calls[0])

# The module "__annotate__" is only created on demand, so go through the
# "annotationlib" module, just like "typing.get_type_hints" would.
module_annotations = annotationlib.call_annotate_function(
    sys.modules[__name__].__annotate__,
    annotationlib.Format.FORWARDREF,
)
print("Module annotations:", displayDict(module_annotations))

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
