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
""" Collection of information for Report and their writing.

"""

from nuitka import TreeXML
from nuitka.freezer.IncludedDataFiles import getIncludedDataFiles
from nuitka.freezer.Standalone import getCopiedDLLInfos
from nuitka.importing.Importing import getPackageSearchPath
from nuitka.ModuleRegistry import getDoneModules, getModuleInclusionInfos
from nuitka.plugins import PluginBase
from nuitka.Tracing import general
from nuitka.utils.FileOperations import putTextFileContents


def writeCompilationReport(report_filename):
    active_modules_info = getModuleInclusionInfos()

    root = TreeXML.Element("nuitka-compilation-report")

    for module in getDoneModules():
        active_module_info = active_modules_info[module]

        root.append(
            TreeXML.Element(
                "module",
                name=module.getFullName(),
                kind=module.__class__.__name__,
                reason=active_module_info.reason,
            )
        )

    for included_datafile in getIncludedDataFiles():
        if included_datafile.kind == "data_file":
            root.append(
                TreeXML.Element(
                    "data_file",
                    name=included_datafile.dest_path,
                    source=included_datafile.source_path,
                    reason=included_datafile.reason,
                    tags=",".join(included_datafile.tags),
                )
            )
        elif included_datafile.kind == "data_blob":
            root.append(
                TreeXML.Element(
                    "data_blob",
                    name=included_datafile.dest_path,
                    reason=included_datafile.reason,
                    tags=",".join(included_datafile.tags),
                )
            )

    for copied_dll_info in getCopiedDLLInfos():
        root.append(
            TreeXML.Element(
                "included_dll",
                name=copied_dll_info.dll_name,
                dest_path=copied_dll_info.dest_path,
                source_path=copied_dll_info.source_path,
                package=copied_dll_info.source_path,
                sources=".".join(copied_dll_info.sources),
                # TODO: No reason yet.
                # reason=copied_dll_info.reason,
            )
        )

    search_path = getPackageSearchPath(None)

    root.append(
        TreeXML.Element(
            "search_path",
            dirs=":".join(search_path),
        )
    )

    root.append(TreeXML.Element("used_control_tags", tags=PluginBase.used_tags))

    putTextFileContents(filename=report_filename, contents=TreeXML.toString(root))

    general.info("Compilation report in file %r." % report_filename)
