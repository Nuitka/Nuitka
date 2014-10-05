#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Low level constant code generation.

"""

import ctypes
import re
import struct

import marshal
from nuitka.__past__ import iterItems, long, unicode  # pylint: disable=W0622
from nuitka.Constants import (
    constant_builtin_types,
    getConstantWeight,
    isMutable
)

from .BlobCodes import StreamData
from .Emission import SourceCodeCollector
from .Pickling import getStreamedConstant

stream_data = StreamData()

def getConstantCode(context, constant):
    return context.getConstantCode(constant)

# TODO: The determination of this should already happen in Building or in a
# helper not during code generation.
_match_attribute_names = re.compile( r"[a-zA-Z_][a-zA-Z0-9_]*$" )

def getConstantCodeName(context, constant):
    return context.getConstantCode(constant)


def _isAttributeName(value):
    return _match_attribute_names.match(value)


# Indicator to standalone mode code, if we need pickling module early on.
_needs_pickle = False

def needsPickleInit():
    return _needs_pickle


def _getUnstreamCode2(constant_value):
    saved = getStreamedConstant(
        constant_value = constant_value
    )

    assert type(saved) is bytes

    # We need to remember having to use pickle, pylint: disable=W0603
    global _needs_pickle
    _needs_pickle = True

    return stream_data.getStreamDataCode(saved)


def _getUnstreamCode(constant_value, constant_identifier):
    return "%s = UNSTREAM_CONSTANT( %s );" % (
        constant_identifier,
        _getUnstreamCode2(constant_value)
    )


def _packFloat(value):
    return struct.pack("<d", value)

sizeof_long = ctypes.sizeof(ctypes.c_long)

max_unsigned_long = 2**(sizeof_long*8)-1

# The gcc gives a warning for -2**sizeof_long*8-1, which is still an "int", but
# seems to not work (without warning) as literal, so avoid it.
min_signed_long = -(2**(sizeof_long*8-1)-1)

done = set()

def _getConstantInitValueCode(constant_value, constant_type):
    if constant_type is unicode:
        try:
            encoded = constant_value.encode("utf-8")

            if str is not unicode:
                return "UNSTREAM_UNICODE( %s )" % (
                    stream_data.getStreamDataCode(encoded)
                )
            else:
                return "UNSTREAM_STRING( %s, %d, %d )" % (
                    stream_data.getStreamDataCode(encoded, fixed_size = True),
                    len(constant_value),
                    1 if _isAttributeName(constant_value) else 0
                )
        except UnicodeEncodeError:
            return None
    elif constant_type is str:
        # Python3: Strings that can be encoded as UTF-8 are done more or less
        # directly. When they cannot be expressed as UTF-8, that is rare not we
        # can indeed use pickling.
        assert str is not unicode

        if len(constant_value) == 1:
            return "UNSTREAM_CHAR( %d, %d )" % (
                ord(constant_value[0]),
                1 if _isAttributeName(constant_value) else 0
            )
        else:
            return "UNSTREAM_STRING( %s, %d )" % (
                stream_data.getStreamDataCode(constant_value),
                1 if _isAttributeName(constant_value) else 0
            )
    elif constant_type is bytes:
        assert str is unicode

        return "UNSTREAM_BYTES( %s )" % (
            stream_data.getStreamDataCode(constant_value)
        )
    else:
        return None


def decideMarshal(constant_value):
    constant_type = type(constant_value)

    if constant_type is type:
        return False
    elif constant_type is dict:
        for key, value in iterItems(constant_value):
            if not decideMarshal(key):
                return False
            if not decideMarshal(value):
                return False
    elif constant_type in (tuple, list, set, frozenset):
        for element_value in constant_value:
            if not decideMarshal(element_value):
                return False

    # Do it for sufficiently large constants, typically tuples of 20 elements,
    # or dicts of more than 10.
    if getConstantWeight(constant_value) < 20:
        return False

    return True

def isMarshalConstant(constant_value):
    if not decideMarshal(constant_value):
        return False

    marshal_value = marshal.dumps(constant_value)
    restored = marshal.loads(marshal_value)

    return constant_value == restored


def attemptToMarshal(constant_identifier, constant_value, emit):
    if not decideMarshal(constant_value):
        return False

    marshal_value = marshal.dumps(constant_value)
    restored = marshal.loads(marshal_value)

    if constant_value != restored:
        return False

    emit(
        """%s = PyMarshal_ReadObjectFromString( (char *)%s );""" % (
            constant_identifier,
            stream_data.getStreamDataCode(marshal_value)
        )
    )

    return True


def _addConstantInitCode(context, emit, constant_type, constant_value,
                         constant_identifier, module_level):
    # This has many cases, that all return, and do a lot.
    # pylint: disable=R0911,R0912,R0915

    if constant_value in constant_builtin_types:
        return
    if constant_value is None:
        return
    if constant_value is False:
        return
    if constant_value is True:
        return
    if constant_value is Ellipsis:
        return
    if constant_identifier in done:
        return

    if module_level:
        if context.global_context.getConstantUseCount(constant_identifier) != 1:
            return
    else:
        if context.getConstantUseCount(constant_identifier) == 1:
            return

    done.add(constant_identifier)

    # Use shortest code for ints and longs.
    if constant_type is long:
        # See above, same for long values. Note: These are of course not
        # existant with Python3 which would have covered it before.
        if constant_value >= 0 and constant_value <= max_unsigned_long:
            emit (
                "%s = PyLong_FromUnsignedLong( %sul );" % (
                    constant_identifier,
                    constant_value
                )
            )

            return
        elif constant_value < 0 and constant_value >= min_signed_long:
            emit (
                "%s = PyLong_FromLong( %sl );" % (
                    constant_identifier,
                    constant_value
                )
            )

            return
        elif constant_value == min_signed_long-1:
            emit(
                "%s = PyLong_FromLong( %sl ); %s = PyNumber_InPlaceSubtract( %s, const_int_pos_1 );" % (
                    constant_identifier,
                    min_signed_long,
                    constant_identifier,
                    constant_identifier
                )
            )

            return

    elif constant_type is int:
        if constant_value >= min_signed_long:
            emit(
                "%s = PyInt_FromLong( %sl );" % (
                    constant_identifier,
                    constant_value
                )
            )

            return
        else:
            assert constant_value == min_signed_long-1

            emit(
                "%s = PyInt_FromLong( %sl ); %s = PyNumber_InPlaceSubtract( %s, const_int_pos_1 );" % (
                    constant_identifier,
                    min_signed_long,
                    constant_identifier,
                    constant_identifier
                )
            )

            return

    if constant_type is unicode:
        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        try:
            encoded = constant_value.encode("utf-8")

            if str is not unicode:
                emit(
                    "%s = UNSTREAM_UNICODE( %s );" % (
                        constant_identifier,
                        stream_data.getStreamDataCode(encoded)
                    )
                )
            else:
                emit(
                    "%s = UNSTREAM_STRING( %s, %d );" % (
                        constant_identifier,
                        stream_data.getStreamDataCode(encoded),
                        1 if _isAttributeName(constant_value) else 0
                    )
                )

            return
        except UnicodeEncodeError:
            # So fall back to below code, which will unstream it then.
            pass
    elif constant_type is str:
        # Python3: Strings that can be encoded as UTF-8 are done more or less
        # directly. When they cannot be expressed as UTF-8, that is rare not we
        # can indeed use pickling.
        assert str is not unicode

        if len(constant_value) == 1:
            emit(
                "%s = UNSTREAM_CHAR( %d, %d );" % (
                    constant_identifier,
                    ord(constant_value[0]),
                    1 if _isAttributeName(constant_value) else 0
                )
            )
        else:
            emit(
                "%s = UNSTREAM_STRING( %s, %d );" % (
                    constant_identifier,
                    stream_data.getStreamDataCode(constant_value),
                    1 if _isAttributeName(constant_value) else 0
                )
            )

        return
    elif constant_type is bytes:
        assert str is unicode

        emit(
            "%s = UNSTREAM_BYTES( %s );" % (
                constant_identifier,
                stream_data.getStreamDataCode(constant_value)
            )
        )

        return

    if constant_type is float:
        emit(
            "%s = UNSTREAM_FLOAT( %s );" % (
                constant_identifier,
                stream_data.getStreamDataCode(
                    value      = _packFloat(constant_value),
                    fixed_size = True
                )
            )
        )

        return

    if constant_type is dict:
        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        emit(
            "%s = _PyDict_NewPresized( %d );" % (
                constant_identifier,
                len(constant_value)
            )
        )

        for key, value in iterItems(constant_value):
            key_name = getConstantCodeName(context, key)
            _addConstantInitCode(
                emit                = emit,
                constant_type       = type(key),
                constant_value      = key,
                constant_identifier = key_name,
                module_level        = module_level,
                context             = context
            )

            value_name = getConstantCodeName(context, value)
            _addConstantInitCode(
                emit                = emit,
                constant_type       = type(value),
                constant_value      = value,
                constant_identifier = value_name,
                module_level        = module_level,
                context             = context
            )

            emit(
                "PyDict_SetItem( %s, %s, %s );" % (
                    constant_identifier,
                    key_name,
                    value_name
                )
            )

        return

    if constant_type is tuple:
        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        emit(
            "%s = PyTuple_New( %d );" % (
                constant_identifier,
                len(constant_value)
            )
        )

        for count, element_value in enumerate(constant_value):
            element_name = getConstantCodeName(
                context  = context,
                constant = element_value
            )

            _addConstantInitCode(
                emit                = emit,
                constant_type       = type(element_value),
                constant_value      = element_value,
                constant_identifier = getConstantCodeName(
                    context  = context,
                    constant = element_value
                ),
                module_level        = module_level,
                context             = context
            )

            # Do not take references, these won't be deleted ever.
            emit(
                "PyTuple_SET_ITEM( %s, %d, %s ); Py_INCREF( %s );" % (
                    constant_identifier,
                    count,
                    element_name,
                    element_name
                )
            )

        return

    if constant_type is list:
        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        emit(
            "%s = PyList_New( %d );" % (
                constant_identifier,
                len(constant_value)
            )
        )

        for count, element_value in enumerate(constant_value):
            element_name = getConstantCodeName(
                context  = context,
                constant = element_value
            )

            _addConstantInitCode(
                emit                = emit,
                constant_type       = type(element_value),
                constant_value      = element_value,
                constant_identifier = element_name,
                module_level        = module_level,
                context             = context
            )

            # Do not take references, these won't be deleted ever.
            emit(
                "PyList_SET_ITEM( %s, %d, %s ); Py_INCREF( %s );" % (
                    constant_identifier,
                    count,
                    element_name,
                    element_name
                )
            )

        return

    if constant_type is set:
        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        emit("%s = PySet_New( NULL );" % constant_identifier)

        for element_value in constant_value:
            element_name = getConstantCodeName(
                context  = context,
                constant = element_value
            )

            _addConstantInitCode(
                emit                = emit,
                constant_type       = type(element_value),
                constant_value      = element_value,
                constant_identifier = element_name,
                module_level        = module_level,
                context             = context
            )

            emit(
                "PySet_Add( %s, %s );" % (
                    constant_identifier,
                    element_name
                )
            )

        return

    if constant_type in (frozenset, complex, unicode, long, range):
        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        emit(_getUnstreamCode(constant_value, constant_identifier))

        return

    assert False, ( type(constant_value), constant_value, constant_identifier )


def getConstantsInitCode(context):
    # There are many cases for constants to be created in the most efficient
    # way, pylint: disable=R0912

    emit = SourceCodeCollector()

    sorted_constants = sorted(
        iterItems(context.getConstants()),
        key = lambda k: (len(k), k )
    )

    for constant_identifier, constant_value in sorted_constants:
        _addConstantInitCode(
            emit                = emit,
            constant_type       = type(constant_value),
            constant_value      = constant_value,
            constant_identifier = constant_identifier,
            module_level        = False,
            context             = context
        )

    return emit.codes


def getConstantsDeclCode(context):
    # There are many cases for constants of different types.
    # pylint: disable=R0912
    statements = []

    sorted_constants = sorted(
        iterItems(context.getConstants()),
        key = lambda k: (len(k), k )
    )

    for constant_identifier, constant_value in sorted_constants:
        # Need not declare built-in types.
        if constant_value in constant_builtin_types:
            continue
        if constant_value is None:
            continue
        if constant_value is False:
            continue
        if constant_value is True:
            continue
        if constant_value is Ellipsis:
            continue

        if context.getConstantUseCount(constant_identifier) != 1:
            statements.append("PyObject *%s;" % constant_identifier)

    return statements


def getConstantAccess(to_name, constant, emit, context):
    # Many cases, because for each type, we may copy or optimize by creating
    # empty.  pylint: disable=R0911,R0912, R0915

    if type(constant) is dict:
        if constant:
            for key, value in iterItems(constant):
                # key cannot be mutable.
                assert not isMutable(key)
                if isMutable(value):
                    needs_deep = True
                    break
            else:
                needs_deep = False

            if needs_deep:
                code = "DEEP_COPY( %s )" % getConstantCode(
                    constant = constant,
                    context  = context
                )
            else:
                code = "PyDict_Copy( %s )" % getConstantCode(
                    constant = constant,
                    context  = context
                )
        else:
            code = "PyDict_New()"

        ref_count = 1
    elif type(constant) is set:
        if constant:
            code = "PySet_New( %s )" % getConstantCode(
                constant = constant,
                context  = context
            )
        else:
            code = "PySet_New( NULL )"

        ref_count = 1
    elif type(constant) is list:
        if constant:
            for value in constant:
                if isMutable(value):
                    needs_deep = True
                    break
            else:
                needs_deep = False

            if needs_deep:
                code = "DEEP_COPY( %s )" % getConstantCode(
                    constant = constant,
                    context  = context
                )
            else:
                code = "LIST_COPY( %s )" % getConstantCode(
                    constant = constant,
                    context  = context
                )
        else:
            code = "PyList_New( 0 )"

        ref_count = 1
    elif type(constant) is tuple:
        for value in constant:
            if isMutable(value):
                needs_deep = True
                break
        else:
            needs_deep = False

        if needs_deep:
            code = "DEEP_COPY( %s )" % getConstantCode(
                 constant = constant,
                 context  = context
            )

            ref_count = 1
        else:
            code = getConstantCode(
                context  = context,
                constant = constant
            )

            ref_count = 0
    else:
        code = getConstantCode(
            context  = context,
            constant = constant
        )

        ref_count = 0

    emit(
        "%s = %s;" % (
            to_name,
            code,
        )
    )

    if ref_count:
        context.addCleanupTempName(to_name)


def getModuleConstantCode(constant):
    assert type(constant) is str

    result = _getConstantInitValueCode(
        constant_value = constant,
        constant_type  = type(constant)
    )

    assert result is not None

    return result


constant_counts = {}

def getConstantInitCodes(module_context):
    decls = []
    inits = []

    sorted_constants = sorted(
        module_context.getConstants(),
        key = lambda k: (len(k), k )
    )

    global_context = module_context.global_context

    for constant_identifier in sorted_constants:
        if not constant_identifier.startswith("const_"):
            continue

        if global_context.getConstantUseCount(constant_identifier ) == 1:
            qualifier = "static "

            constant_value = global_context.constants[constant_identifier]

            _addConstantInitCode(
                emit                = inits.append,
                constant_type       = type(constant_value),
                constant_value      = constant_value,
                constant_identifier = constant_identifier,
                module_level        = True,
                context             = module_context
            )
        else:
            qualifier = "extern "

        decls.append(qualifier + "PyObject *" + constant_identifier + ";")


    return decls, inits


def allocateNestedConstants(module_context):
    def considerForDeferral(constant_value):
        if isMarshalConstant(constant_value):
            return

        module_context.getConstantCode(constant_value)

        constant_type = type(constant_value)

        if constant_type in (tuple, list, set, frozenset):
            for element in constant_value:
                considerForDeferral(element)
        elif constant_type is dict:
            for key, value in iterItems(constant_value):
                considerForDeferral(key)
                considerForDeferral(value)

    for constant_identifier in set(module_context.getConstants()):
        constant_value = module_context.global_context.constants[
            constant_identifier
        ]

        constant_type = type(constant_value)

        if constant_type in (tuple, dict, list, set, frozenset):
            considerForDeferral(constant_value)
