#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Node class mixins for flags and optimization state."""


class MarkUnoptimizedFunctionIndicatorMixin(object):
    """Mixin indicating a function contains 'exec' or star import and checks locals before globals."""

    # pylint: disable=assigning-non-slot
    __slots__ = ()

    def __init__(self, flags):
        self.unoptimized_locals = flags is not None and "has_exec" in flags
        self.unqualified_exec = flags is not None and "has_unqualified_exec" in flags

    def isUnoptimized(self):
        return self.unoptimized_locals

    def isUnqualifiedExec(self):
        return self.unoptimized_locals and self.unqualified_exec


class MarkNeedsAnnotationsMixin(object):
    # pylint: disable=assigning-non-slot
    __slots__ = ()

    def __init__(self):
        self.needs_annotations_dict = False

    def markAsNeedsAnnotationsDictionary(self):
        """For use during tree building only."""
        self.needs_annotations_dict = True

    def needsAnnotationsDictionary(self):
        return self.needs_annotations_dict


class EntryPointMixin(object):
    # pylint: disable=assigning-non-slot
    __slots__ = ()

    def __init__(self):
        self.trace_collection = None

    def setTraceCollection(self, trace_collection):
        previous = self.trace_collection
        self.trace_collection = trace_collection
        return previous

    def getTraceCollection(self):
        return self.trace_collection


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
