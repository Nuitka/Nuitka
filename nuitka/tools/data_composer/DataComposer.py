#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Data composer, crunch constants into binary blobs to load. """

import binascii
import os
import re
import struct
import sys
from math import copysign, isinf, isnan

from nuitka.__past__ import BytesIO, long, to_byte, unicode, xrange
from nuitka.build.DataComposerInterface import deriveModuleConstantsBlobName
from nuitka.Builtins import builtin_exception_values_list, builtin_named_values
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.PythonVersions import python_version
from nuitka.Serialization import (
    BlobData,
    BuiltinAnonValue,
    BuiltinGenericAliasValue,
    BuiltinSpecialValue,
    BuiltinUnionTypeValue,
    ConstantStreamReader,
)
from nuitka.Tracing import data_composer_logger
from nuitka.utils.FileOperations import getFileSize, listDir, syncFileOutput
from nuitka.utils.Json import writeJsonToFilename

_max_uint64_t_value = 2**64 - 1
_max_uint31_t_value = 2**31 - 1


def _encodeVariableLength(value):
    """Get the variable length size encoding of a uint64_t value."""

    assert 0 <= value <= _max_uint64_t_value

    result = b""

    while value >= 128:
        # Need to take the last seven bits as a byte value
        result += to_byte((value & 255) | 128)
        value >>= 7

    # Last byte or whole value small enough.
    return result + to_byte(value)


def scanConstFiles(build_dir):
    result = []

    for fullpath, filename in listDir(build_dir):
        if not filename.endswith(".const"):
            continue

        result.append((fullpath, filename))

    return result


# TODO: The determination of this should already happen in Building or in a
# helper not during code generation.
_match_attribute_names = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*$")


def _isAttributeName(value):
    # TODO: The exception is to make sure we intern the ".0" argument name
    # used for generator expressions, iterator value.
    return _match_attribute_names.match(value) or value == ".0"


_last_written = None


