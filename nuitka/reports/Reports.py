#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


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
from nuitka.build.SconsUtils import readSconsErrorReport
from nuitka.code_generation.ConstantCodes import getDistributionMetadataValues
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.freezer.IncludedDataFiles import getIncludedDataFiles
from nuitka.freezer.IncludedEntryPoints import getStandaloneEntryPoints
from nuitka.freezer.Standalone import getRemovedUsedDllsInfo
from nuitka.importing.Importing import getPackageSearchPath
from nuitka.importing.Recursion import getRecursionDecisions
from nuitka.ModuleRegistry import (
    getDoneModules,
    getModuleInclusionInfoByName,
    getModuleInfluences,
    getModuleOptimizationTimingInfos,
)
from nuitka.Options import (
    getCompilationMode,
    getCompilationReportFilename,
    getCompilationReportTemplates,
    getCompilationReportUserData,
    isOnefileMode,
    shallCreateDiffableCompilationReport,
)
from nuitka.OutputDirectories import (
    getResultRunFilename,
    getSourceDirectoryPath,
    hasMainModule,
)
from nuitka.plugins.Plugins import getActivePlugins
from nuitka.PythonFlavors import getPythonFlavorName
from nuitka.PythonVersions import (
    getLaunchingSystemPrefixPath,
    getSystemPrefixPath,
    python_version_full_str,
)
from nuitka.Tracing import ReportingSystemExit, reports_logger
from nuitka.utils.Distributions import (
    getDistributionInstallerName,
    getDistributionLicense,
    getDistributionName,
    getDistributionsFromModuleName,
    getDistributionVersion,
    isDistributionVendored,
)
from nuitka.utils.FileOperations import (
    getReportPath,
    putBinaryFileContents,
    putTextFileContents,
)
from nuitka.utils.Jinja2 import getTemplate
from nuitka.utils.MemoryUsage import getMemoryInfos
from nuitka.utils.Utils import (
    getArchitecture,
    getLinuxDistribution,
    getMacOSRelease,
    getOS,
    getWindowsRelease,
    isLinux,
    isMacOS,
    isWin32OrPosixWindows,
)
from nuitka.Version import getCommercialVersion, getNuitkaVersion


