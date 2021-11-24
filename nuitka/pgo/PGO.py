#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
"""Python level PGO handling in Nuitka."""

import os
import struct

from nuitka.__past__ import xrange
from nuitka.Tracing import pgo_logger

_pgo_strings = None

_module_entries = {}
_module_exits = {}


def _readCString(input_file):
    return b"".join(iter(lambda: input_file.read(1), b"\0"))


def _readCIntValue(input_file):
    return struct.unpack("i", input_file.read(4))[0]


def _readStringValue(input_file):
    return _pgo_strings[_readCIntValue(input_file)]


def readPGOInputFile(input_filename):
    """Read PGO information produced by a PGO run."""

    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=global-statement
    global _pgo_strings

    with open(input_filename, "rb") as input_file:
        header = input_file.read(7)

        if header != "KAY.PGO":
            pgo_logger.sysexit(
                "Error, file '%s' is not a valid PGO input for this version of Nuitka."
                % input_filename
            )

        input_file.seek(-7, os.SEEK_END)
        header = input_file.read(7)

        if header != "YAK.PGO":
            pgo_logger.sysexit(
                "Error, file '%s' was not completed correctly." % input_filename
            )

        input_file.seek(-8 - 7, os.SEEK_END)
        count, offset = struct.unpack("ii", input_file.read(8))

        input_file.seek(offset, os.SEEK_SET)

        _pgo_strings = [None] * count

        for i in xrange(count):
            _pgo_strings[i] = _readCString(input_file)

        input_file.seek(7, os.SEEK_SET)

        while True:
            # Which probe is it.
            probe_name = _readStringValue(input_file)

            if probe_name == "ModuleEnter":
                module_name = _readStringValue(input_file)
                arg = _readCIntValue(input_file)

                _module_entries[module_name] = arg
            elif probe_name == "ModuleExit":
                module_name = _readStringValue(input_file)
                had_error = _readCIntValue(input_file) != 0

                _module_exits[module_name] = had_error
            elif probe_name == "END":
                break
