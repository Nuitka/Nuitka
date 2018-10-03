#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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

This deals with constants, there creation, there access, and some checks about
them. Even mutable constants should not change during the course of the
program.

There are shared constants, which are created for multiple modules to use, you
can think of them as globals. And there are module local constants, which are
for a single module only.

"""

import ctypes
import marshal
import re
import struct
import sys
from logging import warning

from nuitka import Options
from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
    iterItems,
    long,
    unicode,
    xrange
)
from nuitka.Builtins import builtin_named_values, builtin_named_values_list
from nuitka.Constants import (
    NoneType,
    compareConstants,
    getConstantWeight,
    isMutable
)

from .BlobCodes import StreamData
from .Emission import SourceCodeCollector
from .Indentation import indented
from .templates.CodeTemplatesConstants import template_constants_reading


def generateConstantReferenceCode(to_name, expression, emit, context):
    """ Assign the constant behind the expression to to_name."""

    getConstantAccess(
        to_name  = to_name,
        constant = expression.getConstant(),
        emit     = emit,
        context  = context
    )


def generateConstantNoneReferenceCode(to_name, expression, emit, context):
    """ Assign 'None' to to_name."""

    # No context or other knowledge needed, pylint: disable=unused-argument

    emit(
        "%s = Py_None;" % to_name
    )


def generateConstantTrueReferenceCode(to_name, expression, emit, context):
    """ Assign 'True' to to_name."""

    # No context or other knowledge needed, pylint: disable=unused-argument

    if to_name.c_type == "nuitka_bool":
        emit(
            "%s = NUITKA_BOOL_TRUE;" % to_name
        )
    else:
        emit(
            "%s = Py_True;" % to_name
        )


def generateConstantFalseReferenceCode(to_name, expression, emit, context):
    """ Assign 'False' to to_name."""

    # No context or other knowledge needed, pylint: disable=unused-argument

    if to_name.c_type == "nuitka_bool":
        emit(
            "%s = NUITKA_BOOL_FALSE;" % to_name
        )
    else:
        emit(
            "%s = Py_False;" % to_name
        )


def generateConstantEllipsisReferenceCode(to_name, expression, emit, context):
    """ Assign 'Ellipsis' to to_name."""

    # No context or other knowledge needed, pylint: disable=unused-argument

    emit(
        "%s = Py_Ellipsis;" % to_name
    )


# One global stream of constant information. In the future it might make
# sense to have per module ones, for better locality of indexes within it,
# but we don't do this yet.
stream_data = StreamData()

# TODO: The determination of this should already happen in Building or in a
# helper not during code generation.
_match_attribute_names = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*$")

def _isAttributeName(value):
    # TODO: The exception is to make sure we intern the ".0" argument name
    # used for generator expressions, iterator value.
    return _match_attribute_names.match(value) or value == ".0"

sizeof_long = ctypes.sizeof(ctypes.c_long)

max_unsigned_long = 2**(sizeof_long*8)-1

# The gcc gives a warning for -2**sizeof_long*8-1, which is still an "int", but
# seems to not work (without warning) as literal, so avoid it.
min_signed_long = -(2**(sizeof_long*8-1)-1)

done = set()

def _getConstantInitValueCode(constant_value, constant_type):
    """ Return code, if possible, to create a constant.

        It's only used for module local constants, like error messages, and
        provides no caching of the values. When it returns "None", it is in
        error.
    """

    # This function is a case driven by returns, pylint: disable=too-many-return-statements

    if constant_type is unicode:
        # Python3: Strings that can be encoded as UTF-8 are done more or less
        # directly. When they cannot be expressed as UTF-8, that is rare not we
        # can indeed use pickling.
        try:
            encoded = constant_value.encode("utf-8")

            if str is bytes:
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
            # TODO: try and use "surrogateescape" for this
            return None
    elif constant_type is str:
        assert str is bytes

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
        assert str is not bytes

        return "UNSTREAM_BYTES( %s )" % (
            stream_data.getStreamDataCode(constant_value)
        )
    else:
        return None


def decideMarshal(constant_value):
    """ Decide of a constant can be created using "marshal" module methods.

        This is not the case for everything. A prominent exception is types,
        they are constants, but the "marshal" module refuses to work with
        them.
    """

    # Many cases to deal with, pylint: disable=too-many-return-statements

    constant_type = type(constant_value)

    if constant_type is type:
        # Types cannot be marshaled, there is no choice about it.
        return False
    elif constant_type is dict:
        # Look at all the keys an values, if one of it cannot be marshaled,
        # or should not, that is it.
        for key, value in iterItems(constant_value):
            if not decideMarshal(key):
                return False
            if not decideMarshal(value):
                return False
    elif constant_type in (tuple, list, set, frozenset):
        for element_value in constant_value:
            if not decideMarshal(element_value):
                return False
    elif constant_type is xrange:
        return False
    elif constant_type is slice:
        return False

    return True


def isMarshalConstant(constant_value):
    """ Decide if we want to use marshal to create a constant.

        The reason we do this, is because creating dictionaries with 700
        elements creates a lot of C code, while gaining usually no performance
        at all. The MSVC compiler is especially notorious about hanging like
        forever with this active, due to its optimizer not scaling.

        Therefore we use a constant "weight" (how expensive it is), and apply
        that to decide.

        If marshal is not possible, or constant "weight" is too large, we
        don't do it. Also, for some constants, marshal can fail, and return
        other values. Check that too. In that case, we have to create it.
    """

    if not decideMarshal(constant_value):
        return False

    if getConstantWeight(constant_value) < 20:
        return False

    try:
        marshal_value = marshal.dumps(constant_value)
    except ValueError:
        if Options.isDebug():
            warning("Failed to marshal constant %r." % constant_value)

        return False

    restored = marshal.loads(marshal_value)

    r = compareConstants(constant_value, restored)
    if not r:
        pass
        # TODO: Potentially warn about these, where that is not the case.

    return r


def getMarshalCode(constant_identifier, constant_value, emit):
    """ Force the marshal of a value.

    """
    marshal_value = marshal.dumps(constant_value)
    restored = marshal.loads(marshal_value)

    assert compareConstants(constant_value, restored)

    emit(
        "%s = PyMarshal_ReadObjectFromString( (char *)%s );" % (
            constant_identifier,
            stream_data.getStreamDataCode(marshal_value)
        )
    )


def attemptToMarshal(constant_identifier, constant_value, emit):
    """ Try and marshal a value, if so decided. Indicate with return value.

        See above for why marshal is only used in problematic cases.
    """

    if not isMarshalConstant(constant_value):
        return False

    marshal_value = marshal.dumps(constant_value)
    restored = marshal.loads(marshal_value)

    # TODO: The check in isMarshalConstant is currently preventing this from
    # happening.
    if not compareConstants(constant_value, restored):
        warning("Problem with marshal of constant %r", constant_value)

        return False

    emit(
        "%s = PyMarshal_ReadObjectFromString( (char *)%s );" % (
            constant_identifier,
            stream_data.getStreamDataCode(marshal_value)
        )
    )

    return True

def _addConstantInitCode(context, emit, check, constant_type, constant_value,
                         constant_identifier, module_level):
    """ Emit code for a specific constant to be prepared during init.

        This may be module or global init. Code makes sure that nested
        constants belong into the same scope.
    """
    # Got a couple of values to dodge, pylint: disable=too-many-return-statements

    if constant_value is None:
        return
    elif constant_value is False:
        return
    elif constant_value is True:
        return
    elif constant_value is Ellipsis:
        return
    elif constant_value is NotImplemented:
        return
    elif type(constant_value) is type:
        return
    elif constant_identifier in done:
        # Do not repeat ourselves.
        return

    if Options.shallTraceExecution():
        emit("""NUITKA_PRINT_TRACE("Creating constant: %s");""" % constant_identifier)

    # Then it's a real named constant not yet created.
    __addConstantInitCode(context, emit, check, constant_type, constant_value,
                          constant_identifier, module_level)

    # In debug mode, lets check if the constants somehow change behind our
    # back, add those values too.
    if Options.isDebug():
        emit(
             """\
