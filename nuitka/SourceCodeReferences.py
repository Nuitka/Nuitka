#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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

class SourceCodeReference:
    @classmethod
    def fromFilenameAndLine(cls, filename, line, future_spec):
        result = cls()

        result.filename = filename
        result.line = line
        result.future_spec = future_spec

        return result

    def __init__(self):
        self.line = None
        self.filename = None
        self.future_spec = None

        self.set_line = True

    def __repr__(self):
        return "<%s to %s:%s>" % (self.__class__.__name__, self.filename, self.line)

    def clone(self, line):
        result = SourceCodeReference.fromFilenameAndLine(
            filename    = self.filename,
            line        = line,
            future_spec = self.future_spec
        )

        result.set_line = self.set_line

        return result

    def atLineNumber(self, line):
        assert int(line) == line

        return self.clone(line)

    def getLineNumber(self):
        return self.line

    def getFilename(self):
        return self.filename

    def getFutureSpec(self):
        return self.future_spec

    def getAsString(self):
        return "%s:%s" % (self.filename, self.line)

    def shallSetCurrentLine(self):
        return self.set_line

    def __cmp__(self, other):
        if other is None:
            return -1

        assert isinstance(other, SourceCodeReference), other

        result = cmp(self.filename, other.filename)

        if result == 0:
            result = cmp(self.line, other.line)

        return result

    def atInternal(self):
        if self.set_line:
            result = self.clone(self.line)
            result.set_line = False

            return result
        else:
            return self


def fromFilename(filename, future_spec):
    return SourceCodeReference.fromFilenameAndLine(
        filename    = filename,
        line        = 1,
        future_spec = future_spec,
    )
