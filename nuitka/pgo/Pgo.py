#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Python level PGO handling in Nuitka."""

import base64
import struct

from nuitka.__past__ import long, unicode, xrange
from nuitka.options.Options import (
    getPythonPgoJsonFilename,
    getPythonPgoUnseenModulePolicy,
    isDevelPgoWarnUnknown,
)
from nuitka.Tracing import pgo_logger
from nuitka.utils.Json import writeJsonToFilename

from .PgoFormat import loadPgoSpec

_pgo_active = False

# The format version of the PGO file that is understood here.
_pgo_format_version = 2

# The format constants parsed from the C header, loaded on first use.
_pgo_spec = None

_module_entries = {}
_module_exits = {}

_class_prepare_calls = {}


def _getPgoSpec():
    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=global-statement
    global _pgo_spec

    if _pgo_spec is None:
        _pgo_spec = loadPgoSpec(pgo_logger)

    return _pgo_spec


def _getPgoProbeNames():
    spec = _getPgoSpec()

    return {
        spec.probe_module_enter: "ModuleEnter",
        spec.probe_module_exit: "ModuleExit",
        spec.probe_class_prepare_result: "ClassPrepareResult",
        spec.probe_class_prepare_result_once: "ClassPrepareResultOnce",
        spec.probe_string_definition: "StringDefinition",
        spec.probe_key_definition: "KeyDefinition",
        spec.probe_value_definition: "ValueDefinition",
    }


class PgoValueTooLarge(object):
    """PGO value that was too large to be recorded.

    Only its type and size are known, not its contents, so it cannot be used
    as an expected value.
    """

    def __init__(self, value_type, size):
        self.value_type = value_type
        self.size = size


class PgoValueTooLargeEncoding(object):
    """PGO value whose encoding exceeded the budget.

    Nothing is known about it, so it cannot be used as an expected value.
    """


class PgoValueTooMany(object):
    """PGO key that was observed with too many distinct values.

    Nothing reliable is known about it, so it cannot be used as an expected
    value.
    """


class PgoValueUnsupported(object):
    """PGO value that could not be reconstructed.

    Nothing is known about it beyond its type name, so it cannot be used as
    an expected value.
    """

    def __init__(self, type_name):
        self.type_name = type_name


class PgoValueUnsupportedCapture(object):
    """PGO value that could not be captured at run time.

    The writer could not represent the value at all, so nothing is known
    about it. Its presence still proves that the probe was executed.
    """


def getPGOClassPrepareResult(scope_id):
    return _class_prepare_calls.get(scope_id)


def _readUvarint(input_file):
    """Read an unsigned variably sized integer.

    Args:
        input_file: The file to read from.

    Returns:
        int value of the variable length encoded integer.

    Raises:
        EOFError: If the file ends in the middle of the integer.
    """

    shift = 0
    result = 0

    while True:
        data = input_file.read(1)

        if not data:
            raise EOFError("Unexpected end of PGO file.")

        if str is bytes:
            value = ord(data)
        else:
            value = data[0]

        result |= (value & 0x7F) << shift

        if not value & 0x80:
            return result

        shift += 7


def _readRawBytes(input_file, length):
    data = input_file.read(length)

    if len(data) != length:
        raise EOFError("Unexpected end of PGO file.")

    return data


def _readStringEntry(input_file, strings):
    length = _readUvarint(input_file)

    strings.append(_readRawBytes(input_file, length))

    return len(strings) - 1


def _readStringReference(input_file, strings):
    string_id = _readUvarint(input_file)

    if string_id >= len(strings):
        return pgo_logger.sysexit(
            "Error, invalid string reference %d in PGO file." % string_id
        )

    return strings[string_id]


def _readKeyEntry(input_file, strings, keys):
    scope_kind = _readUvarint(input_file)
    string_id = _readUvarint(input_file)

    if string_id >= len(strings):
        return pgo_logger.sysexit(
            "Error, invalid string reference %d in PGO file." % string_id
        )

    keys.append((scope_kind, string_id))

    return len(keys) - 1


def _readKeyReference(input_file, keys):
    key_id = _readUvarint(input_file)

    if key_id >= len(keys):
        return pgo_logger.sysexit(
            "Error, invalid key reference %d in PGO file." % key_id
        )

    return key_id


