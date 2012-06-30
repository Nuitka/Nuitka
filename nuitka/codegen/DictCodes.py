#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
""" Code generation for dicts.

Right now only the creation is done here. But more should be added later on.
"""

from .Identifiers import getCodeTemporaryRefs, CallIdentifier

def getDictionaryCreationCode( context, keys, values ):
    key_codes = getCodeTemporaryRefs( keys )
    value_codes = getCodeTemporaryRefs( values )

    arg_codes = []

    # Strange as it is, CPython evalutes the key/value pairs strictly in order, but for
    # each pair, the value first.
    for key_code, value_code in zip( key_codes, value_codes ):
        arg_codes.append( value_code )
        arg_codes.append( key_code )

    args_length = len( keys )

    context.addMakeDictUse( args_length )

    return CallIdentifier(
        called  = "MAKE_DICT%d" % args_length,
        args    = arg_codes
    )
