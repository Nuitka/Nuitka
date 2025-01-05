#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code generation for networkx module specific stuff. """

from .BuiltinCodes import getBuiltinCallViaSpecCode
from .ImportCodes import getImportModuleNameHardCode
from .JitCodes import addUncompiledFunctionSourceDict


def generateNetworkxUtilsDecoratorsArgmapCallCode(to_name, expression, emit, context):
    """This is for networkx.utils.decorators.argmap calls."""

    # TODO: Have global cached forms of hard attribute lookup results too.
    argmap_class_name = context.allocateTempName("argmap_class", unique=True)

    getImportModuleNameHardCode(
        to_name=argmap_class_name,
        module_name="networkx.utils.decorators",
        import_name="argmap",
        needs_check=False,
        emit=emit,
        context=context,
    )

    addUncompiledFunctionSourceDict(func_value=expression.subnode_func, context=context)

    getBuiltinCallViaSpecCode(
        spec=expression.spec,
        called_name=argmap_class_name,
        to_name=to_name,
        expression=expression,
        emit=emit,
        context=context,
    )


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
