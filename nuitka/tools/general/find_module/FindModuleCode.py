#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Find module code and open it in Visual Code.

The idea is that this can be used during development, to accept module names,
but also standalone filenames, etc. to simply find the original code in the
compiling environment with "--edit-module-code" option.

TODO: At this time it doesn't do all desired things yet.
"""

import os

from nuitka.importing.Importing import (
    ModuleName,
    addMainScriptDirectory,
    locateModule,
)
from nuitka.Tracing import tools_logger
from nuitka.utils.Execution import callProcess, getExecutablePath
from nuitka.utils.FileOperations import relpath
from nuitka.utils.Importing import getPackageDirFilename
from nuitka.utils.Utils import isWin32Windows


def findModuleCode(module_name):
    module_name = ModuleName(module_name)

    return locateModule(module_name=module_name, parent_package=None, level=0)[1]


def editModuleCode(module_search_desc):
    # plenty of checks to resolved, pylint: disable=too-many-branches

    module_filename = None
    module_name = None

    if isWin32Windows() and "\\" in module_search_desc:
        if os.path.exists(module_search_desc):
            module_filename = module_search_desc
        else:
            if module_search_desc.endswith(".py"):
                module_search_desc = module_search_desc[:-3]

            candidate = module_search_desc

            # spell-checker: ignore ONEFIL
            while not candidate.endswith(".DIS") and not os.path.basename(
                candidate
            ).startswith("ONEFIL"):
                candidate = os.path.dirname(candidate)

            module_name = relpath(module_search_desc, start=candidate).replace(
                "\\", "."
            )
    elif not isWin32Windows() and "/" in module_search_desc:
        if os.path.exists(module_search_desc):
            module_filename = module_search_desc
        else:
            if module_search_desc.endswith(".py"):
                module_search_desc = module_search_desc[:-3]

            candidate = module_search_desc

            while not candidate.endswith(".dist") and candidate:
                candidate = os.path.dirname(candidate)

            if candidate:
                module_name = relpath(module_search_desc, start=candidate).replace(
                    "/", "."
                )
            else:
                module_name = None
    else:
        module_name = ModuleName(module_search_desc)

    if module_name is None:
        tools_logger.sysexit(
            "Error, did not find module for '%s' " % module_search_desc
        )
    else:
        addMainScriptDirectory(os.getcwd())
        module_filename = findModuleCode(module_name)

    if module_filename is None:
        tools_logger.sysexit("Error, did not find '%s' module" % module_name)
    else:
        if os.path.isdir(module_filename):
            candidate = getPackageDirFilename(module_filename)

            if candidate is not None:
                module_filename = candidate

        if os.path.isdir(module_filename):
            tools_logger.sysexit(
                "Error, %s is a namespace package with no code" % module_name
            )

        if module_name is not None:
            tools_logger.info("Found '%s' as '%s'" % (module_name, module_filename))

        visual_code_binary = getExecutablePath(
            "code.cmd" if isWin32Windows() else "code"
        )

        if visual_code_binary:
            callProcess([visual_code_binary, module_filename])


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
