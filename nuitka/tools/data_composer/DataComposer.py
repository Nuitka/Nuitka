#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Data composer, crunch constants into binary blobs to load."""

import os
import re
import struct
import sys
from math import copysign, isinf, isnan

from nuitka.__past__ import BytesIO, long, to_byte, unicode, xrange
from nuitka.build.ConstantBlobFormat import loadConstantBlobSpec
from nuitka.build.DataComposerInterface import deriveModuleConstantsBlobName
from nuitka.Builtins import builtin_exception_values_list, builtin_named_values
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.nodes.CodeObjectSpecs import CodeObjectSpec
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


def _writeConstantValue(output, constant_value, blob_spec):
    # Massively many details per value,
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    # We are a singleton, pylint: disable=global-statement
    global _last_written

    constant_type = type(constant_value)

    if constant_value is None:
        output.write(blob_spec.tag_none)
    elif constant_value is _last_written:
        output.write(blob_spec.tag_previous)
    elif constant_value is True:
        output.write(blob_spec.tag_true)
    elif constant_value is False:
        output.write(blob_spec.tag_false)
    elif constant_type is tuple:
        output.write(blob_spec.tag_tuple + _encodeVariableLength(len(constant_value)))

        _last_written = None

        for element in constant_value:
            _writeConstantValue(output, element, blob_spec)
    elif constant_type is list:
        output.write(blob_spec.tag_list + _encodeVariableLength(len(constant_value)))

        _last_written = None

        for element in constant_value:
            _writeConstantValue(output, element, blob_spec)
    elif constant_type is dict:
        output.write(blob_spec.tag_dict + _encodeVariableLength(len(constant_value)))

        # Write keys first, and values second, such that we allow for the
        # last_written to have an impact.
        items = constant_value.items()

        _last_written = None
        for key, value in items:
            _writeConstantValue(output, key, blob_spec)

        _last_written = None
        for key, value in items:
            _writeConstantValue(output, value, blob_spec)
    elif constant_type is set:
        output.write(blob_spec.tag_set + _encodeVariableLength(len(constant_value)))

        _last_written = None
        for element in constant_value:
            _writeConstantValue(output, element, blob_spec)
    elif constant_type is frozenset:
        output.write(
            blob_spec.tag_frozenset + _encodeVariableLength(len(constant_value))
        )

        _last_written = None
        for element in constant_value:
            _writeConstantValue(output, element, blob_spec)
    elif constant_type is long:
        is_negative = constant_value < 0
        abs_constant_value = abs(constant_value)

        if abs_constant_value < _max_uint31_t_value:
            output.write(
                (
                    blob_spec.tag_long_negative_small
                    if is_negative
                    else blob_spec.tag_long_positive_small
                )
                + _encodeVariableLength(abs_constant_value)
            )
        else:
            output.write(
                blob_spec.tag_long_negative_large
                if is_negative
                else blob_spec.tag_long_positive_large
            )

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
            (blob_spec.tag_int_negative if is_negative else blob_spec.tag_int_positive)
            + _encodeVariableLength(abs_constant_value)
        )
    elif constant_type is float:
        if constant_value == 0.0:
            if copysign(1, constant_value) == 1:
                output.write(
                    blob_spec.tag_float_special
                    + to_byte(blob_spec.float_special_pos_zero)
                )
            else:
                output.write(
                    blob_spec.tag_float_special
                    + to_byte(blob_spec.float_special_neg_zero)
                )
        elif isnan(constant_value):
            if copysign(1, constant_value) == 1:
                output.write(
                    blob_spec.tag_float_special
                    + to_byte(blob_spec.float_special_pos_nan)
                )
            else:
                output.write(
                    blob_spec.tag_float_special
                    + to_byte(blob_spec.float_special_neg_nan)
                )
        elif isinf(constant_value):
            if copysign(1, constant_value) == 1:
                output.write(
                    blob_spec.tag_float_special
                    + to_byte(blob_spec.float_special_pos_inf)
                )
            else:
                output.write(
                    blob_spec.tag_float_special
                    + to_byte(blob_spec.float_special_neg_inf)
                )
        else:
            output.write(blob_spec.tag_float + struct.pack("d", constant_value))
    elif constant_type is unicode:
        if str is not bytes:
            # spell-checker: ignore surrogatepass
            encoded = constant_value.encode("utf8", "surrogatepass")
        else:
            encoded = constant_value.encode("utf8")

        encoded_len = len(encoded)
        if not encoded_len:
            output.write(blob_spec.tag_text_empty)
        elif encoded_len == 1:
            output.write(blob_spec.tag_text_single + encoded)
        # Zero termination if possible.
        elif b"\0" in encoded:
            output.write(
                blob_spec.tag_text_utf8_length_prefixed
                + _encodeVariableLength(encoded_len)
            )
            output.write(encoded)
        else:
            if str is not bytes and _isAttributeName(constant_value):
                indicator = blob_spec.tag_attribute_name
            else:
                indicator = blob_spec.tag_text_utf8_zero_terminated

            output.write(indicator + encoded + b"\0")
    elif constant_type is bytes:
        if len(constant_value) == 1:
            output.write(blob_spec.tag_bytes_single + constant_value)
        # Zero termination if possible.
        elif b"\0" in constant_value:
            output.write(
                blob_spec.tag_bytes_length_prefixed
                + _encodeVariableLength(len(constant_value))
            )
            output.write(constant_value)
        else:
            if str is bytes and _isAttributeName(constant_value):
                indicator = blob_spec.tag_attribute_name
            else:
                indicator = blob_spec.tag_bytes_zero_terminated

            output.write(indicator + constant_value + b"\0")
    elif constant_type is slice:
        output.write(blob_spec.tag_slice)
        _last_written = None
        _writeConstantValue(output, constant_value.start, blob_spec)
        _writeConstantValue(output, constant_value.stop, blob_spec)
        _writeConstantValue(output, constant_value.step, blob_spec)
    elif constant_type is range:
        output.write(blob_spec.tag_range)
        _last_written = None
        _writeConstantValue(output, constant_value.start, blob_spec)
        _writeConstantValue(output, constant_value.stop, blob_spec)
        _writeConstantValue(output, constant_value.step, blob_spec)
    elif constant_type is xrange:
        output.write(blob_spec.tag_range)
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

        _writeConstantValue(output, range_args[0], blob_spec)
        _writeConstantValue(output, range_args[1], blob_spec)
        _writeConstantValue(output, range_args[2], blob_spec)
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
            output.write(blob_spec.tag_complex_special)

            _last_written = None
            _writeConstantValue(output, constant_value.real, blob_spec)
            _writeConstantValue(output, constant_value.imag, blob_spec)
        else:
            output.write(blob_spec.tag_complex)
            output.write(struct.pack("dd", constant_value.real, constant_value.imag))

    elif constant_type is bytearray:
        output.write(
            blob_spec.tag_bytearray + _encodeVariableLength(len(constant_value))
        )

        if python_version < 0x270:
            constant_value = constant_value.decode("latin1")
        output.write(constant_value)
    elif constant_type is BuiltinAnonValue:
        output.write(blob_spec.tag_builtin_anon)
        output.write(constant_value.getStreamValueByte())
    elif constant_type is BuiltinSpecialValue:
        output.write(blob_spec.tag_builtin_special)
        output.write(constant_value.getStreamValueByte())
    elif constant_type is BlobData:
        constant_value = constant_value.getData()
        output.write(blob_spec.tag_blob_data)
        output.write(_encodeVariableLength(len(constant_value)))
        output.write(constant_value)
    elif constant_type is BuiltinGenericAliasValue:
        output.write(blob_spec.tag_generic_alias)
        _last_written = None
        _writeConstantValue(output, constant_value.origin, blob_spec)
        _writeConstantValue(output, constant_value.args, blob_spec)
    elif constant_type is BuiltinUnionTypeValue:
        output.write(blob_spec.tag_union_type)
        _last_written = None
        _writeConstantValue(output, constant_value.args, blob_spec)
    elif constant_value in builtin_named_values:
        output.write(blob_spec.tag_builtin_named)
        output.write(builtin_named_values[constant_value].encode("utf8"))
        output.write(b"\0")
    elif constant_value in builtin_exception_values_list:
        output.write(blob_spec.tag_builtin_exception)
        output.write(constant_value.__name__.encode("utf8"))
        output.write(b"\0")
    elif constant_type is CodeObjectSpec:
        output.write(blob_spec.tag_code_object)
        _last_written = None

        _writeConstantValueCodeObject(output, constant_value, blob_spec)

    else:
        assert False, (type(constant_value), constant_value)

    _last_written = constant_value


