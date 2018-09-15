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
""" Codes for id and hash

"""

from .CodeHelpers import decideConversionCheckNeeded
from .PythonAPICodes import generateCAPIObjectCode


def generateBuiltinIdCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name          = to_name,
        capi             = "PyLong_FromVoidPtr",
        arg_desc         = (
            ("id_arg", expression.getValue()),
        ),
        may_raise        = expression.mayRaiseException(BaseException),
        conversion_check = decideConversionCheckNeeded(to_name, expression),
        source_ref       = expression.getCompatibleSourceReference(),
        emit             = emit,
        context          = context
    )


def generateBuiltinHashCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name          = to_name,
        capi             = "BUILTIN_HASH",
        arg_desc         = (
            ("hash_arg", expression.getValue()),
        ),
        may_raise        = expression.mayRaiseException(BaseException),
        conversion_check = decideConversionCheckNeeded(to_name, expression),
        source_ref       = expression.getCompatibleSourceReference(),
        emit             = emit,
        context          = context
    )
