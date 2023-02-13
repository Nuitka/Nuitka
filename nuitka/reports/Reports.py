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
""" Collection of information for reports and their writing.

These reports are in XML form, and with Jinja2 templates in any form you like.

"""

import os
import sys

from nuitka import TreeXML
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.freezer.IncludedDataFiles import getIncludedDataFiles
from nuitka.freezer.IncludedEntryPoints import getStandaloneEntryPoints
from nuitka.importing.Importing import getPackageSearchPath
from nuitka.ModuleRegistry import (
    getDoneModules,
    getModuleInclusionInfoByName,
    getModuleInfluences,
    getModuleOptimizationTimingInfos,
)
from nuitka.Options import (
    getCompilationReportFilename,
    getCompilationReportTemplates,
)
from nuitka.plugins.Plugins import getActivePlugins
from nuitka.Tracing import reports_logger
from nuitka.utils.Distributions import getDistributionsFromModuleName
from nuitka.utils.FileOperations import putTextFileContents
from nuitka.utils.Jinja2 import getTemplate


def _getReportInputData():
    """Collect all information for reporting into a dictionary."""

    # pylint: used with locals for laziness, disable=possibly-unused-variable

    module_names = tuple(module.getFullName() for module in getDoneModules())

    module_kinds = dict(
        (module.getFullName(), module.__class__.__name__) for module in getDoneModules()
    )

    module_inclusion_infos = dict(
        (module.getFullName(), getModuleInclusionInfoByName(module.getFullName()))
        for module in getDoneModules()
    )

    module_plugin_influences = dict(
        (module.getFullName(), getModuleInfluences(module.getFullName()))
        for module in getDoneModules()
    )

    module_timing_infos = dict(
        (module.getFullName(), getModuleOptimizationTimingInfos(module.getFullName()))
        for module in getDoneModules()
    )

    module_distributions = {}
    distribution_modules = {}
    for module in getDoneModules():
        module_distributions[module.getFullName()] = getDistributionsFromModuleName(
            module.getFullName()
        )
        for _distribution in module_distributions[module.getFullName()]:
            if _distribution not in distribution_modules:
                distribution_modules[_distribution] = OrderedSet()

            distribution_modules[_distribution].add(module.getFullName())

    module_usages = dict(
        (module.getFullName(), module.getUsedModules()) for module in getDoneModules()
    )

    all_distributions = tuple(
        sorted(
            set(sum(module_distributions.values(), ())),
            key=lambda dist: dist.metadata["Name"],
        )
    )

    return dict(
        (var_name, var_value)
        for var_name, var_value in locals().items()
        if not var_name.startswith("_")
    )


def _addModulesToReport(root, report_input_data):
    # Many details to work with, pylint: disable=too-many-locals

    for module_name in report_input_data["module_names"]:
        active_module_info = report_input_data["module_inclusion_infos"][module_name]

        module_xml_node = TreeXML.appendTreeElement(
            root,
            "module",
            name=module_name,
            kind=report_input_data["module_kinds"][module_name],
            reason=active_module_info.reason,
        )

        for plugin_name, influence, detail in report_input_data[
            "module_plugin_influences"
        ][module_name]:
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

        for timing_info in report_input_data["module_timing_infos"][module_name]:
            timing_xml_node = TreeXML.Element(
                "optimization-time",
            )

            # Going via attrib, because pass is a keyword in Python.
            timing_xml_node.attrib["pass"] = str(timing_info.pass_number)
            timing_xml_node.attrib["time"] = "%.2f" % timing_info.time_used

            module_xml_node.append(timing_xml_node)

        distributions = report_input_data["module_distributions"][module_name]

        if distributions:
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

        for used_module in report_input_data["module_usages"][module_name]:
            TreeXML.appendTreeElement(
                used_modules_xml_node,
                "module_usage",
                name=used_module.module_name.asString(),
                finding=used_module.finding,
                line=str(used_module.source_ref.getLineNumber()),
            )


def writeCompilationReport(report_filename, report_input_data):
    """Write the compilation report in XML format."""
    # Many details, pylint: disable=too-many-branches,too-many-locals

    root = TreeXML.Element("nuitka-compilation-report")

    _addModulesToReport(root, report_input_data)

    for included_datafile in getIncludedDataFiles():
        if included_datafile.kind == "data_file":
            TreeXML.appendTreeElement(
                root,
                "data_file",
                name=included_datafile.dest_path,
                source=included_datafile.source_path,
                size=str(included_datafile.getFileSize()),
                reason=included_datafile.reason,
                tags=",".join(included_datafile.tags),
            )
        elif included_datafile.kind == "data_blob":
            TreeXML.appendTreeElement(
                root,
                "data_blob",
                name=included_datafile.dest_path,
                size=str(included_datafile.getFileSize()),
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

    for distribution in report_input_data["all_distributions"]:
        TreeXML.appendTreeElement(
            distributions_xml_node,
            "distribution",
            name=distribution.metadata["Name"],
            version=distribution.metadata["Version"],
        )

    try:
        putTextFileContents(filename=report_filename, contents=TreeXML.toString(root))
    except OSError as e:
        reports_logger.warning(
            "Compilation report write to file '%s' failed due to: %s."
            % (report_filename, e)
        )
    else:
        reports_logger.info(
            "Compilation report written to file '%s'." % report_filename
        )


def writeCompilationReportFromTemplate(
    template_filename, report_filename, report_input_data
):
    template = getTemplate(
        package_name=None,
        template_subdir=os.path.dirname(template_filename) or ".",
        template_name=os.path.basename(template_filename),
        extensions=("jinja2.ext.do",),
    )

    def get_distribution_license(distribution):
        license_name = distribution.metadata["License"]

        if license_name == "UNKNOWN":
            for classifier in (
                value
                for (key, value) in distribution.metadata.items()
                if "Classifier" in key
            ):
                parts = [part.strip() for part in classifier.split("::")]
                if not parts:
                    continue

                if parts[0] == "License":
                    license_name = parts[-1]
                    break

        return license_name

    def quoted(value):
        if isinstance(value, str):
            return "'%s'" % value
        else:
            return [quoted(element) for element in value]

    report_text = template.render(
        # Get the license text.
        get_distribution_license=get_distribution_license,
        # Quote a list of strings.
        quoted=quoted,
        # For checking length of lists.
        len=len,
        **report_input_data
    )

    try:
        putTextFileContents(filename=report_filename, contents=report_text)
    except OSError as e:
        reports_logger.warning(
            "Compilation report from template failed write file '%s' due to: %s."
            % (report_filename, e)
        )
    else:
        reports_logger.info(
            "Compilation report from template written to file '%s'." % report_filename
        )


def writeCompilationReports():
    report_filename = getCompilationReportFilename()
    template_specs = getCompilationReportTemplates()

    if report_filename or template_specs:
        report_input_data = _getReportInputData()

        if report_filename:
            writeCompilationReport(
                report_filename=report_filename, report_input_data=report_input_data
            )

        for template_filename, report_filename in template_specs:
            if (
                not os.path.exists(template_filename)
                and os.path.sep not in template_filename
            ):
                candidate = os.path.join(os.path.dirname(__file__), template_filename)

                if not candidate.endswith(".rst.j2"):
                    candidate += ".rst.j2"

                if os.path.exists(candidate):
                    template_filename = candidate

            if not os.path.exists(template_filename):
                reports_logger.warning(
                    "Cannot find report template '%s' ignoring report request."
                    % template_filename
                )
                continue

            writeCompilationReportFromTemplate(
                template_filename=template_filename,
                report_filename=report_filename,
                report_input_data=report_input_data,
            )