def _decodePgoString(value):
    # For JSON, invalid UTF-8 must not abort the output.
    return value.decode("utf8", "backslashreplace")


def _decodeModuleName(value):
    if str is not bytes:
        value = value.decode("utf8")

    return value


# Modules whose globals may be resolved when reconstructing reduce output. Being
# selective here avoids importing arbitrary modules (and running their import
# side effects) just because a PGO file mentions them.
_pgo_allowed_global_modules = (
    "builtins",
    "__builtin__",
    "copyreg",
    "copy_reg",
    "functools",
    "_functools",
    "operator",
    "_operator",
    "collections",
    "types",
)


def _createUnsupportedValue(type_name, exception):
    if isDevelPgoWarnUnknown():
        pgo_logger.warning(
            "PGO: cannot use value of type %r: %s" % (type_name, exception)
        )

    return PgoValueUnsupported(type_name=type_name)


def _resolveGlobal(module_name, qualname):
    # Objects from "__main__" of the capture run cannot be resolved meaningfully.
    if module_name in ("__main__", "__mp_main__"):
        return PgoValueUnsupported(type_name=qualname)

    # Only a known set of modules is importable while reading PGO data.
    if module_name not in _pgo_allowed_global_modules:
        return _createUnsupportedValue(
            qualname, "module %r is not allowed to be imported" % module_name
        )

    if str is bytes and module_name == "builtins":
        module_name = "__builtin__"

    try:
        result = __import__(module_name, fromlist=["*"])
    except Exception as exception:  # pylint: disable=broad-except
        return _createUnsupportedValue(qualname, exception)

    for attribute_name in qualname.split("."):
        if attribute_name == "<locals>":
            return PgoValueUnsupported(type_name=qualname)

        result = getattr(result, attribute_name, None)

        if result is None:
            return PgoValueUnsupported(type_name=qualname)

    return result


def _getTypeName(value):
    if type(value) is PgoValueUnsupported:
        return value.type_name

    if type(value) is type:
        return value.__name__

    return None


def _reconstruct(value_type, callable_value, args, state, listitems, dictitems):
    if not callable(callable_value) or type(args) is not tuple:
        return PgoValueUnsupported(type_name=_getTypeName(value_type))

    try:
        result = callable_value(*args)

        if state is not None:
            setstate = getattr(result, "__setstate__", None)

            if setstate is not None:
                setstate(state)
            elif type(state) is dict:
                result.__dict__.update(state)

        if listitems is not None:
            for item in listitems:
                result.append(item)

        if dictitems is not None:
            for key, item in dictitems:
                result[key] = item  # type: ignore
    except Exception as exception:  # pylint: disable=broad-except
        return _createUnsupportedValue(_getTypeName(value_type), exception)

    return result


