#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code to generate and interact with module loaders.

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

import sys

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.importing.Recursion import getExcludedModuleNames
from nuitka.ModuleRegistry import getDoneModules, getUncompiledTechnicalModules
from nuitka.options.Options import (
    getFileReferenceMode,
    hasNonDeploymentIndicator,
    isShowInclusion,
    isStandaloneMode,
    shallMakeModule,
)
from nuitka.plugins.Hooks import onMetaPathLoaderEntryTemplate
from nuitka.PythonVersions import python_version
from nuitka.Tracing import inclusion_logger
from nuitka.utils.CStrings import (
    encodePythonIdentifierToC,
    encodePythonStringToC,
    encodePythonUnicodeToC,
)
from nuitka.utils.ModuleNames import (
    makeTriggerModuleName,
    post_module_load_trigger_name,
    pre_module_load_trigger_name,
)
from nuitka.utils.Utils import isWin32Windows

from .Indentation import indented
from .templates.CodeTemplatesLoader import (
    template_metapath_loader_body,
    template_metapath_loader_bytecode_module_entry,
    template_metapath_loader_excluded_module_entry,
    template_metapath_loader_extension_module_entry,
)
from .templates.CodeTemplatesModules import template_module_loader_entry


def _getModuleEntryCodeName(module_name):
    return "entry_" + encodePythonIdentifierToC(module_name)


def _getLoaderModuleOrderKey(module):
    return module.getFullName()


def _getLoaderModuleOrder():
    return sorted(getDoneModules(), key=_getLoaderModuleOrderKey)


def _getLoaderModuleNames():
    return OrderedSet([module.getFullName() for module in _getLoaderModuleOrder()])


def _getModuleEntryRefName(module_name):
    if module_name not in _getLoaderModuleNames():
        return "NULL"

    return "&%s" % _getModuleEntryCodeName(module_name)


def _getGetNameFuncCode():
    if shallMakeModule():
        return "getModuleNameWithPackageLoadedPrefix"

    return "NULL"


def _getModuleEntryRefs(module_name):
    return (
        _getModuleEntryRefName(
            makeTriggerModuleName(module_name, pre_module_load_trigger_name)
        ),
        _getModuleEntryRefName(
            makeTriggerModuleName(module_name, post_module_load_trigger_name)
        ),
        _getModuleEntryRefName(module_name.getPackageName()),
    )


def _getModuleEntryDecls(pre_load_entry, post_load_entry, parent_entry):
    decls = []

    for entry_ref in (pre_load_entry, post_load_entry, parent_entry):
        if entry_ref != "NULL":
            decls.append(
                "extern struct Nuitka_MetaPathBasedLoaderEntry %s;" % entry_ref[1:]
            )

    return "\n".join(decls)


def _getModuleEntryCommonArgs(module):
    module_name = module.getFullName()

    flags = []

    if (
        not isStandaloneMode()
        and not shallMakeModule()
        and getFileReferenceMode() == "original"
        and python_version >= 0x370
    ):
        # File system paths that will hopefully work, spell-checker: ignore getfilesystemencoding
        if isWin32Windows():
            file_path = encodePythonUnicodeToC(module.getCompileTimeFilename())
        else:
            file_path = encodePythonStringToC(
                module.getCompileTimeFilename().encode(sys.getfilesystemencoding())
            )
    else:
        file_path = "NULL"

    if hasNonDeploymentIndicator("perfect-support") and isPerfectSupported(module_name):
        flags.append("NUITKA_PERFECT_SUPPORTED_FLAG")

    if module.isMainModule():
        flags.append("NUITKA_MAIN_MODULE_FLAG")

    pre_load_entry, post_load_entry, parent_entry = _getModuleEntryRefs(module_name)

    return {
        "module_name": module_name.asCString(),
        "get_name_func": _getGetNameFuncCode(),
        "compare_name_func": "NULL",
        "get_display_name": "NULL",
        "pre_load": pre_load_entry,
        "post_load": post_load_entry,
        "parent": parent_entry,
        "flags": flags,
        "file_path": file_path,
    }


def getModuleLoaderEntryCode(module):
    module_identifier = module.getCodeName()

    template_args = _getModuleEntryCommonArgs(module)

    if module.isCompiledPythonPackage():
        template_args["flags"].append("NUITKA_PACKAGE_FLAG")

    template_args["entry_name"] = _getModuleEntryCodeName(module.getFullName())
    template_args["module_identifier"] = module_identifier
    template_args["module_loader_entry_body"] = ""
    template_args["template"] = template_module_loader_entry

    onMetaPathLoaderEntryTemplate(module=module, template_args=template_args)

    template_args["flags"] = " | ".join(template_args["flags"]) or "0"

    template_args["module_loader_entry_decls"] = _getModuleEntryDecls(
        template_args["pre_load"],
        template_args["post_load"],
        template_args["parent"],
    )

    template = template_args.pop("template")
    return template % template_args