hash_%(constant_identifier)s = DEEP_HASH( %(constant_identifier)s );""" % {
             "constant_identifier" : constant_identifier
             }
        )

        check(
            """\
CHECK_OBJECT( %(constant_identifier)s );
assert( hash_%(constant_identifier)s == DEEP_HASH( %(constant_identifier)s ) );""" % {
             "constant_identifier" : constant_identifier
             }
        )


def __addConstantInitCode(context, emit, check, constant_type, constant_value,
                          constant_identifier, module_level):
    """ Emit code for a specific constant to be prepared during init.

        This may be module or global init. Code makes sure that nested
        constants belong into the same scope.
    """
    # This has many cases, that all return, and do a lot.
    # pylint: disable=too-many-branches,too-many-locals,too-many-return-statements,too-many-statements

    # For the module level, we only mean to create constants that are used only
    # inside of it. For the global level, it must must be single use.
    if module_level:
        if context.global_context.getConstantUseCount(constant_identifier) != 1:
            return
    else:
        if context.getConstantUseCount(constant_identifier) == 1:
            return

    # Adding it to "done". We cannot have recursive constants, so this is OK
    # to be done now.
    done.add(constant_identifier)

    # Use shortest code for ints and longs.
    if constant_type is long:
        # See above, same for long values. Note: These are of course not
        # existent with Python3 which would have covered it before.
        if 0 <= constant_value <= max_unsigned_long:
            emit (
                "%s = PyLong_FromUnsignedLong( %sul );" % (
                    constant_identifier,
                    constant_value
                )
            )

            return
        elif 0 > constant_value >= min_signed_long:
            emit (
                "%s = PyLong_FromLong( %sl );" % (
                    constant_identifier,
                    constant_value
                )
            )

            return
        elif constant_value == min_signed_long-1:
            # There are compilers out there, that give warnings for the literal
            # MININT when used. We work around that warning here.
            emit(
                """\
