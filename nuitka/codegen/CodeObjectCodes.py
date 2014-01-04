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
""" Code generation for code objects.

Right now only the creation is done here. But more should be added later on.
"""

from nuitka.Utils import python_version

from .ConstantCodes import getConstantHandle, getConstantCode
from .Identifiers import Identifier

import hashlib

from nuitka.__past__ import iterItems

# Code objects needed made unique by a key.
code_objects = {}

# False alarms about "hashlib.md5" due to its strange way of defining what is
# exported, pylint won't understand it. pylint: disable=E1101
if python_version < 300:
    def _calcHash(key):
        hash_value = hashlib.md5(
            "%s%s%d%s%d%d%s%s%s%s" % key
        )

        return hash_value.hexdigest()
else:
    def _calcHash(key):
        hash_value = hashlib.md5(
            ("%s%s%d%s%d%d%s%s%s%s" % key).encode("utf-8")
        )

        return hash_value.hexdigest()

def _getCodeObjects():
    return sorted(iterItems(code_objects))

# Sad but true, code objects have these many details that actually are fed from
# all different source, pylint: disable=R0913
def getCodeObjectHandle( context, filename, code_name, line_number, var_names,
                         arg_count, kw_only_count, is_generator, is_optimized,
                         has_starlist, has_stardict ):
    var_names = tuple(var_names)

    assert type(has_starlist) is bool
    assert type(has_stardict) is bool

    key = (
        filename,
        code_name,
        line_number,
        var_names,
        arg_count,
        kw_only_count,
        is_generator,
        is_optimized,
        has_starlist,
        has_stardict
    )

    if key not in code_objects:
        code_objects[ key ] = Identifier(
            "codeobj_%s" % _calcHash(key),
            0
        )

        getConstantHandle(context, filename)
        getConstantHandle(context, code_name)
        getConstantHandle(context, var_names)

    return code_objects[key]


def getCodeObjectsDeclCode(for_header):
    # There are many cases for constants of different types.
    # pylint: disable=R0912
    statements = []

    for _code_object_key, code_identifier in _getCodeObjects():
        declaration = "PyCodeObject *%s;" % code_identifier.getCode()

        if for_header:
            declaration = "extern " + declaration

        statements.append(declaration)

    return statements

def getCodeObjectsInitCode(context):
    statements = []

    for code_object_key, code_identifier in _getCodeObjects():
        co_flags = []

        if code_object_key[2] != 0:
            co_flags.append("CO_NEWLOCALS")

        if code_object_key[6]:
            co_flags.append("CO_GENERATOR")

        if code_object_key[7]:
            co_flags.append("CO_OPTIMIZED")

        if code_object_key[8]:
            co_flags.append("CO_VARARGS")

        if code_object_key[9]:
            co_flags.append("CO_VARKEYWORDS")

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
                code_object_key[4],
                " | ".join(co_flags) or "0",
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
                code_object_key[4],
                code_object_key[5],
                " | ".join(co_flags) or  "0",
            )

        statements.append(code)

    return statements
