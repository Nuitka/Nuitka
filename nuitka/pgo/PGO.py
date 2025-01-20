#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Python level PGO handling in Nuitka."""

import os
import struct

from nuitka.__past__ import xrange
from nuitka.Options import getPythonPgoUnseenModulePolicy
from nuitka.Tracing import pgo_logger

_pgo_active = False

_pgo_strings = None

_module_entries = {}
_module_exits = {}


def _readCString(input_file):
    return b"".join(iter(lambda: input_file.read(1), b"\0"))


def _readCIntValue(input_file):
    return struct.unpack("i", input_file.read(4))[0]


def _readStringValue(input_file):
    return _pgo_strings[_readCIntValue(input_file)]


def _readModuleIdentifierValue(input_file):
    module_identifier = _readStringValue(input_file)
    if str is not bytes:
        module_identifier = module_identifier.decode("utf8")

    return module_identifier


def readPGOInputFile(input_filename):
    """Read PGO information produced by a PGO run."""

    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=global-statement
    global _pgo_strings, _pgo_active

    with open(input_filename, "rb") as input_file:
        header = input_file.read(7)

        if header != b"KAY.PGO":
            pgo_logger.sysexit(
                "Error, file '%s' is not a valid PGO input for this version of Nuitka."
                % input_filename
            )

        input_file.seek(-7, os.SEEK_END)
        header = input_file.read(7)

        if header != b"YAK.PGO":
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

            if probe_name == b"ModuleEnter":
                module_name = _readModuleIdentifierValue(input_file)
                arg = _readCIntValue(input_file)

                _module_entries[module_name] = arg
            elif probe_name == b"ModuleExit":
                module_name = _readModuleIdentifierValue(input_file)
                had_error = _readCIntValue(input_file) != 0

                _module_exits[module_name] = had_error
            elif probe_name == b"END":
                break
            else:
                pgo_logger.sysexit(
                    "Error, unknown probe '%s' encountered." % probe_name
                )

    _pgo_active = True


def decideInclusionFromPGO(module_name, module_kind):
    """Decide module inclusion based on PGO input.

    At this point, PGO can decide the inclusion to not be done. It will
    ask to include things it has seen at run time, and that won't be a
    problem, but it will ask to exclude modules not seen entered at runtime,
    the decision for bytecode is same as inclusion, but the demotion is done
    later, after first compiling it. Caching might save compile time a second
    time around once the cache is populated, but care must be taken for that
    to not cause inclusions that are not used.
    """

    # Only if we had input of course.
    if not _pgo_active:
        return None

    # At this time, we do not yet detect the loading of extension modules,
    # but of course we could and should do that.
    if module_kind == "extension":
        return None

    if module_name in _module_entries:
        return True

    unseen_module_policy = getPythonPgoUnseenModulePolicy()

    if unseen_module_policy == "exclude":
        return False
    else:
        return None


def decideCompilationFromPGO(module_name):
    # Only if we had input of course.
    if not _pgo_active:
        return None

    # TODO: Could become more complicated.
    unseen_module_policy = getPythonPgoUnseenModulePolicy()

    if module_name not in _module_entries and unseen_module_policy == "bytecode":
        return "bytecode"
    else:
        return None


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