def _getReportInputData(aborted):
    """Collect all information for reporting into a dictionary."""

    # used with locals for laziness and these are to populate a dictionary with
    # many entries,
    # pylint: disable=possibly-unused-variable,too-many-branches,too-many-locals,too-many-statements

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

    module_usages = dict(
        (module.getFullName(), tuple(module.getUsedModules()))
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

    module_distribution_usages = {}
    for module in getDoneModules():
        module_distribution_usages[module.getFullName()] = OrderedSet()

        for _module_usage in module_usages[module.getFullName()]:
            if _module_usage.module_name not in module_usages:
                continue

            module_distribution_usages[module.getFullName()].update(
                dist
                for dist in module_distributions[_module_usage.module_name]
                if dist not in module_distributions[module.getFullName()]
            )

    module_distribution_names = dict(
        (module.getFullName(), module.getUsedDistributions())
        for module in getDoneModules()
    )

    all_distributions = tuple(
        sorted(
            set(sum(module_distributions.values(), ())),
            key=getDistributionName,
        )
    )

    module_distribution_installers = dict(
        (
            getDistributionName(dist),
            getDistributionInstallerName(getDistributionName(dist)),
        )
        for dist in all_distributions
    )

    module_distribution_vendored = dict(
        (
            getDistributionName(dist),
            isDistributionVendored(getDistributionName(dist)),
        )
        for dist in all_distributions
    )

    module_exclusions = dict((module.getFullName(), {}) for module in getDoneModules())

    # TODO: The module filename, and other things can be None. Once we change to
    # namedtuples, we need to adapt the type check.
    def _replaceNoneWithString(value):
        if type(value) is tuple:
            return tuple(_replaceNoneWithString(element) for element in value)

        return value if value is not None else ""

    for (
        _using_module_name,
        _module_filename,
        _module_name,
        _module_kind,
        _extra_recursion,
    ), (_decision, _reason) in sorted(
        getRecursionDecisions().items(), key=_replaceNoneWithString
    ):
        if _decision is not False:
            continue

        if _using_module_name is None:
            continue

        # We might be interrupted, and have this information, but never actually
        # finished the module.
        if _using_module_name not in module_exclusions:
            continue

        module_exclusions[_using_module_name][_module_name] = _reason

    included_metadata = dict(
        (distribution_name, meta_data_value.reasons)
        for distribution_name, meta_data_value in getDistributionMetadataValues()
    )

    memory_infos = getMemoryInfos()

    python_exe = sys.executable

    python_flavor = getPythonFlavorName()
    python_version = python_version_full_str
    os_name = getOS()
    arch_name = getArchitecture()

    # Record system encoding, spell-checker: ignore getfilesystemencoding
    filesystem_encoding = sys.getfilesystemencoding()

    if isWin32OrPosixWindows():
        os_release = str(getWindowsRelease())
    elif isLinux():
        os_release = "-".join(x for x in getLinuxDistribution() if x)
    elif isMacOS():
        os_release = getMacOSRelease()
    else:
        os_release = "unknown"

    nuitka_version = getNuitkaVersion()
    nuitka_commercial_version = getCommercialVersion() or "not installed"

    nuitka_aborted = aborted

    nuitka_exception = sys.exc_info()

    user_data = getCompilationReportUserData()

    data_composer = getDataComposerReportValues()

    if hasMainModule():
        output_run_filename = os.path.abspath(
            getResultRunFilename(onefile=isOnefileMode())
        )
        scons_error_report_data = readSconsErrorReport(
            source_dir=getSourceDirectoryPath()
        )
    else:
        scons_error_report_data = {}
        output_run_filename = "failed too early"

    compilation_mode = getCompilationMode()

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

        sys_prefix = getLaunchingSystemPrefixPath() or sys.prefix
        real_sys_prefix = getSystemPrefixPath()

        if real_sys_prefix != sys_prefix:
            _report_prefixes.append(("${sys.real_prefix}", real_sys_prefix))

        _report_prefixes.append(("${sys.prefix}", sys_prefix))
        _report_prefixes.append(("${cwd}", os.getcwd()))

    return _report_prefixes


def _getCompilationReportPath(path):
    return getReportPath(path, prefixes=_getReportPathPrefixes())


def _addModulesToReport(root, report_input_data, diffable):
    # Many details to work with,
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

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

        distributions = report_input_data["module_distributions"][module_name]

        if distributions:
            module_xml_node.attrib["distribution"] = ",".join(
                getDistributionName(dist) for dist in distributions
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
                if condition_tags_used:
                    influence_xml_node.attrib["tags_used"] = ",".join(
                        condition_tags_used
                    )
                influence_xml_node.attrib["result"] = str(condition_result).lower()
            elif influence == "variable-used":
                (
                    variable_name,
                    condition_tags_used,
                    variable_value,
                    config_module_name,
                ) = detail

                influence_xml_node.attrib["variable"] = variable_name
                if condition_tags_used:
                    influence_xml_node.attrib["tags_used"] = ",".join(
                        condition_tags_used
                    )
                influence_xml_node.attrib["value"] = variable_value

                if module_name != config_module_name:
                    influence_xml_node.attrib["config_module"] = config_module_name

            elif influence == "parameter-used":
                parameter_name, condition_tags_used, parameter_value = detail

                influence_xml_node.attrib["parameter"] = parameter_name
                if condition_tags_used:
                    influence_xml_node.attrib["tags_used"] = ",".join(
                        condition_tags_used
                    )
                influence_xml_node.attrib["value"] = repr(parameter_value)
            elif influence == "detection":
                detection_name, detection_value = detail

                influence_xml_node.attrib["detection"] = detection_name
                influence_xml_node.attrib["value"] = repr(detection_value)
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

            if timing_info.micro_passes:
                timing_xml_node.attrib["micro_passes"] = str(timing_info.micro_passes)

            if timing_info.merge_counts:
                merged_total = 0

                for branch_count, merge_count in timing_info.merge_counts.items():
                    merged_total += branch_count * merge_count

                max_merge_size = max(timing_info.merge_counts)

                timing_xml_node.attrib["max_branch_merge"] = str(max_merge_size)
                timing_xml_node.attrib["merged_total"] = str(merged_total)

            module_xml_node.append(timing_xml_node)

        distributions = report_input_data["module_distribution_usages"][module_name]

        if distributions:
            distributions_xml_node = TreeXML.appendTreeElement(
                module_xml_node,
                "distribution-usages",
            )

            for distribution in distributions:
                TreeXML.appendTreeElement(
                    distributions_xml_node,
                    "distribution-usage",
                    name=getDistributionName(distribution),
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
                    "distribution-lookup",
                    name=distribution_name,
                    found="yes" if found else "no",
                )

        used_modules_xml_node = TreeXML.appendTreeElement(
            module_xml_node,
            "module_usages",
        )

        for count, used_module in enumerate(
            report_input_data["module_usages"][module_name]
        ):
            # We don't want to see those parent imports, unless they have
            # an effect.
            if used_module.reason == "import path parent":
                while True:
                    count += 1
                    next_used_module = report_input_data["module_usages"][module_name][
                        count
                    ]

                    if next_used_module.reason != "import path parent":
                        break

                exclusion_reason = report_input_data["module_exclusions"][
                    module_name
                ].get(next_used_module.module_name)

                if exclusion_reason is None or next_used_module.finding != "not-found":
                    continue

            module_usage_node = TreeXML.appendTreeElement(
                used_modules_xml_node,
                "module_usage",
                name=used_module.module_name.asString(),
                finding=used_module.finding,
                line=str(used_module.source_ref.getLineNumber()),
                # TODO: Add reason in a hotfix.
                # reason=used_module.reason,
            )

            exclusion_reason = report_input_data["module_exclusions"][module_name].get(
                used_module.module_name
            )

            # Include reason why a module was excluded unless it is obvious like
            # with built-in modules.
            if exclusion_reason is not None and used_module.module_kind != "built-in":
                module_usage_node.attrib["finding"] = "excluded"
                module_usage_node.attrib["exclusion_reason"] = exclusion_reason


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
        mode=report_input_data["compilation_mode"],
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

    if report_input_data["scons_error_report_data"]:
        scons_error_reports_node = TreeXML.appendTreeElement(
            root, "scons_error_reports"
        )

        for cmd, (stdout, stderr) in report_input_data[
            "scons_error_report_data"
        ].items():
            scons_error_report_node = TreeXML.appendTreeElement(
                scons_error_reports_node, "scons_error_report"
            )

            TreeXML.appendTreeElement(
                scons_error_report_node,
                "command",
            ).text = cmd

            if stdout:
                if not stdout.startswith("\n"):
                    stdout = "\n" + stdout

                stdout = stdout.rstrip("\n") + "\n"

                TreeXML.appendTreeElement(
                    scons_error_report_node,
                    "stdout",
                ).text = stdout

            if stderr:
                if not stderr.startswith("\n"):
                    stderr = "\n" + stderr

                stderr = stderr.rstrip("\n") + "\n"

                TreeXML.appendTreeElement(
                    scons_error_report_node,
                    "stderr",
                ).text = stderr

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

    if report_input_data["included_metadata"]:
        metadata_node = TreeXML.appendTreeElement(
            root,
            "metadata",
        )

        for distribution_name, reasons in sorted(
            report_input_data["included_metadata"].items()
        ):
            TreeXML.appendTreeElement(
                metadata_node,
                "included_metadata",
                name=distribution_name,
                reason=". ".join(reasons),
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
            reason=standalone_entry_point.reason,
            # TODO: No reason yet.
        )

    for standalone_entry_point, (reason, removed_dll_paths) in getRemovedUsedDllsInfo():
        for removed_dll_path in removed_dll_paths:
            TreeXML.appendTreeElement(
                root,
                "excluded_dll",
                name=_getCompilationReportPath(removed_dll_path),
                used_by=standalone_entry_point.dest_path,
                reason=reason,
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
        distribution_node = TreeXML.appendTreeElement(
            distributions_xml_node,
            "distribution",
            name=getDistributionName(distribution),
            version=getDistributionVersion(distribution),
            installer=report_input_data["module_distribution_installers"][
                getDistributionName(distribution)
            ],
        )

        if report_input_data["module_distribution_vendored"][
            getDistributionName(distribution)
        ]:
            distribution_node.attrib["vendored"] = "yes"

    python_xml_node = TreeXML.appendTreeElement(
        root,
        "python",
        python_exe=_getCompilationReportPath(report_input_data["python_exe"]),
        python_flavor=report_input_data["python_flavor"],
        python_version=report_input_data["python_version"],
        os_name=report_input_data["os_name"],
        os_release=report_input_data["os_release"],
        arch_name=report_input_data["arch_name"],
        filesystem_encoding=report_input_data["filesystem_encoding"],
    )

    search_path = getPackageSearchPath(None)

    if search_path is not None:
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

    python_xml_node = TreeXML.appendTreeElement(
        root,
        "output",
        run_filename=_getCompilationReportPath(
            report_input_data["output_run_filename"]
        ),
    )

    contents = TreeXML.toString(root)

    if type(contents) is not bytes:
        contents = contents.encode("utf8")

    try:
        putBinaryFileContents(filename=report_filename, contents=contents)
    except OSError as e:
        reports_logger.warning(
            "Compilation report write to file '%s' failed due to: %s."
            % (report_filename, e)
        )

        if _crash_report_filename == report_filename:
            _crash_report_filename = None
    else:
        if _crash_report_filename != report_filename:
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

    def quoted(value):
        if isinstance(value, str):
            return "'%s'" % value
        else:
            return [quoted(element) for element in value]

    report_text = template.render(
        # Get the license text.
        get_distribution_license=getDistributionLicense,
        # get the distribution_name
        get_distribution_name=getDistributionName,
        # get the distribution version
        get_distribution_version=getDistributionVersion,
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
_crash_report_bug_message = True


def _informAboutCrashReport():
    if _crash_report_filename is not None:
        message = (
            "Compilation crash report written to file '%s'." % _crash_report_filename
        )

        if _crash_report_bug_message:
            message += " Please include it in your bug report."

        reports_logger.info(
            message,
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

        # Inform user about bug reporting of a bug only, if this is not some sort
        # of reporting exit, these do not constitute definitive bugs of Nuitka but
        # are often usage errors only.

        # Using global here, as this is really a singleton
        # pylint: disable=global-statement
        global _crash_report_bug_message
        _crash_report_bug_message = sys.exc_info()[0] is not ReportingSystemExit

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
