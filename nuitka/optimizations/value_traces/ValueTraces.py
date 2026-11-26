#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Value trace factories.

This creates merge traces, using the specialized classes for common
numbers of traces, and the generic class otherwise.
"""

from .ValueTracesGenerated import (
    ValueTraceMerge2,
    ValueTraceMerge3,
    ValueTraceMerge4,
    ValueTraceMerge5,
    ValueTraceMerge6,
)
from .ValueTracesStatic import ValueTraceMerge

_merge_trace_classes = {
    2: ValueTraceMerge2,
    3: ValueTraceMerge3,
    4: ValueTraceMerge4,
    5: ValueTraceMerge5,
    6: ValueTraceMerge6,
}


def makeMergeTrace(traces):
    merge_class = _merge_trace_classes.get(len(traces))

    if merge_class is None:
        return ValueTraceMerge(traces)

    return merge_class(*traces)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
