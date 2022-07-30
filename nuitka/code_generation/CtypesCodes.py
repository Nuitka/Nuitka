#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code generation for ctypes module stuff. """

from .BuiltinCodes import getBuiltinCallViaSpecCode
from .ImportCodes import getImportModuleNameHardCode


def generateCtypesCdllCallCode(to_name, expression, emit, context):
    # TODO: Have global cached forms of hard attribute lookup results too.
    ctypes_cdll_class = context.allocateTempName("ctypes_cdll_class", unique=True)

    getImportModuleNameHardCode(
        to_name=ctypes_cdll_class,
        module_name="ctypes",
        import_name="CDLL",
        needs_check=False,
        emit=emit,
        context=context,
    )

    getBuiltinCallViaSpecCode(
        spec=expression.spec,
        called_name=ctypes_cdll_class,
        to_name=to_name,
        expression=expression,
        emit=emit,
        context=context,
    )