def getModuleMetaPathLoaderEntryCode(module, bytecode_accessor, entry_name):
    template_args = _getModuleEntryCommonArgs(module)
    template_args["entry_name"] = entry_name

    if module.isUncompiledPythonModule():
        code_data = module.getByteCode()
        is_package = module.isUncompiledPythonPackage()

        template_args["flags"].append("NUITKA_BYTECODE_FLAG")
        if is_package:
            template_args["flags"].append("NUITKA_PACKAGE_FLAG")

        accessor_code = bytecode_accessor.getBlobDataCode(
            data=code_data,
            name="bytecode of module '%s'" % module.getFullName(),
        )

        template_args["bytecode"] = accessor_code[accessor_code.find("[") + 1 : -1]
        template_args["size"] = len(code_data)
        template_args["template"] = template_metapath_loader_bytecode_module_entry
    elif module.isPythonExtensionModule():
        template_args["flags"].append("NUITKA_EXTENSION_MODULE_FLAG")

        if module.isExtensionModulePackage():
            template_args["flags"].append("NUITKA_PACKAGE_FLAG")

        template_args["template"] = template_metapath_loader_extension_module_entry
    else:
        assert False, module

    onMetaPathLoaderEntryTemplate(module=module, template_args=template_args)

    template_args["flags"] = " | ".join(template_args["flags"]) or "0"

    template = template_args.pop("template")
    return template % template_args


def getMetaPathLoaderBodyCode(bytecode_accessor):
    # Somewhat detail rich, pylint: disable=too-many-locals
    metapath_loader_inittab = []
    metapath_loader_decls = []
    metapath_loader_refs = []

    # We need the entry names up front, so that pre/post load and parent entries
    # can reference each other by name rather than relying on name based lookups
    # at runtime.
    ordered_modules = _getLoaderModuleOrder()

    for module in ordered_modules:
        entry_name = _getModuleEntryCodeName(module.getFullName())

        # Bytecode and extension entries need external linkage, as compiled
        # modules may reference them.
        metapath_loader_decls.append(
            "extern struct Nuitka_MetaPathBasedLoaderEntry %s;" % entry_name
        )

        if not module.isCompiledPythonModule():
            # Bytecode and extension modules have no C file of their own, so the
            # entry is defined here.
            metapath_loader_inittab.append(
                getModuleMetaPathLoaderEntryCode(
                    module=module,
                    bytecode_accessor=bytecode_accessor,
                    entry_name=entry_name,
                )
            )

        metapath_loader_refs.append("    &%s," % entry_name)

    frozen_defs = []

    # Only the non-technical ones need to be there.
    for uncompiled_module in getUncompiledTechnicalModules():
        module_name = uncompiled_module.getFullName()
        code_data = uncompiled_module.getByteCode()
        is_package = uncompiled_module.isUncompiledPythonPackage()

        size = len(code_data)

        # Packages are indicated with negative size.
        if is_package:
            size = -size

        accessor_code = bytecode_accessor.getBlobDataCode(
            data=code_data,
            name="bytecode of module '%s'" % uncompiled_module.getFullName(),
        )

        frozen_defs.append(
            """\
{{"{module_name}", {start}, {size}}},""".format(
                module_name=module_name,
                start=accessor_code[accessor_code.find("[") + 1 : -1],
                size=size,
            )
        )

        if isShowInclusion():
            inclusion_logger.info("Embedded as frozen module '%s'." % module_name)

    if isStandaloneMode() and hasNonDeploymentIndicator("excluded-module-usage"):
        for excluded_index, (module_name, reason) in enumerate(
            getExcludedModuleNames()
        ):
            # This one does it on purpose, spell-checker: ignore aspose
            if module_name.hasNamespace("aspose"):
                continue

            # Excluded module names can be duplicated, e.g. the same module
            # excluded via multiple reasons, so use an index to make the entry
            # name unique.
            entry_name = "entry_excluded_%d" % excluded_index

            module_c_name = module_name.asCString()
            get_name_func = _getGetNameFuncCode()
            reason_c_string = encodePythonStringToC(reason.encode("utf8"))

            # Check for "excluded by user" or similar reason if necessary,
            # but for now we include all rejected modules that have a reason.
            # We might want to filter this better, e.g. only if it starts with "Module ... instructed by user"
            # For now, let's include all explicit 'False' decisions where we have a module name.
            metapath_loader_inittab.append(
                template_metapath_loader_excluded_module_entry
                % {
                    "entry_name": entry_name,
                    "module_name": module_c_name,
                    "get_name_func": get_name_func,
                    "compare_name_func": "NULL",
                    "flags": "NUITKA_EXCLUDED_MODULE_FLAG",
                    "exclusion_reason": reason_c_string,
                }
            )
            metapath_loader_refs.append("    &%s," % entry_name)

    return template_metapath_loader_body % {
        "metapath_loader_decls": indented(metapath_loader_decls),
        "metapath_loader_inittab": indented(metapath_loader_inittab),
        "metapath_loader_refs": indented(metapath_loader_refs),
        "entry_count": len(metapath_loader_refs),
        "bytecode_count": bytecode_accessor.getConstantsCount(),
        "frozen_modules": indented(frozen_defs),
    }


perfect_supported = set()


def markModuleAsPerfectSupported(module_name):
    perfect_supported.add(module_name)


def isPerfectSupported(module_name):
    return module_name in perfect_supported


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
