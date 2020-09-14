#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Internal tool, assemble a constants blob for Nuitka from module constants.

"""

from __future__ import print_function

import os
import sys

# Unchanged, running from checkout, use the parent directory, the nuitka
# package ought to be there.
sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

# isort:start

import ctypes
import math
import re
import struct

from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
    BytesIO,
    long,
    to_byte,
    unicode,
    xrange,
)
from nuitka.Builtins import builtin_exception_values_list, builtin_named_values
from nuitka.constants.Serialization import (
    BlobData,
    BuiltinAnonValue,
    BuiltinSpecialValue,
    ConstantStreamReader,
)
from nuitka.PythonVersions import python_version
from nuitka.utils.FileOperations import listDir


def scanConstFiles(build_dir):
    result = []

    for fullpath, filename in listDir(build_dir):
        if not filename.endswith(".const"):
            continue

        result.append((fullpath, filename))

    return result


def _deriveConstantsBlobName(filename):
    assert filename.endswith(".const")

    basename = filename[:-6]

    if basename == "__constants":
        return b""
    elif basename == "__bytecode":
        return b".bytecode"
    else:
        # Stripe "module." prefix"
        basename = basename[7:]

        # Filenames that hit case sensitive problems, get those, but we encode that not in the binary.
        if "@" in basename:
            basename = basename.split("@")[0]

        if str is not bytes:
            basename = basename.encode("utf8")

        return basename


sizeof_clong = ctypes.sizeof(ctypes.c_long)

max_signed_long = 2 ** (sizeof_clong * 7) - 1
min_signed_long = -(2 ** (sizeof_clong * 7))

sizeof_clonglong = ctypes.sizeof(ctypes.c_longlong)

max_signed_longlong = 2 ** (sizeof_clonglong * 8 - 1) - 1
min_signed_longlong = -(2 ** (sizeof_clonglong * 8 - 1))


# TODO: The determination of this should already happen in Building or in a
# helper not during code generation.
_match_attribute_names = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*$")


def _isAttributeName(value):
    # TODO: The exception is to make sure we intern the ".0" argument name
    # used for generator expressions, iterator value.
    return _match_attribute_names.match(value) or value == ".0"


def _writeConstantValue(output, constant_value):
    # Massively many details per value, pylint: disable=too-many-branches,too-many-statements

    constant_type = type(constant_value)

    if constant_type is tuple:
        # TODO: Optimize for size of tuple to be < 256 with dedicated value
        output.write(b"T" + struct.pack("i", len(constant_value)))

        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is list:
        # TODO: Optimize for size of tuple to be < 256 with dedicated value
        output.write(b"L" + struct.pack("i", len(constant_value)))

        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is dict:
        # TODO: Optimize for size of tuple to be < 256 with dedicated value
        output.write(b"D" + struct.pack("i", len(constant_value)))

        for key, value in constant_value.items():
            _writeConstantValue(output, key)
            _writeConstantValue(output, value)
    elif constant_type is set:
        # TODO: Optimize for size of tuple to be < 256 with dedicated value
        output.write(b"S" + struct.pack("i", len(constant_value)))

        for element in constant_value:
            _writeConstantValue(output, element)
    elif constant_type is frozenset:
        # TODO: Optimize for size of tuple to be < 256 with dedicated value
        output.write(b"P" + struct.pack("i", len(constant_value)))

        for element in constant_value:
            _writeConstantValue(output, element)

    elif constant_type is long:
        if min_signed_long <= constant_value <= max_signed_long:
            output.write(b"l" + struct.pack("l", constant_value))
        elif min_signed_longlong <= constant_value <= max_signed_longlong:
            output.write(b"q" + struct.pack("q", constant_value))
        else:
            output.write(b"g")

            if constant_value < 0:
                constant_value = abs(constant_value)
                output.write(b"-")
            else:
                output.write(b"+")

            parts = []

            mod_value = 2 ** (sizeof_clonglong * 8)
            while constant_value > 0:
                parts.append(constant_value % mod_value)
                constant_value >>= sizeof_clonglong * 8

            output.write(struct.pack("i", len(parts)))
            for part in reversed(parts):
                output.write(struct.pack("Q", part))

    elif constant_type is int:
        # This is Python2 then. TODO: Special case smaller values.
        output.write(b"i" + struct.pack("l", constant_value))
    elif constant_type is float:
        if constant_value == 0.0 and math.copysign(1, constant_value) == 1:
            output.write(b"Z" + to_byte(0))
        elif math.isnan(constant_value):
            if math.copysign(1, constant_value) == 1:
                output.write(b"Z" + to_byte(1))
            else:
                output.write(b"Z" + to_byte(2))
        elif math.isinf(constant_value):
            if math.copysign(1, constant_value) == 1:
                output.write(b"Z" + to_byte(3))
            else:
                output.write(b"Z" + to_byte(4))
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
        _writeConstantValue(output, constant_value.start)
        _writeConstantValue(output, constant_value.stop)
        _writeConstantValue(output, constant_value.step)
    elif constant_type is range:
        output.write(b";")
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

        output.write(struct.pack("iii", *range_args))
    elif constant_value is None:
        output.write(b"n")
    elif constant_value is True:
        output.write(b"t")
    elif constant_value is False:
        output.write(b"F")
    elif constant_type is complex:
        output.write(b"j")
        output.write(struct.pack("dd", constant_value.real, constant_value.imag))
    elif constant_type is bytearray:
        output.write(b"B" + struct.pack("i", len(constant_value)))

        if python_version < 270:
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


def _writeConstantStream(constants_reader):
    result = BytesIO()

    count = 0
    while 1:
        try:
            constant_value = constants_reader.readConstantValue()
        except EOFError:
            break

        _writeConstantValue(result, constant_value)
        count += 1

    # Dirty end of things marker.
    result.write(b".")

    return count, result.getvalue()


def main():
    # Internal tool, most simple command line handling. This is the build directory
    # where main Nuitka put the .const files.
    build_dir = sys.argv[1]
    output_filename = sys.argv[2]

    const_files = scanConstFiles(build_dir)

    total = 0

    desc = []

    for fullpath, filename in const_files:
        # print("Working on", filename)

        constants_reader = ConstantStreamReader(fullpath)
        name = _deriveConstantsBlobName(filename)

        # print("W", filename, name)

        count, part = _writeConstantStream(constants_reader)
        total += count

        desc.append((name, part))

    with open(output_filename, "wb") as output:
        for name, part in desc:
            output.write(name)
            output.write(b"\0")
            output.write(struct.pack("i", len(part)))
            output.write(part)

    sys.exit(0)


if __name__ == "__main__":
    main()
