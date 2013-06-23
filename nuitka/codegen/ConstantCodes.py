#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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

from .Pickling import getStreamedConstant
from .CppStrings import encodeString

from .TupleCodes import addMakeTupleUse
from .ListCodes import addMakeListUse
from .DictCodes import addMakeDictUse

# pylint: disable=W0622
from ..__past__ import unicode, long, iterItems
# pylint: enable=W0622

from ..Constants import HashableConstant, constant_builtin_types

import re, struct

def getConstantHandle( context, constant ):
    return context.getConstantHandle( constant )

def getConstantCode( context, constant ):
    constant_identifier = context.getConstantHandle(
        constant = constant
    )

    return constant_identifier.getCode()

# TODO: The determination of this should already happen in Building or in a
# helper not during code generation.
_match_attribute_names = re.compile( r"[a-zA-Z_][a-zA-Z0-9_]*$" )

def getConstantCodeName( context, constant ):
    return context.getConstantHandle( constant, real_use = False ).getCode()

def _isAttributeName( value ):
    return _match_attribute_names.match( value )

_needs_pickle = False

def needsPickleInit():
    return _needs_pickle

def _getUnstreamCode( constant_value, constant_identifier ):
    saved = getStreamedConstant(
        constant_value = constant_value
    )

    assert type( saved ) is bytes

    # We need to remember having to use pickle, pylint: disable=W0603
    global _needs_pickle
    _needs_pickle = True

    return "%s = UNSTREAM_CONSTANT( %s, %d );" % (
        constant_identifier,
        encodeString( saved ),
        len( saved )
    )


def _packFloat( value ):
    return struct.pack( "<d", value )

def _addConstantInitCode( context, emit, constant_type, constant_value,
                          constant_identifier ):
    # This has many cases, that all return, and do a lot.
    #  pylint: disable=R0911,R0912,R0915

    # Use shortest code for ints and longs, except when they are big, then fall
    # fallback to pickling. TODO: Avoid the use of pickle even for larger
    # values.
    if constant_type is int and abs( constant_value ) < 2**31:
        emit(
            "%s = PyInt_FromLong( %s );" % (
                constant_identifier,
                constant_value
            )
        )

        return

    # See above, same for long values. Note: These are of course not existant
    # with Python3 which would have covered it before.
    if constant_type is long and abs( constant_value ) < 2**31:
        emit (
            "%s = PyLong_FromLong( %s );" % (
                constant_identifier,
                constant_value
            )
        )

        return

    # Strings that can be encoded as UTF-8 are done more or less directly. When
    # they cannot be expressed as UTF-8, that is rare not we can indeed use
    # pickling.
    if constant_type is str:
        if str is not unicode:
            emit(
                "%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );" % (
                    constant_identifier,
                    encodeString( constant_value ),
                    len( constant_value ),
                    1 if _isAttributeName( constant_value ) else 0,
                    constant_identifier
                )
            )

            return
        else:
            try:
                encoded = constant_value.encode( "utf-8" )

                emit(
                    "%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );" % (
                        constant_identifier,
                        encodeString( encoded ),
                        len( encoded ),
                        1 if _isAttributeName( constant_value ) else 0,
                        constant_identifier
                    )
                )

                return
            except UnicodeEncodeError:
                # So fall back to below code, which will unstream it then.
                pass

    if constant_type is float:
        emit(
            "%s = UNSTREAM_FLOAT( %s );" % (
                constant_identifier,
                encodeString( _packFloat( constant_value ) )
            )
        )

        return

    if constant_value is None:
        return

    if constant_value is False:
        return

    if constant_value is True:
        return

    if constant_type is dict:
        if constant_value == {}:
            emit( "%s = PyDict_New();" % constant_identifier )
        else:
            length = len( constant_value )
            addMakeDictUse( length )

            for key, value in iterItems( constant_value ):
                _addConstantInitCode(
                    emit                = emit,
                    constant_type       = type( key ),
                    constant_value      = key,
                    constant_identifier = getConstantCodeName( context, key ),
                    context             = context
                )
                _addConstantInitCode(
                    emit                = emit,
                    constant_type       = type( value ),
                    constant_value      = value,
                    constant_identifier = getConstantCodeName( context, value ),
                    context             = context
                )

            emit(
                "%s = MAKE_DICT%d( %s );" % (
                    constant_identifier,
                    length,
                    ", ".join(
                        "%s, %s" % (
                            getConstantCodeName( context, value ),
                            getConstantCodeName( context, key )
                        )
                        for key, value
                        in
                        iterItems( constant_value )
                    )
                )
            )

        return

    if constant_type is tuple:
        if constant_value == ():
            emit( "%s = PyTuple_New( 0 );" % constant_identifier )
        else:
            length = len( constant_value )
            addMakeTupleUse( length )

            # Make elements earlier than tuple itself.
            for element in constant_value:
                _addConstantInitCode(
                    emit                = emit,
                    constant_type       = type( element ),
                    constant_value      = element,
                    constant_identifier = getConstantCodeName( context, element ),
                    context             = context
                )

            emit(
                "%s = MAKE_TUPLE%d( %s );" % (
                    constant_identifier,
                    length,
                    ", ".join(
                        getConstantCodeName( context, element )
                        for element
                        in
                        constant_value
                    )
                )
            )

        return

    if constant_type is list:
        if constant_value == []:
            emit( "%s = PyList_New( 0 );" % constant_identifier )
        else:
            length = len( constant_value )
            addMakeListUse( length )

            # Make elements earlier than list itself.
            for element in constant_value:
                _addConstantInitCode(
                    emit                = emit,
                    constant_type       = type( element ),
                    constant_value      = element,
                    constant_identifier = getConstantCodeName( context, element ),
                    context             = context
                )

            emit(
                "%s = MAKE_LIST%d( %s );" % (
                    constant_identifier,
                    length,
                    ", ".join(
                        getConstantCodeName( context, element )
                        for element
                        in
                        constant_value
                    )
                )
            )

        return

    if constant_type is list and constant_value == []:
        emit( "%s = PyList_New( 0 );" % constant_identifier )

        return

    if constant_type is set and constant_value == set():
        emit( "%s = PySet_New( NULL );" % constant_identifier )

        return

    if constant_type in ( set, frozenset, complex, unicode, int, long, bytes, range ):
        emit(  _getUnstreamCode( constant_value, constant_identifier ) )

        return

    if constant_value in constant_builtin_types:
        return

    assert False, (type(constant_value), constant_value, constant_identifier)

