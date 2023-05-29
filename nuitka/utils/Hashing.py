#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Module for working with hashes in Nuitka.

Offers support for hashing incrementally and files esp. without having
to read their contents.
"""

import hashlib
from binascii import crc32

from nuitka.__past__ import unicode

from .FileOperations import openTextFile


class HashBase(object):
    __slots__ = ("hash",)

    def updateFromValues(self, *values):
        for value in values:
            if type(value) is int:
                value = str(int)

            if type(value) in (str, unicode):
                if str is not bytes:
                    value = value.encode("utf8")

                self.updateFromBytes(value)
            elif type(value) is bytes:
                self.updateFromBytes(value)
            else:
                assert False, type(value)

    def updateFromFile(self, filename):
        # TODO: Read in chunks
        with openTextFile(filename, "rb") as input_file:
            self.updateFromFileHandle(input_file)

    def updateFromFileHandle(self, file_handle):
        while 1:
            chunk = file_handle.read(1024 * 64)

            if not chunk:
                break

            self.updateFromBytes(chunk)


class Hash(HashBase):
    def __init__(self):
        self.hash = hashlib.md5()

    def updateFromBytes(self, value):
        self.hash.update(value)

    def asDigest(self):
        return self.hash.digest()

    def asHexDigest(self):
        return self.hash.hexdigest()


def getFileContentsHash(filename, as_string=True):
    result = Hash()
    result.updateFromFile(filename=filename)

    if as_string:
        return result.asHexDigest()
    else:
        return result.asDigest()


def getStringHash(value):
    result = Hash()
    result.updateFromValues(value)

    return result.asHexDigest()


def getHashFromValues(*values):
    result = Hash()
    result.updateFromValues(*values)

    return result.asHexDigest()


class HashCRC32(HashBase):
    def __init__(self):
        self.hash = 0

    def updateFromBytes(self, value):
        self.hash = crc32(value, self.hash)

    def asDigest(self):
        return self.hash
