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

from .utils.Distributions import getDistributionsFromModuleName


def _addModulesToReport(root):
    # Many details to work with, pylint: disable=too-many-locals

    all_distributions = set()
    active_modules_infos = getModuleInclusionInfos()

    for module in getDoneModules():
        active_module_info = active_modules_infos[module]

        module_xml_node = TreeXML.appendTreeElement(
            root,
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

        distributions = getDistributionsFromModuleName(module.getFullName())

        if distributions:
            all_distributions.update(distributions)

            distributions_xml_node = TreeXML.appendTreeElement(
                module_xml_node,
                "distributions",
            )

            for distribution in distributions:
                TreeXML.appendTreeElement(
                    distributions_xml_node,
                    "distribution",
                    name=distribution.metadata["Name"],
                )

        used_modules_xml_node = TreeXML.appendTreeElement(
            module_xml_node,
            "module_usages",
        )

        for used_module in module.getUsedModules():
            TreeXML.appendTreeElement(
                used_modules_xml_node,
                "module_usage",
                name=used_module.module_name.asString(),
                finding=used_module.finding,
                line=str(used_module.source_ref.getLineNumber()),
            )

    return all_distributions


def writeCompilationReport(report_filename):
    """Write the compilation report in XML format."""

    root = TreeXML.Element("nuitka-compilation-report")

    all_distributions = _addModulesToReport(root)

    for included_datafile in getIncludedDataFiles():
        if included_datafile.kind == "data_file":
            TreeXML.appendTreeElement(
                root,
                "data_file",
                name=included_datafile.dest_path,
                source=included_datafile.source_path,
                reason=included_datafile.reason,
                tags=",".join(included_datafile.tags),
            )
        elif included_datafile.kind == "data_blob":
            TreeXML.appendTreeElement(
                root,
                "data_blob",
                name=included_datafile.dest_path,
                reason=included_datafile.reason,
                tags=",".join(included_datafile.tags),
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

        TreeXML.appendTreeElement(
            root,
            "included_" + kind,
            name=os.path.basename(standalone_entry_point.dest_path),
            dest_path=standalone_entry_point.dest_path,
            source_path=standalone_entry_point.source_path,
            package=standalone_entry_point.package_name or "",
            ignored="yes" if ignored else "no",
            reason=standalone_entry_point.reason
            # TODO: No reason yet.
        )

    search_path_xml_node = TreeXML.appendTreeElement(
        root,
        "search_path",
    )

    for search_path in getPackageSearchPath(None):
        TreeXML.appendTreeElement(search_path_xml_node, "path", value=search_path)

    options_xml_node = TreeXML.appendTreeElement(
        root,
        "command_line",
    )

    for arg in sys.argv[1:]:
        TreeXML.appendTreeElement(options_xml_node, "option", value=arg)

    active_plugins_xml_node = TreeXML.appendTreeElement(
        root,
        "plugins",
    )

    for plugin in getActivePlugins():
        if plugin.isDetector():
            continue

        TreeXML.appendTreeElement(
            active_plugins_xml_node,
            "plugin",
            name=plugin.plugin_name,
            user_enabled="no" if plugin.isAlwaysEnabled() else "yes",
        )

    distributions_xml_node = TreeXML.appendTreeElement(
        root,
        "distributions",
    )

    for distribution in sorted(
        all_distributions, key=lambda dist: dist.metadata["Name"]
    ):
        TreeXML.appendTreeElement(
            distributions_xml_node,
            "distribution",
            name=distribution.metadata["Name"],
            version=distribution.metadata["Version"],
        )

    putTextFileContents(filename=report_filename, contents=TreeXML.toString(root))

    general.info("Compilation report in file '%s'." % report_filename)