def _readValueEntry(input_file, strings):
    # One branch per value tag of the format, pylint: disable=too-many-branches,too-many-locals,too-many-return-statements,too-many-statements
    tag = _readRawBytes(input_file, 1)

    spec = _getPgoSpec()

    if tag == spec.value_tag_none:
        return None

    if tag == spec.value_tag_true:
        return True

    if tag == spec.value_tag_false:
        return False

    if tag == spec.value_tag_ellipsis:
        return Ellipsis

    if tag == spec.value_tag_int_positive:
        return _readUvarint(input_file)

    if tag == spec.value_tag_int_negative:
        return -_readUvarint(input_file)

    if tag == spec.value_tag_str:
        value = _readStringReference(input_file, strings)

        if str is not bytes:
            value = value.decode("utf8")

        return value

    if tag == spec.value_tag_unicode:
        return _readStringReference(input_file, strings).decode("utf8")

    if tag == spec.value_tag_bytes:
        return bytes(_readStringReference(input_file, strings))

    if tag == spec.value_tag_bytearray:
        return bytearray(_readStringReference(input_file, strings))

    if tag == spec.value_tag_float:
        return struct.unpack(">d", _readRawBytes(input_file, 8))[0]

    if tag == spec.value_tag_complex:
        real, imag = struct.unpack(">dd", _readRawBytes(input_file, 16))

        return complex(real, imag)

    if tag in (
        spec.value_tag_list,
        spec.value_tag_tuple,
        spec.value_tag_set,
        spec.value_tag_frozenset,
    ):
        count = _readUvarint(input_file)

        result = [
            _readValueEntry(input_file=input_file, strings=strings)
            for _ in xrange(count)
        ]

        if tag == spec.value_tag_list:
            return result
        elif tag == spec.value_tag_tuple:
            return tuple(result)
        elif tag == spec.value_tag_set:
            return set(result)
        else:
            return frozenset(result)

    if tag == spec.value_tag_dict:
        count = _readUvarint(input_file)

        result = {}

        for _ in xrange(count):
            key = _readValueEntry(input_file=input_file, strings=strings)
            item = _readValueEntry(input_file=input_file, strings=strings)

            result[key] = item

        return result

    if tag == spec.value_tag_big_int:
        value = _readStringReference(input_file, strings)

        if str is not bytes:
            value = value.decode("utf8")

        return int(value)

    if tag == spec.value_tag_global:
        module_name = _readStringReference(input_file, strings)
        qualname = _readStringReference(input_file, strings)

        if str is not bytes:
            module_name = module_name.decode("utf8")
            qualname = qualname.decode("utf8")

        return _resolveGlobal(module_name, qualname)

    if tag == spec.value_tag_reduced:
        value_type = _readValueEntry(input_file=input_file, strings=strings)
        callable_value = _readValueEntry(input_file=input_file, strings=strings)
        args = _readValueEntry(input_file=input_file, strings=strings)
        state = _readValueEntry(input_file=input_file, strings=strings)
        listitems = _readValueEntry(input_file=input_file, strings=strings)
        dictitems = _readValueEntry(input_file=input_file, strings=strings)

        return _reconstruct(
            value_type=value_type,
            callable_value=callable_value,
            args=args,
            state=state,
            listitems=listitems,
            dictitems=dictitems,
        )

    if tag == spec.value_tag_unsupported:
        return PgoValueUnsupportedCapture()

    if tag == spec.value_tag_too_large:
        value_type = _readRawBytes(input_file, 1)
        size = _readUvarint(input_file)

        if str is not bytes:
            value_type = value_type.decode("ascii")

        return PgoValueTooLarge(value_type=value_type, size=size)

    if tag == spec.value_tag_too_large_encoding:
        return PgoValueTooLargeEncoding()

    if tag == spec.value_tag_too_many:
        return PgoValueTooMany()

    return pgo_logger.sysexit("Error, unknown value tag %r in PGO file." % tag)


def _readKeyName(input_file, strings, keys):
    key_id = _readKeyReference(input_file=input_file, keys=keys)

    scope_kind, string_id = keys[key_id]

    return key_id, scope_kind, _decodeModuleName(strings[string_id])


def _getUnusableValueReason(value):
    # One branch per unusable value type, pylint: disable=too-many-branches,too-many-return-statements
    value_type = type(value)

    if value_type is PgoValueTooLarge:
        return "value too large (type %r, size %d)" % (value.value_type, value.size)

    if value_type is PgoValueTooLargeEncoding:
        return "value encoding too large"

    if value_type is PgoValueTooMany:
        return "too many distinct values"

    if value_type is PgoValueUnsupported:
        if value.type_name is not None:
            return "value could not be reconstructed (type %r)" % value.type_name

        return "value could not be reconstructed"

    if value_type is PgoValueUnsupportedCapture:
        return "value could not be captured"

    if value_type is dict:
        for key, item in value.items():
            reason = _getUnusableValueReason(key)

            if reason is None:
                reason = _getUnusableValueReason(item)

            if reason is not None:
                return reason
    elif value_type in (list, tuple, set, frozenset):
        for item in value:
            reason = _getUnusableValueReason(item)

            if reason is not None:
                return reason

    return None


