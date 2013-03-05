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
from .Indentation import indented

# pylint: disable=W0622
from ..__past__ import unicode, long
# pylint: enable=W0622

from ..Utils import python_version
from ..Constants import HashableConstant

import re

def getConstantHandle( context, constant ):
    return context.getConstantHandle( constant )

def getConstantCode( context, constant ):
    constant_identifier = context.getConstantHandle(
        constant = constant
    )

    return constant_identifier.getCode()

# TODO: The determination of this should already happen in Building or in a helper not
# during code generation.
_match_attribute_names = re.compile( r"[a-zA-Z_][a-zA-Z0-9_]*$" )

def _isAttributeName( value ):
    return _match_attribute_names.match( value )

def _getUnstreamCode( constant_value, constant_identifier ):
    saved = getStreamedConstant(
        constant_value = constant_value
    )

    assert type( saved ) is bytes

    return "%s = UNSTREAM_CONSTANT( %s, %d );" % (
        constant_identifier,
        encodeString( saved ),
        len( saved )
    )


def _getConstantInitCode( context, constant_type, constant_value, constant_identifier ):
    # Use shortest code for ints and longs, except when they are big, then fall
    # fallback to pickling.
    if constant_type is int and abs( constant_value ) < 2**31:
        return "%s = PyInt_FromLong( %s );" % (
            constant_identifier,
            constant_value
        )

    if constant_type is long and abs( constant_value ) < 2**31:
        return "%s = PyLong_FromLong( %s );" % (
            constant_identifier,
            constant_value
        )

    if constant_type is str:
        if str is not unicode:
            return "%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );" % (
                constant_identifier,
                encodeString( constant_value ),
                len( constant_value ),
                1 if _isAttributeName( constant_value ) else 0,
                constant_identifier
            )
        else:
            try:
                encoded = constant_value.encode( "utf-8" )

                return "%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );" % (
                    constant_identifier,
                    encodeString( encoded ),
                    len( encoded ),
                    1 if _isAttributeName( constant_value ) else 0,
                    constant_identifier
                )
            except UnicodeEncodeError:
                # So fall back to below code, which will unstream it then.
                pass

    if constant_value is None:
        return

    if constant_value is False:
        return

    if constant_value is True:
        return

    if constant_type is dict and constant_value == {}:
        return "%s = PyDict_New();" % constant_identifier

    if constant_type is tuple:
        if constant_value == ():
            return "%s = PyTuple_New( 0 );" % constant_identifier
        else:
            length = len( constant_value )
            context.addMakeTupleUse( length )

            return "%s = MAKE_TUPLE%d( %s );" % (
                constant_identifier,
                len( constant_value ),
                ", ".join(
                    context.getConstantCodeName( element )
                    for element
                    in
                    constant_value
                )
            )

    if constant_type is list and constant_value == []:
        return "%s = PyList_New( 0 );" % constant_identifier

    if constant_type is set and constant_value == set():
        return "%s = PySet_New( NULL );" % constant_identifier

    if constant_type in ( dict, list, set, frozenset, float, complex, unicode, int, long, bytes, range ):
        return _getUnstreamCode( constant_value, constant_identifier )

    assert False, (type(constant_value), constant_value, constant_identifier)

def _lengthKey( value ):
    return len( value[1] ), value[1]

def getConstantsInitCode( context ):
    # There are many cases for constants to be created in the most efficient way,
    # pylint: disable=R0912

    statements = []

    all_constants = context.getContainedConstants()
    all_constants.update( context.getConstants() )

    for ( constant_type, constant_value ), constant_identifier in \
          sorted( all_constants.items(), key = _lengthKey ):
        statements.append(
            _getConstantInitCode(
                constant_type       = constant_type,
                constant_value      = constant_value.getConstant(),
                constant_identifier = constant_identifier,
                context             = context
            )
        )

    for code_object_key, code_identifier in context.getCodeObjects():
        co_flags = []

        if code_object_key[2] != 0:
            co_flags.append( "CO_NEWLOCALS" )

        if code_object_key[5]:
            co_flags.append( "CO_GENERATOR" )

        if code_object_key[6]:
            co_flags.append( "CO_OPTIMIZED" )

        if python_version < 300:
            code = "%s = MAKE_CODEOBJ( %s, %s, %d, %s, %d, %s );" % (
                code_identifier.getCode(),
                getConstantCode(
                    constant = code_object_key[0],
                    context  = context
                ),
                getConstantCode(
                    constant = code_object_key[1],
                    context  = context
                ),
                code_object_key[2],
                getConstantCode(
                    constant = code_object_key[3],
                    context  = context
                ),
                len( code_object_key[3] ),
                " | ".join( co_flags ) or "0",
            )
        else:
            code = "%s = MAKE_CODEOBJ( %s, %s, %d, %s, %d, %d, %s );" % (
                code_identifier.getCode(),
                getConstantCode(
                    constant = code_object_key[0],
                    context  = context
                ),
                getConstantCode(
                    constant = code_object_key[1],
                    context  = context
                ),
                code_object_key[2],
                getConstantCode(
                    constant = code_object_key[3],
                    context  = context
                ),
                len( code_object_key[3] ),
                code_object_key[4],
                " | ".join( co_flags ) or  "0",
            )


        statements.append( code )

    return indented( statements )

def getConstantsDeclCode( context, for_header ):
    statements = []

    for _code_object_key, code_identifier in context.getCodeObjects():
        declaration = "PyCodeObject *%s;" % code_identifier.getCode()

        if for_header:
            declaration = "extern " + declaration

        statements.append( declaration )

    constants = context.getConstants()
    contained_constants = {}

    def considerForDeferral( constant_value ):
        if constant_value is None:
            return

        if constant_value is False:
            return

        if constant_value is True:
            return

        constant_identifier = context.getConstantCodeName( constant_value )

        constant_type = type( constant_value )
        key = constant_type, HashableConstant( constant_value )

        if key not in contained_constants:
            contained_constants[ key ] = constant_identifier

            if constant_type is tuple:
                for element in constant_value:
                    considerForDeferral( element )


    for ( constant_type, constant_value ), constant_identifier in sorted( constants.items(), key = _lengthKey ):
        declaration = "PyObject *%s;" % constant_identifier

        if for_header:
            declaration = "extern " + declaration
        else:
            if constant_type is tuple:
                constant_value = constant_value.getConstant()

                for element in constant_value:
                    considerForDeferral( element )

        statements.append( declaration )

    for key, value in sorted( contained_constants.items(), key = _lengthKey ):
        if key not in constants:
            declaration = "static PyObject *%s;" % value

            statements.append( declaration )

    if not for_header:
        context.setContainedConstants( contained_constants )

    return "\n".join( statements )
