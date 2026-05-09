#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Shared constants blob format specification handling."""

import os
import re

from nuitka.__past__ import to_byte
from nuitka.utils.FileOperations import getFileContents, getNormalizedPathJoin

_define_pattern = re.compile(
    r"^\s*#define\s+(NUITKA_CONSTANT_BLOB_[A-Z0-9_]+)\s+([0-9A-Fa-fxXuUlL]+)\b"
)

_tag_define_names = (
    ("previous", "NUITKA_CONSTANT_BLOB_TAG_PREVIOUS"),
    ("none", "NUITKA_CONSTANT_BLOB_TAG_NONE"),
    ("true", "NUITKA_CONSTANT_BLOB_TAG_TRUE"),
    ("false", "NUITKA_CONSTANT_BLOB_TAG_FALSE"),
    ("tuple", "NUITKA_CONSTANT_BLOB_TAG_TUPLE"),
    ("list", "NUITKA_CONSTANT_BLOB_TAG_LIST"),
    ("dict", "NUITKA_CONSTANT_BLOB_TAG_DICT"),
    ("set", "NUITKA_CONSTANT_BLOB_TAG_SET"),
    ("frozenset", "NUITKA_CONSTANT_BLOB_TAG_FROZENSET"),
    ("long_positive_small", "NUITKA_CONSTANT_BLOB_TAG_LONG_POSITIVE_SMALL"),
    ("long_negative_small", "NUITKA_CONSTANT_BLOB_TAG_LONG_NEGATIVE_SMALL"),
    ("long_positive_large", "NUITKA_CONSTANT_BLOB_TAG_LONG_POSITIVE_LARGE"),
    ("long_negative_large", "NUITKA_CONSTANT_BLOB_TAG_LONG_NEGATIVE_LARGE"),
    ("int_positive", "NUITKA_CONSTANT_BLOB_TAG_INT_POSITIVE"),
    ("int_negative", "NUITKA_CONSTANT_BLOB_TAG_INT_NEGATIVE"),
    ("float_special", "NUITKA_CONSTANT_BLOB_TAG_FLOAT_SPECIAL"),
    ("float", "NUITKA_CONSTANT_BLOB_TAG_FLOAT"),
    ("text_empty", "NUITKA_CONSTANT_BLOB_TAG_TEXT_EMPTY"),
    ("text_single", "NUITKA_CONSTANT_BLOB_TAG_TEXT_SINGLE"),
    (
        "text_utf8_length_prefixed",
        "NUITKA_CONSTANT_BLOB_TAG_TEXT_UTF8_LENGTH_PREFIXED",
    ),
    (
        "text_utf8_zero_terminated",
        "NUITKA_CONSTANT_BLOB_TAG_TEXT_UTF8_ZERO_TERMINATED",
    ),
    ("attribute_name", "NUITKA_CONSTANT_BLOB_TAG_ATTRIBUTE_NAME"),
    ("bytes_length_prefixed", "NUITKA_CONSTANT_BLOB_TAG_BYTES_LENGTH_PREFIXED"),
    ("bytes_zero_terminated", "NUITKA_CONSTANT_BLOB_TAG_BYTES_ZERO_TERMINATED"),
    ("bytes_single", "NUITKA_CONSTANT_BLOB_TAG_BYTES_SINGLE"),
    ("slice", "NUITKA_CONSTANT_BLOB_TAG_SLICE"),
    ("range", "NUITKA_CONSTANT_BLOB_TAG_RANGE"),
    ("complex_special", "NUITKA_CONSTANT_BLOB_TAG_COMPLEX_SPECIAL"),
    ("complex", "NUITKA_CONSTANT_BLOB_TAG_COMPLEX"),
    ("bytearray", "NUITKA_CONSTANT_BLOB_TAG_BYTEARRAY"),
    ("builtin_anon", "NUITKA_CONSTANT_BLOB_TAG_BUILTIN_ANON"),
    ("builtin_special", "NUITKA_CONSTANT_BLOB_TAG_BUILTIN_SPECIAL"),
    ("blob_data", "NUITKA_CONSTANT_BLOB_TAG_BLOB_DATA"),
    ("generic_alias", "NUITKA_CONSTANT_BLOB_TAG_GENERIC_ALIAS"),
    ("union_type", "NUITKA_CONSTANT_BLOB_TAG_UNION_TYPE"),
    ("builtin_named", "NUITKA_CONSTANT_BLOB_TAG_BUILTIN_NAMED"),
    ("builtin_exception", "NUITKA_CONSTANT_BLOB_TAG_BUILTIN_EXCEPTION"),
    ("code_object", "NUITKA_CONSTANT_BLOB_TAG_CODE_OBJECT"),
    ("end", "NUITKA_CONSTANT_BLOB_TAG_END"),
)

