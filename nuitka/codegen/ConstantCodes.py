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


def getConstantsInitCode( context ):
    # There are many cases for constants to be created in the most efficient way,
    # pylint: disable=R0912

    statements = []

    for constant_desc, constant_identifier in context.getConstants():
        constant_type, constant_value = constant_desc
        constant_value = constant_value.getConstant()

        # Use shortest code for ints and longs, except when they are big, then fall
        # fallback to pickling.
        if constant_type is int and abs( constant_value ) < 2**31:
            statements.append(
                "%s = PyInt_FromLong( %s );" % (
                    constant_identifier,
                    constant_value
                )
            )

            continue

        if constant_type is long and abs( constant_value ) < 2**31:
            statements.append(
                "%s = PyLong_FromLong( %s );" % (
                    constant_identifier,
                    constant_value
                )
            )

            continue

        if constant_type is dict and constant_value == {}:
            statements.append(
                "%s = PyDict_New();" % constant_identifier
            )

            continue

        if constant_type is tuple and constant_value == ():
            statements.append(
                "%s = PyTuple_New( 0 );" % constant_identifier
            )

            continue

        if constant_type is list and constant_value == []:
            statements.append(
                "%s = PyList_New( 0 );" % constant_identifier
            )

            continue

        if constant_type is set and constant_value == set():
            statements.append(
                "%s = PySet_New( NULL );" % constant_identifier
            )

            continue

        if constant_type is str:
            if str is not unicode:
                statements.append(
                    '%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );' % (
                        constant_identifier,
                        encodeString( constant_value ),
                        len( constant_value ),
                        1 if _isAttributeName( constant_value ) else 0,
                        constant_identifier
                    )
                )

                continue
            else:
                try:
                    encoded = constant_value.encode( "utf-8" )

                    statements.append(
                        '%s = UNSTREAM_STRING( %s, %d, %d );assert( %s );' % (
                            constant_identifier,
                            encodeString( encoded ),
                            len( encoded ),
                            1 if _isAttributeName( constant_value ) else 0,
                            constant_identifier
                        )
                    )

                    continue
                except UnicodeEncodeError:
                    pass

        if constant_value is None:
            continue

        if constant_value is False:
            continue

        if constant_value is True:
            continue

        if constant_type in ( tuple, list, float, complex, unicode, int, long, dict, frozenset, set, bytes, range ):
            statements.append(
                _getUnstreamCode( constant_value, constant_identifier )
            )

            continue

        assert False, (type(constant_value), constant_value, constant_identifier)

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
