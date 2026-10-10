#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Shared PGO file format specification handling."""

import os
import re

from nuitka.__past__ import to_byte
from nuitka.utils.FileOperations import getFileContents, getNormalizedPathJoin

_define_pattern = re.compile(
    r"^\s*#define\s+(NUITKA_PGO_[A-Z0-9_]+)\s+([0-9A-Fa-fxXuUlL]+)\b"
)

_probe_define_names = (
    ("end", "NUITKA_PGO_PROBE_END"),
    ("module_enter", "NUITKA_PGO_PROBE_MODULE_ENTER"),
    ("module_exit", "NUITKA_PGO_PROBE_MODULE_EXIT"),
    ("class_prepare_result", "NUITKA_PGO_PROBE_CLASS_PREPARE_RESULT"),
    ("class_prepare_result_once", "NUITKA_PGO_PROBE_CLASS_PREPARE_RESULT_ONCE"),
    ("string_definition", "NUITKA_PGO_PROBE_STRING_DEFINITION"),
    ("key_definition", "NUITKA_PGO_PROBE_KEY_DEFINITION"),
    ("value_definition", "NUITKA_PGO_PROBE_VALUE_DEFINITION"),
)

_scope_define_names = (
    ("module", "NUITKA_PGO_SCOPE_MODULE"),
    ("class", "NUITKA_PGO_SCOPE_CLASS"),
)

_value_tag_define_names = (
    ("none", "NUITKA_PGO_VALUE_TAG_NONE"),
    ("true", "NUITKA_PGO_VALUE_TAG_TRUE"),
    ("false", "NUITKA_PGO_VALUE_TAG_FALSE"),
    ("ellipsis", "NUITKA_PGO_VALUE_TAG_ELLIPSIS"),
    ("int_positive", "NUITKA_PGO_VALUE_TAG_INT_POSITIVE"),
    ("int_negative", "NUITKA_PGO_VALUE_TAG_INT_NEGATIVE"),
    ("float", "NUITKA_PGO_VALUE_TAG_FLOAT"),
    ("complex", "NUITKA_PGO_VALUE_TAG_COMPLEX"),
    ("str", "NUITKA_PGO_VALUE_TAG_STR"),
    ("unicode", "NUITKA_PGO_VALUE_TAG_UNICODE"),
    ("bytes", "NUITKA_PGO_VALUE_TAG_BYTES"),
    ("bytearray", "NUITKA_PGO_VALUE_TAG_BYTEARRAY"),
    ("list", "NUITKA_PGO_VALUE_TAG_LIST"),
    ("tuple", "NUITKA_PGO_VALUE_TAG_TUPLE"),
    ("dict", "NUITKA_PGO_VALUE_TAG_DICT"),
    ("set", "NUITKA_PGO_VALUE_TAG_SET"),
    ("frozenset", "NUITKA_PGO_VALUE_TAG_FROZENSET"),
    ("too_large", "NUITKA_PGO_VALUE_TAG_TOO_LARGE"),
    ("too_large_encoding", "NUITKA_PGO_VALUE_TAG_TOO_LARGE_ENCODING"),
    ("too_many", "NUITKA_PGO_VALUE_TAG_TOO_MANY"),
    ("big_int", "NUITKA_PGO_VALUE_TAG_BIG_INT"),
    ("global", "NUITKA_PGO_VALUE_TAG_GLOBAL"),
    ("reduced", "NUITKA_PGO_VALUE_TAG_REDUCED"),
    ("unsupported", "NUITKA_PGO_VALUE_TAG_UNSUPPORTED"),
)

_required_define_names = (
    _probe_define_names,
    _scope_define_names,
    _value_tag_define_names,
)

_pgo_spec_cache = {}


class _PgoSpec(object):
    def __init__(self, filename, values):
        self.filename = filename

        for field_name, define_name in _probe_define_names:
            setattr(self, "probe_" + field_name, values[define_name])

        for field_name, define_name in _scope_define_names:
            setattr(self, "scope_" + field_name, values[define_name])

        for field_name, define_name in _value_tag_define_names:
            setattr(self, "value_tag_" + field_name, to_byte(values[define_name]))


def _getDefaultPgoSpecFilename():
    return getNormalizedPathJoin(
        os.path.dirname(__file__),
        "..",
        "build",
        "include",
        "nuitka",
        "python_pgo_spec.h",
    )


def _parsePgoSpecValue(value):
    value = value.rstrip("uUlL")

    return int(value, 0)


def _isIgnorablePgoSpecLine(line):
    line = line.strip()

    if not line:
        return True

    if line in (
        "#pragma once",
        "#ifndef __NUITKA_PYTHON_PGO_SPEC_H__",
        "#define __NUITKA_PYTHON_PGO_SPEC_H__",
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


def _loadPgoSpecValues(filename, logger):
    result = {}

    for count, line in enumerate(
        getFileContents(filename, encoding="ascii").splitlines(), 1
    ):
        match = _define_pattern.match(line)

        if match is None:
            if _isIgnorablePgoSpecLine(line):
                continue

            return logger.sysexit(
                "Unexpected line %d in PGO spec '%s': %r" % (count, filename, line)
            )

        define_name, define_value = match.groups()
        result[define_name] = _parsePgoSpecValue(define_value)

    return result


def _checkRequiredPgoSpecValues(filename, values, logger):
    missing = []

    for define_names in _required_define_names:
        for _field_name, define_name in define_names:
            if define_name not in values:
                missing.append(define_name)

    if missing:
        return logger.sysexit(
            "Missing PGO spec values in '%s': %s"
            % (filename, ", ".join(sorted(missing)))
        )


def _checkPgoSpecValuesAreDistinct(filename, values, define_names, description, logger):
    used_values = set()

    for _field_name, define_name in define_names:
        value = values[define_name]

        if value < 0 or value > 255:
            return logger.sysexit(
                "Invalid %s in '%s' for %s: %r"
                % (description, filename, define_name, value)
            )

        if value in used_values:
            return logger.sysexit(
                "Duplicate %s in '%s' for %s: %r"
                % (description, filename, define_name, value)
            )

        used_values.add(value)


def _checkPgoSpecValues(filename, values, logger):
    _checkRequiredPgoSpecValues(filename=filename, values=values, logger=logger)

    _checkPgoSpecValuesAreDistinct(
        filename=filename,
        values=values,
        define_names=_probe_define_names,
        description="PGO probe ID",
        logger=logger,
    )
    _checkPgoSpecValuesAreDistinct(
        filename=filename,
        values=values,
        define_names=_scope_define_names,
        description="PGO scope kind",
        logger=logger,
    )
    _checkPgoSpecValuesAreDistinct(
        filename=filename,
        values=values,
        define_names=_value_tag_define_names,
        description="PGO value tag",
        logger=logger,
    )


def loadPgoSpec(logger):
    filename = _getDefaultPgoSpecFilename()

    result = _pgo_spec_cache.get(filename)

    if result is None:
        values = _loadPgoSpecValues(filename, logger)

        _checkPgoSpecValues(filename, values, logger)

        result = _PgoSpec(filename=filename, values=values)
        _pgo_spec_cache[filename] = result

    return result


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