_float_special_define_names = (
    ("pos_zero", "NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_POS_ZERO"),
    ("neg_zero", "NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_NEG_ZERO"),
    ("pos_nan", "NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_POS_NAN"),
    ("neg_nan", "NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_NEG_NAN"),
    ("pos_inf", "NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_POS_INF"),
    ("neg_inf", "NUITKA_CONSTANT_BLOB_FLOAT_SPECIAL_NEG_INF"),
)

_code_flag_define_names = (
    ("code_flag_qualname", "NUITKA_CONSTANT_BLOB_CODE_FLAG_QUALNAME"),
    ("code_flag_free_vars", "NUITKA_CONSTANT_BLOB_CODE_FLAG_FREE_VARS"),
    ("code_flag_kw_only", "NUITKA_CONSTANT_BLOB_CODE_FLAG_KW_ONLY"),
    ("code_flag_pos_only", "NUITKA_CONSTANT_BLOB_CODE_FLAG_POS_ONLY"),
    ("code_flag_optimized", "NUITKA_CONSTANT_BLOB_CODE_FLAG_OPTIMIZED"),
    ("code_flag_newlocals", "NUITKA_CONSTANT_BLOB_CODE_FLAG_NEWLOCALS"),
    ("code_flag_varargs", "NUITKA_CONSTANT_BLOB_CODE_FLAG_VARARGS"),
    ("code_flag_varkeywords", "NUITKA_CONSTANT_BLOB_CODE_FLAG_VARKEYWORDS"),
    (
        "code_flag_future_division",
        "NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_DIVISION",
    ),
    (
        "code_flag_future_unicode_literals",
        "NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_UNICODE_LITERALS",
    ),
    (
        "code_flag_future_print_function",
        "NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_PRINT_FUNCTION",
    ),
    (
        "code_flag_future_absolute_import",
        "NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_ABSOLUTE_IMPORT",
    ),
    (
        "code_flag_future_generator_stop",
        "NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_GENERATOR_STOP",
    ),
    (
        "code_flag_future_annotations",
        "NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_ANNOTATIONS",
    ),
    (
        "code_flag_future_barry_as_bdfl",
        "NUITKA_CONSTANT_BLOB_CODE_FLAG_FUTURE_BARRY_AS_BDFL",
    ),
)

_code_kind_define_names = (
    ("code_kind_mask", "NUITKA_CONSTANT_BLOB_CODE_KIND_MASK"),
    ("code_kind_generator", "NUITKA_CONSTANT_BLOB_CODE_KIND_GENERATOR"),
    ("code_kind_coroutine", "NUITKA_CONSTANT_BLOB_CODE_KIND_COROUTINE"),
    ("code_kind_asyncgen", "NUITKA_CONSTANT_BLOB_CODE_KIND_ASYNCGEN"),
)

_required_define_names = (
    ("tags", _tag_define_names),
    ("float_specials", _float_special_define_names),
    ("code_flags", _code_flag_define_names),
    ("code_kinds", _code_kind_define_names),
)

_constant_blob_spec_cache = {}


class _ConstantBlobSpec(object):
    def __init__(self, filename, values):
        self.filename = filename

        for field_name, define_name in _tag_define_names:
            setattr(self, "tag_" + field_name, to_byte(values[define_name]))

        for field_name, define_name in _float_special_define_names:
            setattr(self, "float_special_" + field_name, values[define_name])

        for field_name, define_name in _code_flag_define_names:
            setattr(self, field_name, values[define_name])

        for field_name, define_name in _code_kind_define_names:
            setattr(self, field_name, values[define_name])


def _getDefaultConstantBlobSpecFilename():
    return getNormalizedPathJoin(
        os.path.dirname(__file__), "include", "nuitka", "constants_blob_spec.h"
    )


def _getActiveConstantBlobSpecFilename():
    filename = os.getenv("NUITKA_CONSTANTS_BLOB_HEADER")

    if filename is None:
        filename = _getDefaultConstantBlobSpecFilename()

    return os.path.normpath(os.path.abspath(filename))


def _parseConstantBlobSpecValue(value):
    value = value.rstrip("uUlL")

    return int(value, 0)


def _isIgnorableConstantBlobSpecLine(line):
    line = line.strip()

    if not line:
        return True

    if line in (
        "#ifndef __NUITKA_CONSTANTS_BLOB_SPEC_H__",
        "#define __NUITKA_CONSTANTS_BLOB_SPEC_H__",
        "#endif",
    ):
        return True

    if (
        line.startswith("//")
        or line.startswith("/*")
        or line.startswith("*")
        or line == "*/"
    ):
        return True

    return False


def _loadConstantBlobSpecValues(filename, logger):
    result = {}

    for count, line in enumerate(
        getFileContents(filename, encoding="ascii").splitlines(), 1
    ):
        match = _define_pattern.match(line)

        if match is None:
            if _isIgnorableConstantBlobSpecLine(line):
                continue

            return logger.sysexit(
                "Unexpected line %d in constants blob spec '%s': %r"
                % (count, filename, line)
            )

        define_name, define_value = match.groups()
        result[define_name] = _parseConstantBlobSpecValue(define_value)

    return result


