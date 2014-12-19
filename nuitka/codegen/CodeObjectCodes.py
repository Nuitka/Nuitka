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

from .ConstantCodes import getConstantCode


def getCodeObjectsDeclCode(context):
    statements = []

    for _code_object_key, code_identifier in context.getCodeObjects():
        declaration = "static PyCodeObject *%s;" % code_identifier

        statements.append(declaration)

    return statements

def getCodeObjectsInitCode(context):
    statements = []

    for code_object_key, code_identifier in context.getCodeObjects():
        co_flags = []

        if code_object_key[2] != 0 and \
           (code_object_key[7] or python_version < 340):
            co_flags.append("CO_NEWLOCALS")

        if code_object_key[6]:
            co_flags.append("CO_GENERATOR")

        if code_object_key[7]:
            co_flags.append("CO_OPTIMIZED")

        if code_object_key[8]:
            co_flags.append("CO_VARARGS")

        if code_object_key[9]:
            co_flags.append("CO_VARKEYWORDS")

        if not code_object_key[10]:
            co_flags.append("CO_NOFREE")

        co_flags.extend(code_object_key[11])

        if python_version < 300:
            code = "%s = MAKE_CODEOBJ( %s, %s, %d, %s, %d, %s );" % (
                code_identifier,
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
                code_identifier,
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