def _writeConstantValueCodeObject(output, code_object, blob_spec):
    # Lots of details and optimization to deal with
    # pylint: disable=too-many-branches,too-many-statements

    # Flags for the code object, not all items will be present.
    flags = 0

    if python_version >= 0x3B0:
        if code_object.getCodeObjectQualname() != code_object.getCodeObjectName():
            assert code_object.getCodeObjectQualname().endswith(
                "." + code_object.getCodeObjectName()
            )
            flags |= blob_spec.code_flag_qualname

    if code_object.getFreeVarNames():
        flags |= blob_spec.code_flag_free_vars

    if python_version >= 0x300:
        if code_object.getKwOnlyParameterCount():
            flags |= blob_spec.code_flag_kw_only

    if python_version >= 0x380:
        if code_object.getPosOnlyParameterCount():
            flags |= blob_spec.code_flag_pos_only

    co_kind = code_object.getCodeObjectKind()

    if co_kind == "Generator":
        flags |= blob_spec.code_kind_generator
    elif co_kind == "Coroutine":
        flags |= blob_spec.code_kind_coroutine
    elif co_kind == "Asyncgen":
        flags |= blob_spec.code_kind_asyncgen

    if code_object.getFlagIsOptimizedValue():
        flags |= blob_spec.code_flag_optimized

    if code_object.getFlagNewLocalsValue():
        flags |= blob_spec.code_flag_newlocals

    if code_object.hasStarListArg():
        flags |= blob_spec.code_flag_varargs

    if code_object.hasStarDictArg():
        flags |= blob_spec.code_flag_varkeywords

    future_flags = code_object.getFutureSpec().asFlags()

    if "CO_FUTURE_DIVISION" in future_flags:
        flags |= blob_spec.code_flag_future_division

    if "CO_FUTURE_UNICODE_LITERALS" in future_flags:
        flags |= blob_spec.code_flag_future_unicode_literals

    if "CO_FUTURE_PRINT_FUNCTION" in future_flags:
        flags |= blob_spec.code_flag_future_print_function

    if "CO_FUTURE_ABSOLUTE_IMPORT" in future_flags:
        flags |= blob_spec.code_flag_future_absolute_import

    if "CO_FUTURE_GENERATOR_STOP" in future_flags:
        flags |= blob_spec.code_flag_future_generator_stop

    if "CO_FUTURE_ANNOTATIONS" in future_flags:
        flags |= blob_spec.code_flag_future_annotations

    if "CO_FUTURE_BARRY_AS_BDFL" in future_flags:
        flags |= blob_spec.code_flag_future_barry_as_bdfl

    output.write(_encodeVariableLength(flags))

    # Name is mandatory, no flag needed.
    _writeConstantValue(output, code_object.getCodeObjectName(), blob_spec)

    # Line number is mandatory, no flag needed. Encoded values start at 0,
    # where 1 is what is normally used.
    output.write(_encodeVariableLength(code_object.getLineNumber() - 1))

    # Right now this is only argument names, so argument count is implied,
    # it is mandatory so no flag is needed, empty value is very compact
    # anyway and rare.
    _writeConstantValue(output, code_object.getVarNames(), blob_spec)

    # TODO: Not sure if this is redundant potentially it can
    # be derives from the var names already.
    output.write(_encodeVariableLength(code_object.getArgumentCount()))

    # Do not include the name part in the code object, saving
    # the repetition.
    if flags & blob_spec.code_flag_qualname:
        _writeConstantValue(
            output, code_object.getCodeObjectQualname().rsplit(".")[0], blob_spec
        )

    # Free vars are optional.
    if flags & blob_spec.code_flag_free_vars:
        _writeConstantValue(output, code_object.getFreeVarNames(), blob_spec)

    # Keyword-only args are optional and version dependent.
    if flags & blob_spec.code_flag_kw_only:
        output.write(_encodeVariableLength(code_object.getKwOnlyParameterCount() - 1))

    # Positional-only args are optional and version dependent.
    if flags & blob_spec.code_flag_pos_only:
        output.write(_encodeVariableLength(code_object.getPosOnlyParameterCount() - 1))


def _writeConstantStream(constants_reader, blob_spec):
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
        _writeConstantValue(result, constant_value, blob_spec)

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
    result.write(blob_spec.tag_end)

    return count, struct.pack("H", count) + result.getvalue()


def _writeConstantsBlob(output_filename, desc):
    with open(output_filename, "wb") as output:
        for name, part in desc:
            output.write(name + b"\0")
            output.write(struct.pack("I", len(part)))
            output.write(part)

        data_size = output.tell()

        data_composer_logger.info("Total constants blob size %d." % data_size)

        syncFileOutput(output)


def main():
    # many details, mostly needed for reporting: pylint: disable=too-many-locals

    blob_spec = loadConstantBlobSpec(data_composer_logger)

    data_composer_logger.is_quiet = (
        os.getenv("NUITKA_DATA_COMPOSER_VERBOSE", "0") != "1"
    )
    data_composer_logger.info("Using constants blob spec '%s'." % blob_spec.filename)

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
                count, part = _writeConstantStream(constants_reader, blob_spec)
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