def _considerClassPrepareResult(code_name, value):
    unusable_reason = _getUnusableValueReason(value)

    if unusable_reason is not None:
        if isDevelPgoWarnUnknown():
            pgo_logger.warning(
                "PGO class prepare of '%s' is not usable: %s."
                % (code_name, unusable_reason)
            )

        # Cannot use the contents for optimization purposes, ignore it.
        return

    if code_name in _class_prepare_calls:
        if _class_prepare_calls[code_name] != value:
            if isDevelPgoWarnUnknown():
                pgo_logger.warning(
                    "Ignoring PGO data for class prepare of '%s', differing values observed."
                    % code_name
                )

            _class_prepare_calls[code_name] = None
    else:
        _class_prepare_calls[code_name] = value


def _readPgoProbe(input_file, strings, keys, values, probes, probe_id):
    # One branch per probe ID of the format, pylint: disable=too-many-branches,too-many-locals,too-many-return-statements
    spec = _getPgoSpec()

    if probe_id == spec.probe_string_definition:
        string_id = _readUvarint(input_file)

        if string_id != len(strings):
            return pgo_logger.sysexit(
                "Error, out of order string definition %d in PGO file." % string_id
            )

        _readStringEntry(input_file=input_file, strings=strings)
    elif probe_id == spec.probe_key_definition:
        key_id = _readUvarint(input_file)

        if key_id != len(keys):
            return pgo_logger.sysexit(
                "Error, out of order key definition %d in PGO file." % key_id
            )

        _readKeyEntry(input_file=input_file, strings=strings, keys=keys)
    elif probe_id == spec.probe_value_definition:
        value_id = _readUvarint(input_file)

        if value_id != len(values):
            return pgo_logger.sysexit(
                "Error, out of order value definition %d in PGO file." % value_id
            )

        values.append(_readValueEntry(input_file=input_file, strings=strings))
    elif probe_id == spec.probe_module_enter:
        key_id, scope_kind, module_name = _readKeyName(
            input_file=input_file, strings=strings, keys=keys
        )

        if scope_kind != spec.scope_module:
            return pgo_logger.sysexit(
                "Error, module enter probe with non-module key in PGO file."
            )

        _module_entries[module_name] = True

        probes.append({"probe": "ModuleEnter", "key_id": key_id, "module": module_name})
    elif probe_id == spec.probe_module_exit:
        key_id, scope_kind, module_name = _readKeyName(
            input_file=input_file, strings=strings, keys=keys
        )

        if scope_kind != spec.scope_module:
            return pgo_logger.sysexit(
                "Error, module exit probe with non-module key in PGO file."
            )

        had_error = _readUvarint(input_file) != 0

        _module_exits[module_name] = had_error

        probes.append(
            {
                "probe": "ModuleExit",
                "key_id": key_id,
                "had_error": had_error,
                "module": module_name,
            }
        )
    elif probe_id in (
        spec.probe_class_prepare_result,
        spec.probe_class_prepare_result_once,
    ):
        key_id, scope_kind, code_name = _readKeyName(
            input_file=input_file, strings=strings, keys=keys
        )

        if scope_kind != spec.scope_class:
            return pgo_logger.sysexit(
                "Error, class prepare probe with non-class key in PGO file."
            )

        value_id = _readUvarint(input_file)

        if value_id >= len(values):
            return pgo_logger.sysexit(
                "Error, invalid value reference %d in PGO file." % value_id
            )

        value = values[value_id]

        _considerClassPrepareResult(code_name=code_name, value=value)

        probe_entry = {
            "probe": (
                "ClassPrepareResult"
                if probe_id == spec.probe_class_prepare_result
                else "ClassPrepareResultOnce"
            ),
            "key_id": key_id,
            "value_id": value_id,
            "class": code_name,
            "value": _jsonifyValue(value),
        }

        if probe_id == spec.probe_class_prepare_result:
            probe_entry["count"] = _readUvarint(input_file)

        probes.append(probe_entry)
    else:
        probe_name = _getPgoProbeNames().get(probe_id)

        if probe_name is not None:
            return pgo_logger.sysexit(
                "Error, unsupported probe '%s' in PGO file." % probe_name
            )
        else:
            return pgo_logger.sysexit(
                "Error, unknown probe ID %d in PGO file." % probe_id
            )


