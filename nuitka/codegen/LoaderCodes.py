#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code to generate and interact with module loaders.

This is for generating the look-up table for the modules included in a binary
or distribution folder.
"""


from nuitka.ModuleRegistry import getUncompiledModules

from . import ConstantCodes
from .Indentation import indented
from .templates.CodeTemplatesLoader import (
    template_metapath_loader_body,
    template_metapath_loader_bytecode_module_entry,
    template_metapath_loader_compiled_module_entry,
    template_metapath_loader_shlib_module_entry,
)


def getModuleMetapathLoaderEntryCode(module):
    module_name = module.getFullName()

    if module.isUncompiledPythonModule():
        code_data = module.getByteCode()
        is_package = module.isUncompiledPythonPackage()

        flags = ["NUITKA_BYTECODE_FLAG"]
        if is_package:
            flags.append("NUITKA_PACKAGE_FLAG")

        return template_metapath_loader_bytecode_module_entry % {
            "module_name": module.getFullName(),
            "bytecode": stream_data.getStreamDataOffset(code_data),
            "size": len(code_data),
            "flags": " | ".join(flags),
        }
    elif module.isPythonShlibModule():
        assert module_name != "__main__"

        return template_metapath_loader_shlib_module_entry % {
            "module_name": module_name
        }
    else:
        flags = []
        if module.isCompiledPythonPackage():
            flags.append("NUITKA_PACKAGE_FLAG")

        return template_metapath_loader_compiled_module_entry % {
            "module_name": module_name,
            "module_identifier": module.getCodeName(),
            "flags": " | ".join(flags),
        }


stream_data = ConstantCodes.stream_data


def getMetapathLoaderBodyCode(other_modules):
    metapath_loader_inittab = []
    metapath_module_decls = []

    for other_module in other_modules:
        metapath_loader_inittab.append(
            getModuleMetapathLoaderEntryCode(module=other_module)
        )

        if other_module.isCompiledPythonModule():
            metapath_module_decls.append(
                "extern PyObject *modulecode_%(module_identifier)s(PyObject *);"
                % {"module_identifier": other_module.getCodeName()}
            )

    for uncompiled_module in getUncompiledModules():
        metapath_loader_inittab.append(
            getModuleMetapathLoaderEntryCode(module=uncompiled_module)
        )

    return template_metapath_loader_body % {
        "metapath_module_decls": indented(metapath_module_decls, 0),
        "metapath_loader_inittab": indented(metapath_loader_inittab),
    }
