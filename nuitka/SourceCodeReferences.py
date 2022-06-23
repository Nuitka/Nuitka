#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.__past__ import total_ordering
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)


@total_ordering
class SourceCodeReference(object):
    __slots__ = ["filename", "line", "column"]

    @classmethod
    def fromFilenameAndLine(cls, filename, line):
        result = cls()

        result.filename = filename
        result.line = line

        return result

    if isCountingInstances():
        __del__ = counted_del()

    @counted_init
    def __init__(self):
        self.filename = None
        self.line = None
        self.column = None

    def __repr__(self):
        return "<%s to %s:%s>" % (self.__class__.__name__, self.filename, self.line)

    def __hash__(self):
        return hash((self.filename, self.line, self.column))

    def __lt__(self, other):
        # Many cases decide early, pylint: disable=too-many-return-statements
        if other is None:
            return True

        if other is self:
            return False

        assert isinstance(other, SourceCodeReference), other

        if self.filename < other.filename:
            return True
        elif self.filename > other.filename:
            return False
        else:
            if self.line < other.line:
                return True
            elif self.line > other.line:
                return False
            else:
                if self.column < other.column:
                    return True
                elif self.column > other.column:
                    return False
                else:
                    return self.isInternal() < other.isInternal()

    def __eq__(self, other):
        if other is None:
            return False

        if other is self:
            return True

        assert isinstance(other, SourceCodeReference), other

        if self.filename != other.filename:
            return False

        if self.line != other.line:
            return False

        if self.column != other.column:
            return False

        return self.isInternal() is other.isInternal()

    def _clone(self, line):
        """Make a copy it itself."""
        return self.fromFilenameAndLine(filename=self.filename, line=line)

    def atInternal(self):
        """Make a copy it itself but mark as internal code.

        Avoids useless copies, by returning an internal object again if
        it is already internal.
        """
        if not self.isInternal():
            result = self._clone(self.line)

            return result
        else:
            return self

    def atLineNumber(self, line):
        """Make a reference to the same file, but different line.

        Avoids useless copies, by returning same object if the line is
        the same.
        """

        assert type(line) is int, line

        if self.line != line:
            return self._clone(line)
        else:
            return self

    def atColumnNumber(self, column):
        assert type(column) is int, column

        if self.column != column:
            result = self._clone(self.line)
            result.column = column
            return result
        else:
            return self

    def getLineNumber(self):
        return self.line

    def getColumnNumber(self):
        return self.column

    def getFilename(self):
        return self.filename

    def getAsString(self):
        return "%s:%s" % (self.filename, self.line)

    @staticmethod
    def isInternal():
        return False


class SourceCodeReferenceInternal(SourceCodeReference):
    __slots__ = ()

    @staticmethod
    def isInternal():
        return True


def fromFilename(filename):
    return SourceCodeReference.fromFilenameAndLine(filename=filename, line=1)
