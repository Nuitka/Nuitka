#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Module for working with hashes in Nuitka.

Offers support for hashing incrementally and files esp. without having
to read their contents.
"""

import struct
from binascii import crc32

from nuitka.__past__ import md5, unicode
from nuitka.containers.OrderedDicts import OrderedDict


class HashBase(object):
    __slots__ = ("hash",)

    def updateFromValues(self, *values):
        for value in values:
            if type(value) is int:
                value = str(value)

            if type(value) in (str, unicode):
                if str is not bytes:
                    value = value.encode("utf8")

                self.updateFromBytes(value)
            elif type(value) is bytes:
                self.updateFromBytes(value)
            elif type(value) in (dict, OrderedDict):
                self.updateFromBytes(b"dict")
                self.updateFromValues(*list(value.items()))
            elif type(value) is tuple:
                self.updateFromBytes(b"tuple")
                self.updateFromValues(*value)
            elif type(value) is list:
                self.updateFromBytes(b"list")
                self.updateFromValues(*value)
            elif value is None:
                self.updateFromBytes(b"none")
            else:
                assert False, type(value)

    def updateFromFile(self, filename, line_filter=None):
        from .FileOperations import openTextFile

        with openTextFile(filename, "rb") as input_file:
            self.updateFromFileHandle(input_file, line_filter=line_filter)

    def updateFromFileHandle(self, file_handle, line_filter=None):
        if line_filter is None:
            while 1:
                chunk = file_handle.read(1024 * 1024)

                if not chunk:
                    break

                self.updateFromBytes(chunk)
        else:
            for line in file_handle:
                line = line_filter(line)

                if line is not None:
                    self.updateFromBytes(line)


class Hash(HashBase):
    def __init__(self):
        self.hash = md5()

    def updateFromBytes(self, value):
        self.hash.update(value)

    def asDigest(self):
        return self.hash.digest()

    def asHexDigest(self):
        return self.hash.hexdigest()


def getStringHash(value, as_string=True):
    result = Hash()
    result.updateFromValues(value)

    if as_string:
        return result.asHexDigest()
    else:
        return result.asDigest()


def getHashFromValues(*values):
    result = Hash()
    result.updateFromValues(*values)

    return result.asHexDigest()


class HashAlgorithmBase(HashBase):
    __slots__ = ("hash_func",)

    def __init__(self, hash_func):
        self.hash = 0
        self.hash_func = hash_func

    def updateFromBytes(self, value):
        self.hash = self.hash_func(value, self.hash)

    def asDigest(self):
        if self.hash < 0:
            return struct.unpack("I", struct.pack("i", self.hash))[0]

        return self.hash

    if str is bytes:
        # For Python2, we need to remove the 'L' suffix.
        def asHexDigest(self):
            return hex(self.asDigest())[2:].rstrip("L")

    else:

        def asHexDigest(self):
            return hex(self.asDigest())[2:]


class HashCRC32(HashAlgorithmBase):
    def __init__(self):
        HashAlgorithmBase.__init__(self, crc32)


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