def _writeConstantValue(output, constant_value):
    # Massively many details per value, pylint: disable=too-many-branches,too-many-statements

    # We are a singleton, pylint: disable=global-statement
    global _last_written

    constant_type = type(constant_value)

    if constant_value is None:
        output.write(b"n")
    elif constant_value is _last_written:
        output.write(b"p")
    elif constant_value is True:
        output.write(b"t")
    elif constant_value is False:
        output.write(b"F")
    elif constant_type is tuple:
        output.write(b"T" + _encodeVariableLength(len(constant_value)))

        _last_written = None

        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is list:
        output.write(b"L" + _encodeVariableLength(len(constant_value)))

        _last_written = None

        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is dict:
        output.write(b"D" + _encodeVariableLength(len(constant_value)))

        # Write keys first, and values second, such that we allow for the
        # last_written to have an impact.
        items = constant_value.items()

        _last_written = None
        for key, value in items:
            _writeConstantValue(output, key)

        _last_written = None
        for key, value in items:
            _writeConstantValue(output, value)
    elif constant_type is set:
        output.write(b"S" + _encodeVariableLength(len(constant_value)))

        _last_written = None
        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is frozenset:
        output.write(b"P" + _encodeVariableLength(len(constant_value)))

        _last_written = None
        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is long:
        is_negative = constant_value < 0
        abs_constant_value = abs(constant_value)

        if abs_constant_value < _max_uint31_t_value:
            output.write(
                (b"q" if is_negative else b"l")
                + _encodeVariableLength(abs_constant_value)
            )
        else:
            output.write(b"G" if is_negative else b"g")

            parts = []

            mod_value = 2**31
            while abs_constant_value > 0:
                parts.append(abs_constant_value % mod_value)
                abs_constant_value >>= 31

            output.write(_encodeVariableLength(len(parts)))
            for part in reversed(parts):
                output.write(_encodeVariableLength(part))

    elif constant_type is int:
        is_negative = constant_value < 0
        abs_constant_value = abs(constant_value)
        # This is Python2 then.

        output.write(
            (b"I" if is_negative else b"i") + _encodeVariableLength(abs_constant_value)
        )
    elif constant_type is float:
        if constant_value == 0.0:
            if copysign(1, constant_value) == 1:
                output.write(b"Z" + to_byte(0))
            else:
                output.write(b"Z" + to_byte(1))
        elif isnan(constant_value):
            if copysign(1, constant_value) == 1:
                output.write(b"Z" + to_byte(2))
            else:
                output.write(b"Z" + to_byte(3))
        elif isinf(constant_value):
            if copysign(1, constant_value) == 1:
                output.write(b"Z" + to_byte(4))
            else:
                output.write(b"Z" + to_byte(5))
        else:
            output.write(b"f" + struct.pack("d", constant_value))
    elif constant_type is unicode:
        if str is not bytes:
            encoded = constant_value.encode("utf8", "surrogatepass")
        else:
            encoded = constant_value.encode("utf8")

        if len(encoded) == 1:
            output.write(b"w" + encoded)
        # Zero termination if possible.
        elif b"\0" in encoded:
            output.write(b"v" + _encodeVariableLength(len(encoded)))
            output.write(encoded)
        else:
            if str is not bytes and _isAttributeName(constant_value):
                indicator = b"a"
            else:
                indicator = b"u"

            output.write(indicator + encoded + b"\0")
    elif constant_type is bytes:
        if len(constant_value) == 1:
            output.write(b"d" + constant_value)
        # Zero termination if possible.
        elif b"\0" in constant_value:
            output.write(b"b" + _encodeVariableLength(len(constant_value)))
            output.write(constant_value)
        else:
            if str is bytes and _isAttributeName(constant_value):
                indicator = b"a"
            else:
                indicator = b"c"

            output.write(indicator + constant_value + b"\0")
    elif constant_type is slice:
        output.write(b":")
        _last_written = None
        _writeConstantValue(output, constant_value.start)
        _writeConstantValue(output, constant_value.stop)
        _writeConstantValue(output, constant_value.step)
    elif constant_type is range:
        output.write(b";")
        _last_written = None
        _writeConstantValue(output, constant_value.start)
        _writeConstantValue(output, constant_value.stop)
        _writeConstantValue(output, constant_value.step)
    elif constant_type is xrange:
        output.write(b";")
        _last_written = None

        range_args = [
            int(v)
            for v in str(constant_value)[7 if str is bytes else 6 : -1].split(",")
        ]

        # Default start.
        if len(range_args) == 1:
            range_args.insert(0, 0)

        # Default step
        if len(range_args) < 3:
            range_args.append(1)

        _writeConstantValue(output, range_args[0])
        _writeConstantValue(output, range_args[1])
        _writeConstantValue(output, range_args[2])
    elif constant_type is complex:
        # Some float values do not transport well, use float streaming then.
        if (
            constant_value.real == 0
            or constant_value.imag == 0
            or isnan(constant_value.real)
            or isnan(constant_value.imag)
            or isinf(constant_value.real)
            or isinf(constant_value.imag)
        ):
            output.write(b"J")

            _last_written = None
            _writeConstantValue(output, constant_value.real)
            _writeConstantValue(output, constant_value.imag)
        else:
            output.write(b"j")
            output.write(struct.pack("dd", constant_value.real, constant_value.imag))

    elif constant_type is bytearray:
        output.write(b"B" + _encodeVariableLength(len(constant_value)))

        if python_version < 0x270:
            constant_value = constant_value.decode("latin1")
        output.write(constant_value)
    elif constant_type is BuiltinAnonValue:
        output.write(b"M")
        output.write(constant_value.getStreamValueByte())
    elif constant_type is BuiltinSpecialValue:
        output.write(b"Q")
        output.write(constant_value.getStreamValueByte())
    elif constant_type is BlobData:
        constant_value = constant_value.getData()
        output.write(b"X")
        output.write(_encodeVariableLength(len(constant_value)))
        output.write(constant_value)
    elif constant_type is BuiltinGenericAliasValue:
        output.write(b"A")
        _last_written = None
        _writeConstantValue(output, constant_value.origin)
        _writeConstantValue(output, constant_value.args)
    elif constant_type is BuiltinUnionTypeValue:
        output.write(b"H")
        _last_written = None
        _writeConstantValue(output, constant_value.args)
    elif constant_value in builtin_named_values:
        output.write(b"O")
        output.write(builtin_named_values[constant_value].encode("utf8"))
        output.write(b"\0")
    elif constant_value in builtin_exception_values_list:
        output.write(b"E")
        output.write(constant_value.__name__.encode("utf8"))
        output.write(b"\0")
    else:
        assert False, (type(constant_value), constant_value)

    _last_written = constant_value


