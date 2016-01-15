#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" String related codes, str and unicode.

"""

from nuitka.PythonVersions import python_version

from .PythonAPICodes import generateCAPIObjectCode


def generateBuiltinUnicodeCode(to_name, expression, emit, context):
    encoding = expression.getEncoding()
    errors = expression.getErrors()

    if encoding is None and errors is None:
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "PyObject_Unicode",
            arg_desc   = (
                (
                    "str_arg" if python_version < 300 \
                      else "unicode_arg",
                    expression.getValue()
                ),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    else:
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "TO_UNICODE3",
            arg_desc   = (
                ("unicode_arg", expression.getValue()),
                ("unicode_encoding", encoding),
                ("unicode_errors", errors),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            none_null  = True,
            emit       = emit,
            context    = context,
        )


def generateBuiltinStrCode(to_name, expression, emit, context):
    if python_version < 300:
        generateCAPIObjectCode(
            to_name    = to_name,
            capi       = "PyObject_Str",
            arg_desc   = (
                ("str_arg", expression.getValue()),
            ),
            may_raise  = expression.mayRaiseException(BaseException),
            source_ref = expression.getCompatibleSourceReference(),
            emit       = emit,
            context    = context
        )
    else:
        return generateBuiltinUnicodeCode(to_name, expression, emit, context)


def generateBuiltinChrCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_CHR",
        arg_desc   = (
            ("chr_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )


def generateBuiltinOrdCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name    = to_name,
        capi       = "BUILTIN_ORD",
        arg_desc   = (
            ("ord_arg", expression.getValue()),
        ),
        may_raise  = expression.mayRaiseException(BaseException),
        source_ref = expression.getCompatibleSourceReference(),
        emit       = emit,
        context    = context
    )
