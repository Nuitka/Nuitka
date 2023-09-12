#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

import atexit
import os
import sys
import traceback

from nuitka import TreeXML
from nuitka.__past__ import unicode
from nuitka.build.DataComposerInterface import getDataComposerReportValues
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
    getCompilationReportUserData,
    shallCreateDiffableCompilationReport,
)
from nuitka.plugins.Plugins import getActivePlugins
from nuitka.PythonFlavors import getPythonFlavorName
from nuitka.PythonVersions import getSystemPrefixPath, python_version_full_str
from nuitka.Tracing import ReportingSystemExit, reports_logger
from nuitka.utils.Distributions import getDistributionsFromModuleName
from nuitka.utils.FileOperations import getReportPath, putTextFileContents
from nuitka.utils.Jinja2 import getTemplate
from nuitka.utils.MemoryUsage import getMemoryInfos
from nuitka.utils.Utils import getArchitecture, getOS
from nuitka.Version import getCommercialVersion, getNuitkaVersion


def _getReportInputData(aborted):
    """Collect all information for reporting into a dictionary."""

    # used with locals for laziness and these are to populate a dictionary with
    # many entries, pylint: disable=possibly-unused-variable,too-many-locals

    module_names = tuple(module.getFullName() for module in getDoneModules())

    module_kinds = dict(
        (module.getFullName(), module.__class__.__name__) for module in getDoneModules()
    )

    module_sources = dict(
        (module.getFullName(), module.source_ref) for module in getDoneModules()
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

    module_distribution_names = dict(
        (module.getFullName(), module.getUsedDistributions())
        for module in getDoneModules()
    )

    all_distributions = tuple(
        sorted(
            set(sum(module_distributions.values(), ())),
            key=lambda dist: dist.metadata["Name"],
        )
    )

    memory_infos = getMemoryInfos()

    python_exe = sys.executable

    python_flavor = getPythonFlavorName()
    python_version = python_version_full_str
    os_name = getOS()
    arch_name = getArchitecture()

    nuitka_version = getNuitkaVersion()
    nuitka_commercial_version = getCommercialVersion() or "not installed"

    nuitka_aborted = aborted

    nuitka_exception = sys.exc_info()

    user_data = getCompilationReportUserData()

    data_composer = getDataComposerReportValues()

    return dict(
        (var_name, var_value)
        for var_name, var_value in locals().items()
        if not var_name.startswith("_")
    )


_report_prefixes = None


def _getReportPathPrefixes():
    # Using global here, as this is really a singleton, in the form of a module,
    # pylint: disable=global-statement
    global _report_prefixes

    if _report_prefixes is None:
        _report_prefixes = []

        sys_prefix = os.environ.get("NUITKA_SYS_PREFIX", sys.prefix)
        real_sys_prefix = getSystemPrefixPath()

        if real_sys_prefix != sys_prefix:
            _report_prefixes.append(("${sys.real_prefix}", real_sys_prefix))

        _report_prefixes.append(("${sys.prefix}", sys_prefix))
        _report_prefixes.append(("${cwd}", os.getcwd()))

    return _report_prefixes


def _getCompilationReportPath(path):
    return getReportPath(path, prefixes=_getReportPathPrefixes())


def _addModulesToReport(root, report_input_data, diffable):
    # Many details to work with, pylint: disable=too-many-locals

    for module_name in report_input_data["module_names"]:
        active_module_info = report_input_data["module_inclusion_infos"][module_name]

        module_xml_node = TreeXML.appendTreeElement(
            root,
            "module",
            name=module_name,
            kind=report_input_data["module_kinds"][module_name],
            usage=active_module_info.usage_tag,
            reason=active_module_info.reason,
            source_path=_getCompilationReportPath(
                report_input_data["module_sources"][module_name].getFilename()
            ),
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
            timing_xml_node.attrib["time"] = (
                "volatile" if diffable else "%.2f" % timing_info.time_used
            )

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
                    "distribution-used",
                    name=distribution.metadata["Name"],
                )

        module_distribution_names = report_input_data["module_distribution_names"][
            module_name
        ]

        if module_distribution_names:
            module_distribution_names_xml_node = TreeXML.appendTreeElement(
                module_xml_node,
                "distribution-lookups",
            )

            for distribution_name, found in module_distribution_names.items():
                TreeXML.appendTreeElement(
                    module_distribution_names_xml_node,
                    "distribution",
                    name=distribution_name,
                    found="yes" if found else "no",
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


def _addMemoryInfosToReport(performance_xml_node, memory_infos, diffable):
    for key, value in memory_infos.items():
        # Only top level values for now.
        if type(value) is not int:
            continue

        TreeXML.appendTreeElement(
            performance_xml_node,
            "memory_usage",
            name=key,
            value="volatile" if diffable else str(value),
        )


def _addUserDataToReport(root, user_data):
    if user_data:
        user_data_xml_node = TreeXML.appendTreeElement(
            root,
            "user-data",
        )

        for key, value in user_data.items():
            user_data_value_xml_node = TreeXML.appendTreeElement(
                user_data_xml_node,
                key,
            )

            user_data_value_xml_node.text = value


def writeCompilationReport(report_filename, report_input_data, diffable):
    """Write the compilation report in XML format."""
    # Many details, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    # When failing to write the crash report, we need to indicate that it was
    # not done to the atexit handler, pylint: disable=global-statement
    global _crash_report_filename

    exit_message = None
    if not report_input_data["nuitka_aborted"]:
        completion = "yes"
    elif report_input_data["nuitka_exception"][0] is KeyboardInterrupt:
        completion = "interrupted"
    elif report_input_data["nuitka_exception"][0] is SystemExit:
        completion = "error exit (%s)" % report_input_data["nuitka_exception"][1].code
    elif report_input_data["nuitka_exception"][0] is ReportingSystemExit:
        completion = (
            "error exit message (%s)" % report_input_data["nuitka_exception"][1].code
        )
        exit_message = report_input_data["nuitka_exception"][1].exit_message
    else:
        completion = "exception"

    root = TreeXML.Element(
        "nuitka-compilation-report",
        nuitka_version=report_input_data["nuitka_version"],
        nuitka_commercial_version=report_input_data["nuitka_commercial_version"],
        completion=completion,
    )

    if exit_message is not None:
        root.attrib["exit_message"] = exit_message

    if completion == "exception":
        exception_xml_node = TreeXML.appendTreeElement(
            root,
            "exception",
            exception_type=str(sys.exc_info()[0].__name__),
            exception_value=str(sys.exc_info()[1]),
        )

        exception_xml_node.text = "\n" + traceback.format_exc()

    _addModulesToReport(
        root=root, report_input_data=report_input_data, diffable=diffable
    )

    if report_input_data["memory_infos"]:
        performance_xml_node = TreeXML.appendTreeElement(
            root,
            "performance",
        )

        _addMemoryInfosToReport(
            performance_xml_node=performance_xml_node,
            memory_infos=report_input_data["memory_infos"],
            diffable=diffable,
        )

    for included_datafile in getIncludedDataFiles():
        if included_datafile.kind == "data_file":
            TreeXML.appendTreeElement(
                root,
                "data_file",
                name=included_datafile.dest_path,
                source=_getCompilationReportPath(included_datafile.source_path),
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
            source_path=_getCompilationReportPath(standalone_entry_point.source_path),
            package=standalone_entry_point.package_name or "",
            ignored="yes" if ignored else "no",
            reason=standalone_entry_point.reason
            # TODO: No reason yet.
        )

    if not diffable:
        data_composer_values = getDataComposerReportValues()

        data_composer_xml_node = TreeXML.appendTreeElement(
            root,
            "data_composer",
            blob_size=str(data_composer_values["blob_size"]),
        )

        data_composer_stats = data_composer_values["stats"]
        if data_composer_stats:
            for item, item_value in data_composer_stats.items():
                assert type(item) in (str, unicode)
                if type(item_value) is int:
                    data_composer_xml_node.attrib[item] = str(item_value)
                else:
                    for key in item_value:
                        item_value[key] = str(item_value[key])

                    TreeXML.appendTreeElement(
                        data_composer_xml_node,
                        "module_data",
                        filename=item,
                        **item_value
                    )

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

    python_xml_node = TreeXML.appendTreeElement(
        root,
        "python",
        python_exe=_getCompilationReportPath(report_input_data["python_exe"]),
        python_flavor=report_input_data["python_flavor"],
        python_version=report_input_data["python_version"],
        os_name=report_input_data["os_name"],
        arch_name=report_input_data["arch_name"],
    )

    search_path_xml_node = TreeXML.appendTreeElement(
        python_xml_node,
        "search_path",
    )

    for search_path in getPackageSearchPath(None):
        TreeXML.appendTreeElement(
            search_path_xml_node,
            "path",
            value=_getCompilationReportPath(search_path),
        )

    _addUserDataToReport(root=root, user_data=report_input_data["user_data"])

    try:
        putTextFileContents(filename=report_filename, contents=TreeXML.toString(root))
    except OSError as e:
        reports_logger.warning(
            "Compilation report write to file '%s' failed due to: %s."
            % (report_filename, e)
        )

        if _crash_report_filename == report_filename:
            _crash_report_filename = None
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

        if not license_name or license_name == "UNKNOWN":
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


_crash_report_filename = "nuitka-crash-report.xml"


def _informAboutCrashReport():
    if _crash_report_filename is not None:
        reports_logger.info(
            """\
Compilation crash report written to file '%s'. Please include it in \
your bug report."""
            % _crash_report_filename,
            style="red",
        )


def writeCompilationReports(aborted):
    report_filename = getCompilationReportFilename()
    template_specs = getCompilationReportTemplates()
    diffable = shallCreateDiffableCompilationReport()

    if (
        report_filename is None
        and aborted
        and sys.exc_info()[0] not in (KeyboardInterrupt, SystemExit)
    ):
        report_filename = _crash_report_filename

        atexit.register(_informAboutCrashReport)

    if report_filename or template_specs:
        report_input_data = _getReportInputData(aborted)

        if report_filename:
            writeCompilationReport(
                report_filename=report_filename,
                report_input_data=report_input_data,
                diffable=diffable,
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
