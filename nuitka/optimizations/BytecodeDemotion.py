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
""" Demotion of compiled modules to bytecode modules.

"""

import marshal

from nuitka.Bytecodes import compileSourceToBytecode
from nuitka.Caching import writeImportedModulesNamesToCache
from nuitka.importing.ImportCache import (
    isImportedModuleByName,
    replaceImportedModule,
)
from nuitka.ModuleRegistry import replaceRootModule
from nuitka.nodes.ModuleNodes import makeUncompiledPythonModule
from nuitka.Options import isShowProgress, isStandaloneMode
from nuitka.plugins.Plugins import (
    Plugins,
    isTriggerModule,
    replaceTriggerModule,
)
from nuitka.Tracing import inclusion_logger


def demoteSourceCodeToBytecode(module_name, source_code, filename):
    # Second chance for plugins to modify source code just before turning it
    # to bytecode.
    source_code = Plugins.onFrozenModuleSourceCode(
        module_name=module_name, is_package=False, source_code=source_code
    )

    if isStandaloneMode():
        filename = module_name.asPath() + ".py"

    bytecode = compileSourceToBytecode(source_code, filename)

    bytecode = Plugins.onFrozenModuleBytecode(
        module_name=module_name, is_package=False, bytecode=bytecode
    )

    return marshal.dumps(bytecode)


def demoteCompiledModuleToBytecode(module):
    """Demote a compiled module to uncompiled (bytecode)."""

    full_name = module.getFullName()
    filename = module.getCompileTimeFilename()

    if isShowProgress():
        inclusion_logger.info(
            "Demoting module '%s' to bytecode from '%s'."
            % (full_name.asString(), filename)
        )

    source_code = module.getSourceCode()

    bytecode = demoteSourceCodeToBytecode(
        module_name=full_name, source_code=source_code, filename=filename
    )

    uncompiled_module = makeUncompiledPythonModule(
        module_name=full_name,
        filename=filename,
        bytecode=bytecode,
        is_package=module.isCompiledPythonPackage(),
        user_provided=True,
        technical=False,
    )

    used_modules = module.getUsedModules()
    uncompiled_module.setUsedModules(used_modules)
    module.finalize()

    if isImportedModuleByName(full_name):
        replaceImportedModule(old=module, new=uncompiled_module)
    replaceRootModule(old=module, new=uncompiled_module)

    if isTriggerModule(module):
        replaceTriggerModule(old=module, new=uncompiled_module)

    writeImportedModulesNamesToCache(
        module_name=full_name, source_code=source_code, used_modules=used_modules
    )
