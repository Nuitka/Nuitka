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
"""
Freezer for bytecode compiled modules. Not C++ compiled modules.

This is including modules as bytecode and mostly intended for modules, where
we know compiling it useless or does not make much sense, or for standalone
mode to access modules during CPython library init that cannot be avoided.

The level of compatibility for C++ compiled stuff is so high that this is not
needed except for technical reasons.
"""


from nuitka.codegen import ConstantCodes, CodeTemplates
from nuitka.codegen.Indentation import indented
from nuitka import Options

from logging import info

frozen_modules = []

def addFrozenModule(frozen_module):
    assert not isFrozenModule(frozen_module[0]), frozen_module[0]

    frozen_modules.append(frozen_module)

def getFrozenModuleCount():
    return len(frozen_modules)

def isFrozenModule(module_name):
    for frozen_module in frozen_modules:
        frozen_module_name, _code_data, _is_package, _filename, _is_late = \
          frozen_module

        if module_name == frozen_module_name:
            return True
    else:
        return False

stream_data = ConstantCodes.stream_data

def generateBytecodeFrozenCode():
    frozen_defs = []

    for frozen_module in frozen_modules:
        module_name, code_data, is_package, _filename, _is_late = frozen_module

        size = len(code_data)

        # Packages are indicated with negative size.
        if is_package:
            size = -size

        frozen_defs.append(
            """\
{{ (char *)"{module_name}", (unsigned char *){data}, {size} }},""".format(
                module_name = module_name,
                data        = stream_data.getStreamDataCode(
                    value      = code_data,
                    fixed_size = True
                ),
                size        = size
            )
        )

        if Options.isShowInclusion():
            info("Embedded as frozen module '%s'.", module_name)

    return CodeTemplates.template_frozen_modules % {
        "frozen_modules" : indented(frozen_defs)
    }