def _writeConstantStream(constants_reader):
    result = BytesIO()

    # We are a singleton, pylint: disable=global-statement
    global _last_written
    _last_written = None

    count = 0
    while 1:
        try:
            constant_value = constants_reader.readConstantValue()
        except EOFError:
            break

        old_size = result.tell()
        _writeConstantValue(result, constant_value)

        if not data_composer_logger.is_quiet:
            new_size = result.tell()

            result.seek(old_size)
            type_char = result.read(1)
            result.seek(new_size)

            data_composer_logger.info(
                "Size of constant %r is %d with type %r"
                % (constant_value, new_size - old_size, type_char)
            )

        count += 1

    # Dirty end of things marker that would trigger an assertion in the decoder.
    # TODO: Debug mode only?
    result.write(b".")

    return count, struct.pack("H", count) + result.getvalue()


crc32 = 0


def _writeConstantsBlob(output_filename, desc):
    global crc32  # singleton, pylint: disable=global-statement

    with open(output_filename, "w+b") as output:
        output.write(b"\0" * 8)

        def write(data):
            global crc32  # singleton, pylint: disable=global-statement

            output.write(data)
            crc32 = binascii.crc32(data, crc32)

        for name, part in desc:
            write(name + b"\0")
            write(struct.pack("I", len(part)))
            write(part)

        data_size = output.tell() - 8

        if str is bytes:
            # Python2 is doing signed CRC32, but we want unsigned.
            crc32 %= 1 << 32

        output.seek(0)
        output.write(struct.pack("II", crc32, data_size))

        assert output.tell() == 8

        data_composer_logger.info(
            "Total constants blob size without header %d." % data_size
        )
        data_composer_logger.info("Total constants blob CRC32 is %d." % crc32)

        syncFileOutput(output)


def main():
    # many details, mostly needed for reporting: pylint: disable=too-many-locals

    data_composer_logger.is_quiet = (
        os.getenv("NUITKA_DATA_COMPOSER_VERBOSE", "0") != "1"
    )

    # Internal tool, most simple command line handling. This is the build directory
    # where main Nuitka put the .const files.
    build_dir = sys.argv[1]
    output_filename = sys.argv[2]
    stats_filename = sys.argv[3]

    # Scan file ".const" files from the build directory.
    const_files = scanConstFiles(build_dir)

    total = 0

    desc = []

    names = set()

    stats = OrderedDict()

    for fullpath, filename in const_files:
        data_composer_logger.info("Working on constant file '%s'." % filename)

        try:
            with open(fullpath, "rb") as const_file:
                constants_reader = ConstantStreamReader(const_file)
                count, part = _writeConstantStream(constants_reader)
            total += count

            name = deriveModuleConstantsBlobName(filename)

            # Make sure that is not repeated.
            assert name not in names, name
            names.add(name)

            data_composer_logger.info(
                "Storing %r chunk with %s values size %r." % (name, count, len(part))
            )

            if str is not bytes:
                encoded_name = name.encode("utf8")
            else:
                encoded_name = name

            desc.append((encoded_name, part))
        except Exception:
            data_composer_logger.warning("Problem with constant file '%s'." % filename)
            raise

        stats[filename] = {
            "input_size": getFileSize(fullpath),
            "blob_name": name,
            "blob_size": len(part),
        }

    stats["total"] = total

    data_composer_logger.info("Total amount of constants is %d." % total)

    _writeConstantsBlob(output_filename=output_filename, desc=desc)

    writeJsonToFilename(stats_filename, contents=stats)

    sys.exit(0)


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
