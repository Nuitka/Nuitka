#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Blob codes for storing binary data semi-efficiently.

This module offers means to store and encode binary blobs in C++ semi
efficiently. The "StreamData" class is used in two places, for constants
and for freezing of bytecode.
"""

class StreamData:
    def __init__(self, identifier):
        self.stream_data = bytes()
        self.identifier = identifier

    def getStreamDataCode(self, value, fixed_size = False):
        offset = self.stream_data.find(value)
        if offset == -1:
            offset = len(self.stream_data)
            self.stream_data += value

        if fixed_size:
            return "&%s[ %d ]" % (
                self.identifier,
                offset
            )
        else:
            return "&%s[ %d ], %d" % (
                self.identifier,
                offset,
                len(value)
            )

    def getBytes(self):
        return self.stream_data