def _checkRequiredConstantBlobSpecValues(filename, values, logger):
    missing = []

    for _kind, define_names in _required_define_names:
        if type(define_names) is tuple:
            for _field_name, define_name in define_names:
                if define_name not in values:
                    missing.append(define_name)
        elif define_names not in values:
            missing.append(define_names)

    if missing:
        return logger.sysexit(
            "Missing constants blob spec values in '%s': %s"
            % (filename, ", ".join(sorted(missing)))
        )


def _checkConstantBlobTagValues(filename, values, logger):
    used_tag_values = set()

    for _field_name, define_name in _tag_define_names:
        tag_value = values[define_name]

        if tag_value <= 0 or tag_value >= 256:
            return logger.sysexit(
                "Invalid constants blob tag value in '%s' for %s: %r"
                % (filename, define_name, tag_value)
            )

        if tag_value in used_tag_values:
            return logger.sysexit(
                "Duplicate constants blob tag value in '%s' for %s: %r"
                % (filename, define_name, tag_value)
            )

        used_tag_values.add(tag_value)


def _checkConstantBlobFloatSpecialValues(filename, values, logger):
    used_float_special_values = set()

    for _field_name, define_name in _float_special_define_names:
        special_value = values[define_name]

        if special_value < 0 or special_value >= 256:
            return logger.sysexit(
                "Invalid float special value in '%s' for %s: %r"
                % (filename, define_name, special_value)
            )

        if special_value in used_float_special_values:
            return logger.sysexit(
                "Duplicate float special value in '%s' for %s: %r"
                % (filename, define_name, special_value)
            )

        used_float_special_values.add(special_value)


def _checkConstantBlobSingleCodeFlagValues(filename, values, logger):
    used_code_flag_values = 0

    for _field_name, define_name in _code_flag_define_names:
        code_flag_value = values[define_name]

        if code_flag_value <= 0 or code_flag_value >= (1 << 64):
            return logger.sysexit(
                "Invalid code flag value in '%s' for %s: %r"
                % (filename, define_name, code_flag_value)
            )

        if code_flag_value & (code_flag_value - 1):
            return logger.sysexit(
                "Non-bitmask code flag value in '%s' for %s: %r"
                % (filename, define_name, code_flag_value)
            )

        if used_code_flag_values & code_flag_value:
            return logger.sysexit(
                "Duplicate code flag value in '%s' for %s: %r"
                % (filename, define_name, code_flag_value)
            )

        used_code_flag_values |= code_flag_value

    return used_code_flag_values


def _checkConstantBlobCodeKindValues(filename, values, used_code_flag_values, logger):
    code_kind_mask = values["NUITKA_CONSTANT_BLOB_CODE_KIND_MASK"]

    if code_kind_mask <= 0 or code_kind_mask >= (1 << 64):
        return logger.sysexit(
            "Invalid code kind mask in '%s': %r" % (filename, code_kind_mask)
        )

    if used_code_flag_values & code_kind_mask:
        return logger.sysexit("Overlapping code flag values in '%s'" % filename)

    used_code_kind_values = set()

    for _field_name, define_name in _code_kind_define_names[1:]:
        code_kind_value = values[define_name]

        if code_kind_value <= 0 or code_kind_value >= (1 << 64):
            return logger.sysexit(
                "Invalid code kind value in '%s' for %s: %r"
                % (filename, define_name, code_kind_value)
            )

        if code_kind_value & ~code_kind_mask:
            return logger.sysexit(
                "Code kind value outside mask in '%s' for %s: %r"
                % (filename, define_name, code_kind_value)
            )

        if code_kind_value in used_code_kind_values:
            return logger.sysexit(
                "Duplicate code kind value in '%s' for %s: %r"
                % (filename, define_name, code_kind_value)
            )

        used_code_kind_values.add(code_kind_value)


def _checkConstantBlobCodeFlagValues(filename, values, logger):
    used_code_flag_values = _checkConstantBlobSingleCodeFlagValues(
        filename=filename, values=values, logger=logger
    )

    _checkConstantBlobCodeKindValues(
        filename=filename,
        values=values,
        used_code_flag_values=used_code_flag_values,
        logger=logger,
    )


def _checkConstantBlobSpecValues(filename, values, logger):
    _checkRequiredConstantBlobSpecValues(
        filename=filename, values=values, logger=logger
    )
    _checkConstantBlobTagValues(filename=filename, values=values, logger=logger)
    _checkConstantBlobFloatSpecialValues(
        filename=filename, values=values, logger=logger
    )
    _checkConstantBlobCodeFlagValues(filename=filename, values=values, logger=logger)


def loadConstantBlobSpec(logger):
    filename = _getActiveConstantBlobSpecFilename()

    result = _constant_blob_spec_cache.get(filename)

    if result is None:
        values = _loadConstantBlobSpecValues(filename, logger)

        _checkConstantBlobSpecValues(filename, values, logger)

        result = _ConstantBlobSpec(filename=filename, values=values)
        _constant_blob_spec_cache[filename] = result

    return result


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
