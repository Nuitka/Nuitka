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

import os
import sys

from nuitka import TreeXML
from nuitka.freezer.IncludedDataFiles import getIncludedDataFiles
from nuitka.freezer.IncludedEntryPoints import getStandaloneEntryPoints
from nuitka.importing.Importing import getPackageSearchPath
from nuitka.ModuleRegistry import (
    getDoneModules,
    getModuleInclusionInfos,
    getModuleInfluences,
    getModuleOptimizationTimingInfos,
)
from nuitka.plugins.Plugins import getActivePlugins
from nuitka.Tracing import general
from nuitka.utils.FileOperations import putTextFileContents


def writeCompilationReport(report_filename):
    # Many details to work with, pylint: disable=too-many-branches,too-many-locals

    active_modules_infos = getModuleInclusionInfos()

    root = TreeXML.Element("nuitka-compilation-report")

    for module in getDoneModules():
        active_module_info = active_modules_infos[module]

        module_xml_node = TreeXML.Element(
            "module",
            name=module.getFullName(),
            kind=module.__class__.__name__,
            reason=active_module_info.reason,
        )

        for plugin_name, influence, detail in getModuleInfluences(module.getFullName()):
            influence_xml_node = TreeXML.Element(
                "plugin-influence", name=plugin_name, influence=influence
            )

            if influence == "condition-used":
                condition, condition_tags_used, condition_result = detail

                influence_xml_node.attrib["condition"] = condition
                influence_xml_node.attrib["tags_used"] = ",".join(condition_tags_used)
                influence_xml_node.attrib["result"] = str(condition_result).lower()
            else:
                assert False, influence

            module_xml_node.append(influence_xml_node)

        for timing_info in sorted(
            getModuleOptimizationTimingInfos(module.getFullName())
        ):
            timing_xml_node = TreeXML.Element(
                "optimization-time",
            )

            # Going via attrib, because pass is a keyword in Python.
            timing_xml_node.attrib["pass"] = str(timing_info.pass_number)
            timing_xml_node.attrib["time"] = "%.2f" % timing_info.time_used

            module_xml_node.append(timing_xml_node)

        root.append(module_xml_node)

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

    for standalone_entry_point in getStandaloneEntryPoints():
        if standalone_entry_point.kind == "executable":
            continue

        kind = standalone_entry_point.kind

        if kind.endswith("_ignored"):
            ignored = True
            kind = kind.replace("_ignored", "")
        else:
            ignored = False

        root.append(
            TreeXML.Element(
                "included_" + kind,
                name=os.path.basename(standalone_entry_point.dest_path),
                dest_path=standalone_entry_point.dest_path,
                source_path=standalone_entry_point.source_path,
                package=standalone_entry_point.package_name or "",
                ignored="yes" if ignored else "no",
                reason=standalone_entry_point.reason
                # TODO: No reason yet.
            )
        )

    search_path_element = TreeXML.appendTreeElement(
        root,
        "search_path",
    )

    for search_path in getPackageSearchPath(None):
        search_path_element.append(TreeXML.Element("path", value=search_path))

    options_element = TreeXML.appendTreeElement(
        root,
        "command_line",
    )

    for arg in sys.argv[1:]:
        options_element.append(TreeXML.Element("option", value=arg))

    active_plugins_element = TreeXML.appendTreeElement(
        root,
        "plugins",
    )

    for plugin in getActivePlugins():
        if plugin.isDetector():
            continue

        active_plugins_element.append(
            TreeXML.Element(
                "plugin",
                name=plugin.plugin_name,
                user_enabled="no" if plugin.isAlwaysEnabled() else "yes",
            )
        )

    putTextFileContents(filename=report_filename, contents=TreeXML.toString(root))

    general.info("Compilation report in file '%s'." % report_filename)