%s = PyLong_FromLong( %sl ); // To be corrected with -1 in-place next lines.
CHECK_OBJECT( const_int_pos_1 );
%s = PyNumber_InPlaceSubtract( %s, PyLong_FromLong( 1 ) );""" % (
                    constant_identifier,
                    min_signed_long,
                    constant_identifier,
                    constant_identifier
                )
            )

            return
        else:
            getMarshalCode(
                constant_identifier = constant_identifier,
                constant_value      = constant_value,
                emit                = emit
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
            # There are compilers out there, that give warnings for the literal
            # MININT when used. We work around that warning here.
            assert constant_value == min_signed_long-1

            emit(
                """\
%s = PyInt_FromLong( %sl );  // To be corrected in next line.
%s = PyNumber_InPlaceSubtract( %s, PyInt_FromLong( 1 ) );""" % (
                    constant_identifier,
                    min_signed_long,
                    constant_identifier,
                    constant_identifier
                )
            )

            return

    if constant_type is unicode:
        try:
            encoded = constant_value.encode("utf-8")

            if str is bytes:
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
            getMarshalCode(
                constant_identifier = constant_identifier,
                constant_value      = constant_value,
                emit                = emit
            )

            return

    elif constant_type is str:
        # Python3: Strings that can be encoded as UTF-8 are done more or less
        # directly. When they cannot be expressed as UTF-8, that is rare not we
        # can indeed use pickling.
        assert str is bytes

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
        # Python3 only, for Python2, bytes do not happen.
        assert str is not bytes

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
                    value      = struct.pack("<d", constant_value),
                    fixed_size = True
                )
            )
        )

        return

    if constant_type is dict:
        # Not all dictionaries can or should be marshaled. For small ones,
        # or ones with strange values, like "{1:type}", we have to do it.

        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        emit(
            "%s = _PyDict_NewPresized( %d );" % (
                constant_identifier,
                len(constant_value)
            )
        )

        for key, value in iterItems(constant_value):
            key_name = context.getConstantCode(key)
            _addConstantInitCode(
                emit                = emit,
                check               = check,
                constant_type       = type(key),
                constant_value      = key,
                constant_identifier = key_name,
                module_level        = module_level,
                context             = context
            )

            value_name = context.getConstantCode(value)
            _addConstantInitCode(
                emit                = emit,
                check               = check,
                constant_type       = type(value),
                constant_value      = value,
                constant_identifier = value_name,
                module_level        = module_level,
                context             = context
            )

            # TODO: Error checking for debug.
            emit(
                "PyDict_SetItem( %s, %s, %s );" % (
                    constant_identifier,
                    key_name,
                    value_name
                )
            )

        emit(
            "assert( PyDict_Size( %s ) == %d );" % (
                constant_identifier,
                len(constant_value)
            )
        )

        return

    if constant_type is tuple:
        # Not all tuples can or should be marshaled. For small ones,
        # or ones with strange values, like "(type,)", we have to do it.

        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        emit(
            "%s = PyTuple_New( %d );" % (
                constant_identifier,
                len(constant_value)
            )
        )

        for count, element_value in enumerate(constant_value):
            element_name = context.getConstantCode(
                constant = element_value
            )

            _addConstantInitCode(
                emit                = emit,
                check               = check,
                constant_type       = type(element_value),
                constant_value      = element_value,
                constant_identifier = context.getConstantCode(
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
        # Not all lists can or should be marshaled. For small ones,
        # or ones with strange values, like "[type]", we have to do it.

        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        emit(
            "%s = PyList_New( %d );" % (
                constant_identifier,
                len(constant_value)
            )
        )

        for count, element_value in enumerate(constant_value):
            element_name = context.getConstantCode(
                constant = element_value
            )

            _addConstantInitCode(
                emit                = emit,
                check               = check,
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

    if constant_type is set or constant_type is frozenset:
        # Not all sets can or should be marshaled. For small ones,
        # or ones with strange values, like "{type}", we have to do it.
        if attemptToMarshal(constant_identifier, constant_value, emit):
            return

        # Special handling for empty frozensets.
        if not constant_value and constant_type is frozenset:
            emit(
                "%s = PyObject_CallFunction((PyObject*)&PyFrozenSet_Type, NULL);" % (
                    constant_identifier,
                )
            )

            return


        # TODO: Hinting size is really not possible?
        emit(
            "%s = %s( NULL );" % (
                constant_identifier,
                "PySet_New" if constant_type is set else "PyFrozenSet_New"
            )
        )

        for element_value in constant_value:
            element_name = context.getConstantCode(element_value)

            _addConstantInitCode(
                emit                = emit,
                check               = check,
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

        emit(
            "assert( PySet_Size( %s ) == %d );" % (
                constant_identifier,
                len(constant_value)
            )
        )

        return

    if constant_type is slice:
        slice1_name = context.getConstantCode(constant_value.start)
        _addConstantInitCode(
            emit                = emit,
            check               = check,
            constant_type       = type(constant_value.start),
            constant_value      = constant_value.start,
            constant_identifier = slice1_name,
            module_level        = module_level,
            context             = context
        )
        slice2_name = context.getConstantCode(constant_value.stop)
        _addConstantInitCode(
            emit                = emit,
            check               = check,
            constant_type       = type(constant_value.stop),
            constant_value      = constant_value.stop,
            constant_identifier = slice2_name,
            module_level        = module_level,
            context             = context
        )
        slice3_name = context.getConstantCode(constant_value.step)
        _addConstantInitCode(
            emit                = emit,
            check               = check,
            constant_type       = type(constant_value.step),
            constant_value      = constant_value.step,
            constant_identifier = slice3_name,
            module_level        = module_level,
            context             = context
        )

        emit(
             "%s = PySlice_New( %s, %s, %s );" % (
                constant_identifier,
                slice1_name,
                slice2_name,
                slice3_name
            )
        )

        return

    if constant_type is xrange:
        # Strip const_xrange.
        assert constant_identifier.startswith("const_xrange_")

        # For Python2, xrange needs only long values to be created, so avoid objects.
        range_args =  constant_identifier[13:].split('_')

        # Default start.
        if len(range_args) == 1:
            range_args.insert(0, '0')

        # Default step
        if len(range_args) < 3:
            range_args.append('1')


        # Negative values are encoded with "neg" prefix.
        range_args = [
            int(range_arg.replace("neg", '-'))
            for range_arg in
            range_args
        ]

        if xrange is not range:
            emit(
                 "%s = MAKE_XRANGE( %s, %s, %s );" % (
                    constant_identifier,
                    range_args[0],
                    range_args[1],
                    range_args[2]
                )
            )
        else:
            range1_name = context.getConstantCode(range_args[0])
            _addConstantInitCode(
                emit                = emit,
                check               = check,
                constant_type       = type(range_args[0]),
                constant_value      = range_args[0],
                constant_identifier = range1_name,
                module_level        = module_level,
                context             = context
            )
            range2_name = context.getConstantCode(range_args[1])
            _addConstantInitCode(
                emit                = emit,
                check               = check,
                constant_type       = type(range_args[1]),
                constant_value      = range_args[1],
                constant_identifier = range2_name,
                module_level        = module_level,
                context             = context
            )
            range3_name = context.getConstantCode(range_args[2])
            _addConstantInitCode(
                emit                = emit,
                check               = check,
                constant_type       = type(range_args[2]),
                constant_value      = range_args[2],
                constant_identifier = range3_name,
                module_level        = module_level,
                context             = context
            )

            emit(
                 "%s = BUILTIN_XRANGE3( %s, %s, %s );" % (
                    constant_identifier,
                    range1_name,
                    range2_name,
                    range3_name
                )
            )

        return

    if constant_type is bytearray:
        emit(
            "%s = UNSTREAM_BYTEARRAY( %s );" % (
                constant_identifier,
                stream_data.getStreamDataCode(bytes(constant_value))
            )
        )

        return

    if constant_type is complex:
        getMarshalCode(
            constant_identifier = constant_identifier,
            constant_value      = constant_value,
            emit                = emit
        )

        return

    if constant_value in builtin_named_values_list:
        builtin_name = builtin_named_values[constant_value]
        builtin_identifier = context.getConstantCode(builtin_name)

        _addConstantInitCode(
            emit                = emit,
            check               = check,
            constant_type       = type(builtin_name),
            constant_value      = builtin_name,
            constant_identifier = builtin_identifier,
            module_level        = module_level,
            context             = context
        )

        emit(
            "%s = LOOKUP_BUILTIN( %s );" % (
                constant_identifier,
                builtin_identifier
            )
        )

        return


    # Must not reach this, if we did, it's in error, and we need to know.
    assert False, (type(constant_value), constant_value, constant_identifier)


def getConstantsInitCode(context):
    emit = SourceCodeCollector()

    check = SourceCodeCollector()

    # Sort items by length and name, so we are deterministic and pretty.
    sorted_constants = sorted(
        iterItems(context.getConstants()),
        key = lambda k: (len(k[0]), k[0])
    )

    for constant_identifier, constant_value in sorted_constants:
        _addConstantInitCode(
            emit                = emit,
            check               = check,
            constant_type       = type(constant_value),
            constant_value      = constant_value,
            constant_identifier = constant_identifier,
            module_level        = False,
            context             = context
        )

    return emit.codes, check.codes


def getConstantsDeclCode(context):
    statements = []

    # Sort items by length and name, so we are deterministic and pretty.
    sorted_constants = sorted(
        iterItems(context.getConstants()),
        key = lambda k: (len(k[0]), k[0])
    )

    for constant_identifier, constant_value in sorted_constants:
        # Need not declare built-in types.
        if constant_value is None:
            continue
        if constant_value is False:
            continue
        if constant_value is True:
            continue
        if constant_value is Ellipsis:
            continue
        if constant_value is NotImplemented:
            continue
        if type(constant_value) is type:
            continue

        if context.getConstantUseCount(constant_identifier) != 1:
            statements.append("PyObject *%s;" % constant_identifier)

            if Options.isDebug():
                statements.append("Py_hash_t hash_%s;" % constant_identifier)

    return statements


def getConstantAccess(to_name, constant, emit, context):
    # Many cases, because for each type, we may copy or optimize by creating
    # empty.  pylint: disable=too-many-branches,too-many-statements

    if to_name.c_type == "nuitka_bool" and Options.isDebug():
        assert False, constant

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
                code = "DEEP_COPY( %s )" % context.getConstantCode(constant)
            else:
                code = "PyDict_Copy( %s )" % context.getConstantCode(constant)
        else:
            code = "PyDict_New()"

        ref_count = 1
    elif type(constant) is set:
        if constant:
            code = "PySet_New( %s )" % context.getConstantCode(constant)
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
                code = "DEEP_COPY( %s )" % context.getConstantCode(constant)
            else:
                code = "LIST_COPY( %s )" % context.getConstantCode(constant)
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
            code = "DEEP_COPY( %s )" % context.getConstantCode(constant)

            ref_count = 1
        else:
            code = context.getConstantCode(constant)

            ref_count = 0
    elif type(constant) is bytearray:
        code = "BYTEARRAY_COPY( %s )"  % context.getConstantCode(constant)
        ref_count = 1
    else:
        code = context.getConstantCode(
            constant = constant
        )

        ref_count = 0

    if to_name.c_type == "PyObject *":
        value_name = to_name
    else:
        value_name = context.allocateTempName("constant_value")

    emit(
        "%s = %s;" % (
            value_name,
            code,
        )
    )

    if ref_count:
        context.addCleanupTempName(value_name)

    if to_name is not value_name:
        to_name.getCType().emitAssignConversionCode(
            to_name     = to_name,
            value_name  = value_name,
            needs_check = False,
            emit        = emit,
            context     = context
        )


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
    inits = SourceCodeCollector()
    checks = SourceCodeCollector()

    sorted_constants = sorted(
        module_context.getConstants(),
        key = lambda k: (len(k[0]), k[0])
    )

    global_context = module_context.global_context

    for constant_identifier in sorted_constants:
        if not constant_identifier.startswith("const_"):
            continue

        if global_context.getConstantUseCount(constant_identifier) == 1:
            qualifier = "static"

            constant_value = global_context.constants[constant_identifier]

            _addConstantInitCode(
                emit                = inits,
                check               = checks,
                constant_type       = type(constant_value),
                constant_value      = constant_value,
                constant_identifier = constant_identifier,
                module_level        = True,
                context             = module_context
            )
        else:
            qualifier = "extern"

        decls.append(
            "%s PyObject *%s;" % (
                qualifier,
                constant_identifier
            )
        )

        if Options.isDebug():
            decls.append(
                "%s Py_hash_t hash_%s;" % (
                    qualifier,
                    constant_identifier
                )
            )

    return decls, inits.codes, checks.codes


def allocateNestedConstants(module_context):
    # Lots of types to deal with.

    def considerForDeferral(constant_value):
        module_context.getConstantCode(constant_value)

        if isMarshalConstant(constant_value):
            return

        constant_type = type(constant_value)

        if constant_type in (tuple, list, set, frozenset):
            for element in constant_value:
                considerForDeferral(element)
        elif constant_type is dict:
            for key, value in iterItems(constant_value):
                considerForDeferral(key)
                considerForDeferral(value)
        elif constant_type is slice:
            considerForDeferral(constant_value.start)
            considerForDeferral(constant_value.step)
            considerForDeferral(constant_value.stop)
        elif constant_type is xrange:
            if xrange is range:
                # For Python2 ranges, we use C long values directly.
                considerForDeferral(constant_value.start)
                considerForDeferral(constant_value.step)
                considerForDeferral(constant_value.stop)
        elif constant_value in builtin_named_values_list:
            considerForDeferral(builtin_named_values[constant_value])

    for constant_identifier in set(module_context.getConstants()):
        constant_value = module_context.global_context.constants[
            constant_identifier
        ]

        constant_type = type(constant_value)

        if constant_type in (tuple, dict, list, set, frozenset, slice, xrange):
            considerForDeferral(constant_value)
        elif constant_type in (str, NoneType, int, long):
            pass
        elif constant_value in builtin_named_values_list:
            considerForDeferral(builtin_named_values[constant_value])


def getConstantsDefinitionCode(context):
    """ Create the code code "__constants.c" file.

        This needs to create code to make all global constants (used in more
        than one module) and create them.

    """
    constant_inits, constant_checks = getConstantsInitCode(
        context = context
    )

    constant_declarations = getConstantsDeclCode(
        context = context
    )

    if Options.shallMakeModule():
        sys_executable = None
    else:
        sys_executable = context.getConstantCode(sys.executable)

    return template_constants_reading % {
        "constant_declarations" : '\n'.join(constant_declarations),
        "constant_inits"        : indented(constant_inits),
        "constant_checks"       : indented(constant_checks),
        "sys_executable"        : sys_executable
    }
