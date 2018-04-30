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
""" Code to generate and interact with module loaders.

This is for generating the look-up table for the modules included in a binary
or distribution folder.
"""


from nuitka.ModuleRegistry import getUncompiledNonTechnicalModules

from . import ConstantCodes
from .Indentation import indented
from .templates.CodeTemplatesLoader import (
    template_metapath_loader_body,
    template_metapath_loader_bytecode_module_entry,
    template_metapath_loader_compiled_module_entry,
    template_metapath_loader_compiled_package_entry,
    template_metapath_loader_shlib_module_entry
)


def getModuleMetapathLoaderEntryCode(module_name, module_identifier,
                                     is_shlib, is_package):
    if is_shlib:
        assert module_name != "__main__"
        assert not is_package

        return template_metapath_loader_shlib_module_entry % {
            "module_name" : module_name
        }
    elif is_package:
        return template_metapath_loader_compiled_package_entry % {
            "module_name"       : module_name,
            "module_identifier" : module_identifier,
        }
    else:
        return template_metapath_loader_compiled_module_entry % {
            "module_name"       : module_name,
            "module_identifier" : module_identifier,
        }


stream_data = ConstantCodes.stream_data

def getMetapathLoaderBodyCode(other_modules):
    metapath_loader_inittab = []
    metapath_module_decls = []

    for other_module in other_modules:
        if other_module.isUncompiledPythonModule():
            code_data = other_module.getByteCode()
            is_package = other_module.isUncompiledPythonPackage()

            flags = ["NUITKA_BYTECODE_FLAG"]
            if is_package:
                flags.append("NUITKA_PACKAGE_FLAG")

            metapath_loader_inittab.append(
                template_metapath_loader_bytecode_module_entry % {
                    "module_name" : other_module.getFullName(),
                    "bytecode"    : stream_data.getStreamDataOffset(code_data),
                    "size"        : len(code_data),
                    "flags"       : " | ".join(flags)
                }
            )
        else:
            metapath_loader_inittab.append(
                getModuleMetapathLoaderEntryCode(
                    module_name       = other_module.getFullName(),
                    module_identifier = other_module.getCodeName(),
                    is_shlib          = other_module.isPythonShlibModule(),
                    is_package        = other_module.isCompiledPythonPackage()
                )
            )

        if other_module.isCompiledPythonModule():
            metapath_module_decls.append(
                "MOD_INIT_DECL( %s );" % other_module.getCodeName()
            )

    for uncompiled_module in getUncompiledNonTechnicalModules():
        code_data = uncompiled_module.getByteCode()
        is_package = uncompiled_module.isUncompiledPythonPackage()

        flags = ["NUITKA_BYTECODE_FLAG"]
        if is_package:
            flags.append("NUITKA_PACKAGE_FLAG")

        metapath_loader_inittab.append(
            template_metapath_loader_bytecode_module_entry % {
                "module_name" : uncompiled_module.getFullName(),
                "bytecode"    : stream_data.getStreamDataOffset(code_data),
                "size"        : len(code_data),
                "flags"       : " | ".join(flags)
            }
        )


    return template_metapath_loader_body % {
        "metapath_module_decls"   : indented(metapath_module_decls, 0),
        "metapath_loader_inittab" : indented(metapath_loader_inittab)
    }