def _lengthKey( value ):
    return len( value[1] ), value[1]

the_contained_constants = {}

def getConstantsInitCode( context ):
    # There are many cases for constants to be created in the most efficient
    # way, pylint: disable=R0912

    statements = []

    all_constants = the_contained_constants
    all_constants.update( context.getConstants() )

    def receiveStatement( statement ):
        assert statement is not None

        if statement not in statements:
            statements.append( statement )

    for ( constant_type, constant_value ), constant_identifier in \
          sorted( all_constants.items(), key = _lengthKey ):
        _addConstantInitCode(
            emit                = receiveStatement,
            constant_type       = constant_type,
            constant_value      = constant_value.getConstant(),
            constant_identifier = constant_identifier,
            context             = context
        )

    return statements

def getConstantsDeclCode( context, for_header ):
    # There are many cases for constants of different types.
    # pylint: disable=R0912
    statements = []

    constants = context.getConstants()

    contained_constants = {}

    def considerForDeferral( constant_value ):
        if constant_value is None:
            return

        if constant_value is False:
            return

        if constant_value is True:
            return

        constant_type = type( constant_value )

        if constant_type is type:
            return

        key = constant_type, HashableConstant( constant_value )

        if key not in contained_constants:
            constant_identifier = getConstantCodeName( context, constant_value )

            contained_constants[ key ] = constant_identifier

            if constant_type in ( tuple, list ):
                for element in constant_value:
                    considerForDeferral( element )

            if constant_type is dict:
                for key, value in iterItems( constant_value ):
                    considerForDeferral( key )
                    considerForDeferral( value )


    for ( constant_type, constant_value ), constant_identifier in sorted( constants.items(), key = _lengthKey ):
        # Need not declare built-in types.
        if constant_type is type:
            continue

        declaration = "PyObject *%s;" % constant_identifier

        if for_header:
            declaration = "extern " + declaration
        else:
            if constant_type in ( tuple, dict, list ):
                considerForDeferral( constant_value.getConstant() )

        statements.append( declaration )

    for key, value in sorted( contained_constants.items(), key = _lengthKey ):
        if key not in constants:
            declaration = "static PyObject *%s;" % value

            statements.append( declaration )

    if not for_header:
        global the_contained_constants
        the_contained_constants = contained_constants

    return statements
