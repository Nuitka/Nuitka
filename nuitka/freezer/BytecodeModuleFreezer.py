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
"""
Freezer for bytecode compiled modules. Not real C compiled modules.

This is including modules as bytecode and mostly intended for modules, where
we know compiling it useless or does not make much sense, or for standalone
mode to access modules during CPython library init that cannot be avoided.

The level of compatibility for C compiled stuff is so high that this is not
needed except for technical reasons.
"""


from logging import info

from nuitka import Options
from nuitka.codegen import ConstantCodes
from nuitka.codegen.Indentation import indented
from nuitka.codegen.templates.CodeTemplatesFreezer import (
    template_frozen_modules
)
from nuitka.ModuleRegistry import getUncompiledTechnicalModules

stream_data = ConstantCodes.stream_data

def generateBytecodeFrozenCode():
    frozen_defs = []

    for uncompiled_module in getUncompiledTechnicalModules():
        module_name = uncompiled_module.getFullName()
        code_data = uncompiled_module.getByteCode()
        is_package = uncompiled_module.isUncompiledPythonPackage()

        size = len(code_data)

        # Packages are indicated with negative size.
        if is_package:
            size = -size

        frozen_defs.append(
            """\
{{ "{module_name}", {start}, {size} }},""".format(
                module_name = module_name,
                start       = stream_data.getStreamDataOffset(code_data),
                size        = size
            )
        )

        if Options.isShowInclusion():
            info("Embedded as frozen module '%s'.", module_name)

    return template_frozen_modules % {
        "frozen_modules" : indented(frozen_defs, 2)
    }
