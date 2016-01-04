#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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
""" Source code reference record.

All the information to lookup line and file of a code location, together with
the future flags in use there.
"""

from nuitka.nodes.FutureSpecs import FutureSpec
from nuitka.utils.InstanceCounters import counted_del, counted_init


class SourceCodeReference(object):
    # TODO: Measure the access speed impact of slots. The memory savings is
    # not worth it (only a few percent).
    __slots__ = ["filename", "line", "future_spec", "internal"]

    @classmethod
    def fromFilenameAndLine(cls, filename, line, future_spec):
        result = cls()

        result.filename = filename
        result.line = line
        result.future_spec = future_spec

        return result

    __del__ = counted_del()

    @counted_init
    def __init__(self):
        self.line = None
        self.filename = None
        self.future_spec = None
        self.internal = False

    def __repr__(self):
        return "<%s to %s:%s>" % (self.__class__.__name__, self.filename, self.line)

    def __cmp__(self, other):
        if other is None:
            return -1

        assert isinstance(other, SourceCodeReference), other

        result = cmp(self.filename, other.filename)

        if result == 0:
            result = cmp(self.line, other.line)

        if result == 0:
            result = cmp(self.internal, other.internal)

        return result

    def _clone(self, line):
        """ Make a copy it itself.

        """
        result = SourceCodeReference.fromFilenameAndLine(
            filename    = self.filename,
            line        = line,
            future_spec = self.future_spec
        )

        result.internal = self.internal

        return result

    def atInternal(self):
        """ Make a copy it itself but mark as internal code.

            Avoids useless copies, by returning an internal object again if
            it is already internal.
        """
        if not self.internal:
            result = self._clone(self.line)
            result.internal = True

            return result
        else:
            return self


    def atLineNumber(self, line):
        """ Make a reference to the same file, but different line.

            Avoids useless copies, by returning same object if the line is
            the same.
        """

        assert type(line) is int, line

        if self.line != line:
            return self._clone(line)
        else:
            return self

    def getLineNumber(self):
        return self.line

    def getFilename(self):
        return self.filename

    def getFutureSpec(self):
        return self.future_spec

    def getAsString(self):
        return "%s:%s" % (self.filename, self.line)

    def isInternal(self):
        return self.internal


def fromFilename(filename):
    return SourceCodeReference.fromFilenameAndLine(
        filename    = filename,
        line        = 1,
        future_spec = FutureSpec(),
    )
