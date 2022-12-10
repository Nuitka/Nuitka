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
"""Data composer, crunch constants into binary blobs to load. """

import binascii
import math
import os
import re
import struct
import sys

from nuitka.__past__ import (
    BytesIO,
    GenericAlias,
    long,
    to_byte,
    unicode,
    xrange,
)
from nuitka.build.DataComposerInterface import deriveModuleConstantsBlobName
from nuitka.Builtins import builtin_exception_values_list, builtin_named_values
from nuitka.constants.Serialization import (
    BlobData,
    BuiltinAnonValue,
    BuiltinSpecialValue,
    BuiltinUnionTypeValue,
    ConstantStreamReader,
)
from nuitka.PythonVersions import (
    isPythonValidCLongLongValue,
    isPythonValidCLongValue,
    python_version,
    sizeof_clonglong,
)
from nuitka.Tracing import data_composer_logger
from nuitka.utils.FileOperations import listDir


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
        # TODO: Optimize for size of tuple to be < 256 with dedicated value
        output.write(b"T" + struct.pack("i", len(constant_value)))

        _last_written = None

        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is list:
        # TODO: Optimize for size of list to be < 256 with dedicated value
        output.write(b"L" + struct.pack("i", len(constant_value)))

        _last_written = None

        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is dict:
        # TODO: Optimize for size of dict to be < 256 with dedicated value
        output.write(b"D" + struct.pack("i", len(constant_value)))

        # Write keys first, and values second, such that we allow for the
        # last_writte to have an impact.
        items = constant_value.items()

        _last_written = None
        for key, value in items:
            _writeConstantValue(output, key)

        _last_written = None
        for key, value in items:
            _writeConstantValue(output, value)
    elif constant_type is set:
        # TODO: Optimize for size of set to be < 256 with dedicated value
        output.write(b"S" + struct.pack("i", len(constant_value)))

        _last_written = None
        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is frozenset:
        # TODO: Optimize for size of set to be < 256 with dedicated value
        output.write(b"P" + struct.pack("i", len(constant_value)))

        _last_written = None
        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is long:
        if isPythonValidCLongValue(constant_value):
            output.write(b"l" + struct.pack("l", constant_value))
        elif isPythonValidCLongLongValue(constant_value):
            output.write(b"q" + struct.pack("q", constant_value))
        else:
            output.write(b"g")

            if constant_value < 0:
                abs_constant_value = abs(constant_value)
                output.write(b"-")
            else:
                abs_constant_value = constant_value
                output.write(b"+")

            parts = []

            mod_value = 2 ** (sizeof_clonglong * 8)
            while abs_constant_value > 0:
                parts.append(abs_constant_value % mod_value)
                abs_constant_value >>= sizeof_clonglong * 8

            output.write(struct.pack("i", len(parts)))
            for part in reversed(parts):
                output.write(struct.pack("Q", part))

    elif constant_type is int:
        # This is Python2 then. TODO: Special case smaller values.
        output.write(b"i" + struct.pack("l", constant_value))
    elif constant_type is float:
        if constant_value == 0.0:
            if math.copysign(1, constant_value) == 1:
                output.write(b"Z" + to_byte(0))
            else:
                output.write(b"Z" + to_byte(1))
        elif math.isnan(constant_value):
            if math.copysign(1, constant_value) == 1:
                output.write(b"Z" + to_byte(2))
            else:
                output.write(b"Z" + to_byte(3))
        elif math.isinf(constant_value):
            if math.copysign(1, constant_value) == 1:
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
            output.write(b"v" + struct.pack("i", len(encoded)))
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
            output.write(b"b" + struct.pack("i", len(constant_value)))
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

        output.write(struct.pack("lll", *range_args))
    elif constant_type is complex:
        # Some float values do not transport well, use float streaming then.
        if (
            constant_value.real == 0
            or constant_value.imag == 0
            or math.isnan(constant_value.real)
            or math.isnan(constant_value.imag)
            or math.isinf(constant_value.real)
            or math.isinf(constant_value.imag)
        ):
            output.write(b"J")

            _last_written = None
            _writeConstantValue(output, constant_value.real)
            _writeConstantValue(output, constant_value.imag)
        else:
            output.write(b"j")
            output.write(struct.pack("dd", constant_value.real, constant_value.imag))

    elif constant_type is bytearray:
        output.write(b"B" + struct.pack("i", len(constant_value)))

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
        output.write(struct.pack("i", len(constant_value)))
        output.write(constant_value)
    elif constant_type is GenericAlias:
        output.write(b"G")
        _last_written = None
        _writeConstantValue(output, constant_value.__origin__)
        _writeConstantValue(output, constant_value.__args__)
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
        assert False, constant_value

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

    return count, struct.pack("h", count) + result.getvalue()


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


def main():
    data_composer_logger.is_quiet = (
        os.environ.get("NUITKA_DATA_COMPOSER_VERBOSE", "0") != "1"
    )

    # Internal tool, most simple command line handling. This is the build directory
    # where main Nuitka put the .const files.
    build_dir = sys.argv[1]
    output_filename = sys.argv[2]

    const_files = scanConstFiles(build_dir)

    total = 0

    desc = []

    names = set()

    for fullpath, filename in const_files:
        data_composer_logger.info("Working on constant file '%s'." % filename)

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
            # Encoding needs to match generated source code output.
            name = name.encode("latin1")

        desc.append((name, part))

    data_composer_logger.info("Total amount of constants is %d." % total)

    _writeConstantsBlob(output_filename=output_filename, desc=desc)

    sys.exit(0)