def _readPgoTrailer(input_file, input_filename, strings, keys, values):
    string_count = _readUvarint(input_file)
    key_count = _readUvarint(input_file)
    value_count = _readUvarint(input_file)

    if (
        string_count != len(strings)
        or key_count != len(keys)
        or value_count != len(values)
    ):
        return pgo_logger.sysexit(
            "Error, file '%s' has inconsistent counts." % input_filename
        )

    trailer = input_file.read(7)

    if trailer != b"YAK.PGO":
        return pgo_logger.sysexit(
            "Error, file '%s' was not completed correctly." % input_filename
        )


def _jsonifyValue(value):
    # One branch per type of the format, pylint: disable=too-many-branches,too-many-return-statements
    if value is None or type(value) in (bool, int, long, float, str, unicode):
        return value

    if type(value) is dict:
        result = {}

        for key, item in value.items():
            if type(key) not in (str, unicode):
                return {
                    "$dict": [
                        [_jsonifyValue(key), _jsonifyValue(item)]
                        for key, item in value.items()
                    ]
                }

            result[key] = _jsonifyValue(item)

        return result

    if type(value) is list:
        return {"$list": [_jsonifyValue(item) for item in value]}

    if type(value) is tuple:
        return {"$tuple": [_jsonifyValue(item) for item in value]}

    if type(value) is set:
        return {"$set": [_jsonifyValue(item) for item in value]}

    if type(value) is frozenset:
        return {"$frozenset": [_jsonifyValue(item) for item in value]}

    if type(value) is bytes:
        return {"$bytes": base64.b64encode(value).decode("ascii")}

    if type(value) is bytearray:
        return {"$bytearray": base64.b64encode(bytes(value)).decode("ascii")}

    if type(value) is complex:
        return {"$complex": [value.real, value.imag]}

    if type(value) is PgoValueTooLarge:
        return {"$too_large": {"type": value.value_type, "size": value.size}}

    if type(value) is PgoValueTooLargeEncoding:
        return {"$too_large_encoding": True}

    if type(value) is PgoValueTooMany:
        return {"$too_many": True}

    if type(value) is PgoValueUnsupported:
        return {"$unsupported": {"type": value.type_name}}

    if type(value) is PgoValueUnsupportedCapture:
        return {"$unsupported_capture": True}

    return {"$unknown": repr(value)}


def _buildPgoJsonData(string_values, keys, values, probes):
    return {
        "format_version": _pgo_format_version,
        "string_values": [_decodePgoString(value) for value in string_values],
        "keys": [
            {"scope_kind": scope_kind, "string_id": string_id}
            for scope_kind, string_id in keys
        ],
        "values": [_jsonifyValue(value) for value in values],
        "probes": probes,
    }


def readPGOInputFile(input_filename):
    """Read PGO information produced by a PGO run."""

    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=global-statement
    global _pgo_active

    with open(input_filename, "rb") as input_file:
        header = input_file.read(7)

        if header != b"KAY.PGO":
            return pgo_logger.sysexit(
                "Error, file '%s' is not a valid PGO input for this version of Nuitka."
                % input_filename
            )

        try:
            format_version = _readUvarint(input_file)

            if format_version != _pgo_format_version:
                return pgo_logger.sysexit(
                    "Error, file '%s' has PGO format version %d, expected %d."
                    % (input_filename, format_version, _pgo_format_version)
                )

            strings = []
            keys = []
            values = []
            probes = []

            while True:
                probe_id = _readUvarint(input_file)

                if probe_id == _getPgoSpec().probe_end:
                    break

                _readPgoProbe(
                    input_file=input_file,
                    strings=strings,
                    keys=keys,
                    values=values,
                    probes=probes,
                    probe_id=probe_id,
                )

            _readPgoTrailer(
                input_file=input_file,
                input_filename=input_filename,
                strings=strings,
                keys=keys,
                values=values,
            )
        except EOFError:
            return pgo_logger.sysexit("Error, file '%s' is truncated." % input_filename)

        json_filename = getPythonPgoJsonFilename()

        if json_filename is not None:
            writeJsonToFilename(
                json_filename,
                _buildPgoJsonData(
                    string_values=strings, keys=keys, values=values, probes=probes
                ),
            )

            pgo_logger.info("Written PGO data as JSON to '%s'." % json_filename)

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
