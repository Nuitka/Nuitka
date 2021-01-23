#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

Also this prepares tables for the freezer for bytecode compiled modules. Not
real C compiled modules.

This is including modules as bytecode and mostly intended for modules, where
we know compiling it useless or does not make much sense, or for standalone
mode to access modules during CPython library init that cannot be avoided.

The level of compatibility for C compiled stuff is so high that this is not
needed except for technical reasons.
"""

from nuitka import Options
from nuitka.ModuleRegistry import (
    getDoneModules,
    getUncompiledModules,
    getUncompiledTechnicalModules,
)
from nuitka.Tracing import inclusion_logger

from .Indentation import indented
from .templates.CodeTemplatesLoader import (
    template_metapath_loader_body,
    template_metapath_loader_bytecode_module_entry,
    template_metapath_loader_compiled_module_entry,
    template_metapath_loader_shlib_module_entry,
)


def getModuleMetapathLoaderEntryCode(module, bytecode_accessor):
    module_name = module.getFullName()

    if module.isUncompiledPythonModule():
        code_data = module.getByteCode()
        is_package = module.isUncompiledPythonPackage()

        flags = ["NUITKA_BYTECODE_FLAG"]
        if is_package:
            flags.append("NUITKA_PACKAGE_FLAG")

        accessor_code = bytecode_accessor.getBlobDataCode(code_data)

        return template_metapath_loader_bytecode_module_entry % {
            "module_name": module.getFullName(),
            "bytecode": accessor_code[accessor_code.find("[") + 1 : -1],
            "size": len(code_data),
            "flags": " | ".join(flags),
        }
    elif module.isPythonShlibModule():
        assert module_name

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


def getMetapathLoaderBodyCode(bytecode_accessor):
    metapath_loader_inittab = []
    metapath_module_decls = []

    for other_module in getDoneModules():
        metapath_loader_inittab.append(
            getModuleMetapathLoaderEntryCode(
                module=other_module, bytecode_accessor=bytecode_accessor
            )
        )

        if other_module.isCompiledPythonModule():
            metapath_module_decls.append(
                """\
extern PyObject *modulecode_%(module_identifier)s(PyObject *, struct Nuitka_MetaPathBasedLoaderEntry const *);"""
                % {"module_identifier": other_module.getCodeName()}
            )

    for uncompiled_module in getUncompiledModules():
        metapath_loader_inittab.append(
            getModuleMetapathLoaderEntryCode(
                module=uncompiled_module, bytecode_accessor=bytecode_accessor
            )
        )

    frozen_defs = []

    for uncompiled_module in getUncompiledTechnicalModules():
        module_name = uncompiled_module.getFullName()
        code_data = uncompiled_module.getByteCode()
        is_package = uncompiled_module.isUncompiledPythonPackage()

        size = len(code_data)

        # Packages are indicated with negative size.
        if is_package:
            size = -size

        accessor_code = bytecode_accessor.getBlobDataCode(code_data)

        frozen_defs.append(
            """\
{{"{module_name}", {start}, {size}}},""".format(
                module_name=module_name,
                start=accessor_code[accessor_code.find("[") + 1 : -1],
                size=size,
            )
        )

        if Options.isShowInclusion():
            inclusion_logger.info("Embedded as frozen module '%s'." % module_name)

    return template_metapath_loader_body % {
        "metapath_module_decls": indented(metapath_module_decls, 0),
        "metapath_loader_inittab": indented(metapath_loader_inittab),
        "bytecode_count": bytecode_accessor.getConstantsCount(),
        "frozen_modules": indented(frozen_defs),
    }
