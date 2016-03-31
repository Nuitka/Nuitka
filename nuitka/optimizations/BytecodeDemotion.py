#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka.importing.ImportCache import replaceImportedModule
from nuitka.nodes.ModuleNodes import UncompiledPythonModule
from nuitka.plugins.Plugins import Plugins
from nuitka.tree.SourceReading import readSourceCodeFromFilename


def demoteCompiledModuleToBytecode(module):

    full_name = module.getFullName()
    filename = module.getCompileTimeFilename()

    source_code = readSourceCodeFromFilename(full_name, filename)

    source_code = Plugins.onFrozenModuleSourceCode(
        module_name = full_name,
        is_package  = False,
        source_code = source_code
    )

    bytecode = compile(source_code, filename, "exec")

    bytecode = Plugins.onFrozenModuleBytecode(
        module_name = full_name,
        is_package  = False,
        bytecode    = bytecode
    )

    uncompiled_module = UncompiledPythonModule(
        name          = module.getName(),
        package_name  = module.getPackage(),
        bytecode      = bytecode,
        filename      = filename,
        user_provided = True,
        technical     = False,
        source_ref    = module.source_ref
    )

    replaceImportedModule(
        old = module,
        new = uncompiled_module
    )
