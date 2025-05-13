#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" This is the main actions of Nuitka.

This can do all the steps to translate one module to a target language using
the Python C/API, to compile it to either an executable or an extension
module, potentially with bytecode included and used library copied into
a distribution folder.

"""

import os
import sys

from nuitka.build.DataComposerInterface import runDataComposer
from nuitka.build.SconsUtils import (
    getSconsReportValue,
    readSconsErrorReport,
    readSconsReport,
)
from nuitka.code_generation.ConstantCodes import (
    addDistributionMetadataValue,
    getDistributionMetadataValues,
)
from nuitka.freezer.IncludedDataFiles import (
    addIncludedDataFilesFromFileOptions,
    addIncludedDataFilesFromPackageOptions,
    addIncludedDataFilesFromPlugins,
    copyDataFiles,
)
from nuitka.freezer.IncludedEntryPoints import (
    addExtensionModuleEntryPoint,
    addIncludedEntryPoints,
    getStandaloneEntryPoints,
    setMainEntryPoint,
)
from nuitka.importing.Importing import locateModule, setupImportingFromOptions
from nuitka.importing.Recursion import (
    scanIncludedPackage,
    scanPluginFilenamePattern,
    scanPluginPath,
    scanPluginSinglePath,
)
from nuitka.Options import (
    getPythonPgoInput,
    hasPythonFlagIsolated,
    hasPythonFlagNoAnnotations,
    hasPythonFlagNoAsserts,
    hasPythonFlagNoBytecodeRuntimeCache,
    hasPythonFlagNoCurrentDirectoryInPath,
    hasPythonFlagNoDocStrings,
    hasPythonFlagNoWarnings,
    hasPythonFlagUnbuffered,
    isExperimental,
)
from nuitka.plugins.Plugins import Plugins
from nuitka.PostProcessing import executePostProcessing
from nuitka.Progress import (
    closeProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.PythonFlavors import (
    getPythonFlavorName,
    isApplePython,
    isArchPackagePython,
    isDebianPackagePython,
    isFedoraPackagePython,
    isNuitkaPython,
    isPyenvPython,
)
from nuitka.PythonVersions import (
    getModuleLinkerLibs,
    getPythonABI,
    getSupportedPythonVersions,
    python_version,
    python_version_str,
)
from nuitka.Serialization import ConstantAccessor
from nuitka.Tracing import (
    doNotBreakSpaces,
    general,
    inclusion_logger,
    pgo_logger,
)
from nuitka.tree import SyntaxErrors
from nuitka.tree.ReformulationMultidist import createMultidistMainSourceCode
from nuitka.utils import InstanceCounters
from nuitka.utils.Distributions import getDistribution
from nuitka.utils.Execution import (
    callProcess,
    withEnvironmentVarOverridden,
    wrapCommandForDebuggerForExec,
)
from nuitka.utils.FileOperations import (
    changeFilenameExtension,
    deleteFile,
    getExternalUsePath,
    getReportPath,
    openTextFile,
    removeDirectory,
    resetDirectory,
)
from nuitka.utils.Importing import getPackageDirFilename
from nuitka.utils.MemoryUsage import reportMemoryUsage, showMemoryTrace
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.ReExecute import callExecProcess, reExecuteNuitka
from nuitka.utils.StaticLibraries import getSystemStaticLibPythonPath
from nuitka.utils.Utils import getArchitecture, isMacOS, isWin32Windows
from nuitka.Version import getCommercialVersion, getNuitkaVersion

from . import ModuleRegistry, Options, OutputDirectories
from .build.SconsInterface import (
    asBoolStr,
    cleanSconsDirectory,
    getCommonSconsOptions,
    runScons,
    setPythonTargetOptions,
)
from .code_generation import CodeGeneration, LoaderCodes, Reports
from .finalizations import Finalization
from .freezer.Onefile import getCompressorPython, packDistFolderToOnefile
from .freezer.Standalone import (
    checkFreezingModuleSet,
    copyDllsUsed,
    detectUsedDLLs,
)
from .optimizations.Optimization import optimizeModules
from .pgo.PGO import readPGOInputFile
from .reports.Reports import writeCompilationReports
from .tree.Building import buildMainModuleTree
from .tree.SourceHandling import writeSourceCode
from .TreeXML import dumpTreeXMLToFile


def _createMainModule():
    """Create a node tree.

    Turn that source code into a node tree structure. If following into
    imported modules is allowed, more trees will be available during
    optimization, or even immediately through forcefully included
    directory paths.

    """
    # Many cases and details to deal with, pylint: disable=too-many-branches

    Plugins.onBeforeCodeParsing()

    # First, build the raw node tree from the source code.
    if Options.isMultidistMode():
        assert not Options.shallMakeModule()

        main_module = buildMainModuleTree(
            source_code=createMultidistMainSourceCode(),
        )
    else:
        main_module = buildMainModuleTree(
            source_code=None,
        )

    OutputDirectories.setMainModule(main_module)

    for distribution_name in Options.getShallIncludeDistributionMetadata():
        distribution = getDistribution(distribution_name)

        if distribution is None:
            general.sysexit(
                "Error, could not find distribution '%s' for which metadata was asked to be included."
                % distribution_name
            )

        addDistributionMetadataValue(
            distribution_name=distribution_name,
            distribution=distribution,
            reason="user requested",
        )

    # First remove old object files and old generated files, old binary or
    # module, and standalone mode program directory if any, they can only do
    # harm.
    source_dir = OutputDirectories.getSourceDirectoryPath()

    if not Options.shallOnlyExecCCompilerCall():
        cleanSconsDirectory(source_dir)

        # Prepare the ".dist" directory, throwing away what was there before.
        if Options.isStandaloneMode():
            standalone_dir = OutputDirectories.getStandaloneDirectoryPath(bundle=False)
            resetDirectory(
                path=standalone_dir,
                logger=general,
                ignore_errors=True,
                extra_recommendation="Stop previous binary.",
            )

            if Options.shallCreateAppBundle():
                resetDirectory(
                    path=changeFilenameExtension(standalone_dir, ".app"),
                    logger=general,
                    ignore_errors=True,
                    extra_recommendation=None,
                )

    # Delete result file, to avoid confusion with previous build and to
    # avoid locking issues after the build.
    deleteFile(
        path=OutputDirectories.getResultFullpath(onefile=False), must_exist=False
    )
    if Options.isOnefileMode():
        deleteFile(
            path=OutputDirectories.getResultFullpath(onefile=True), must_exist=False
        )

        # Also make sure we inform the user in case the compression is not possible.
        getCompressorPython()

    # Second, do it for the directories given.
    for plugin_filename in Options.getShallFollowExtra():
        scanPluginPath(plugin_filename=plugin_filename, module_package=None)

    for pattern in Options.getShallFollowExtraFilePatterns():
        scanPluginFilenamePattern(pattern=pattern)

    # For packages, include the full suite.
    if Options.shallMakePackage():
        scanIncludedPackage(main_module.getFullName())

    for package_name in Options.getMustIncludePackages():
        scanIncludedPackage(package_name)

    for module_name in Options.getMustIncludeModules():
        module_name, module_filename, module_kind, finding = locateModule(
            module_name=ModuleName(module_name),
            parent_package=None,
            level=0,
        )

        if finding != "absolute":
            inclusion_logger.sysexit(
                "Error, failed to locate module '%s' that you asked to include."
                % module_name.asString()
            )

        if module_kind == "built-in":
            # TODO:
            inclusion_logger.warning(
                "Note, module '%s' that you asked to include is built-in."
                % module_name.asString()
            )
        else:
            scanPluginSinglePath(
                plugin_filename=module_filename,
                module_package=module_name.getPackageName(),
                package_only=True,
            )

    # Allow plugins to add more modules based on the initial set being complete.
    Plugins.onModuleInitialSet()

    # Then optimize the tree and potentially recursed modules.
    # TODO: The passed filename is really something that should come from
    # a command line option, it's a filename for the graph, which might not
    # need a default at all.
    optimizeModules(main_module.getOutputFilename())

    # Freezer may have concerns for some modules.
    if Options.isStandaloneMode():
        checkFreezingModuleSet()

    # Check if distribution meta data is included, that cannot be used.
    for distribution_name, meta_data_value in getDistributionMetadataValues():
        if not ModuleRegistry.hasDoneModule(meta_data_value.module_name):
            inclusion_logger.sysexit(
                "Error, including metadata for distribution '%s' without including related package '%s'."
                % (distribution_name, meta_data_value.module_name)
            )

    # Allow plugins to comment on final module set.
    Plugins.onModuleCompleteSet()

    if Options.isExperimental("check_xml_persistence"):
        for module in ModuleRegistry.getRootModules():
            if module.isMainModule():
                return module

        assert False
    else:
        # Main module might change behind our back, look it up again.
        return main_module


def dumpTreeXML():
    filename = Options.getXMLDumpOutputFilename()

    if filename is not None:
        with openTextFile(filename, "wb") as output_file:
            # XML output only.
            for module in ModuleRegistry.getDoneModules():
                dumpTreeXMLToFile(tree=module.asXml(), output_file=output_file)

        general.info("XML dump of node state written to file '%s'." % filename)


def pickSourceFilenames(source_dir, modules):
    """Pick the names for the C files of each module.

    Args:
        source_dir - the directory to put the module sources will be put into
        modules    - all the modules to build.

    Returns:
        Dictionary mapping modules to filenames in source_dir.

    Notes:
        These filenames can collide, due to e.g. mixed case usage, or there
        being duplicate copies, e.g. a package named the same as the main
        binary.

        Conflicts are resolved by appending @<number> with a count in the
        list of sorted modules. We try to be reproducible here, so we get
        still good caching for external tools.
    """

    collision_filenames = set()

    def _getModuleFilenames(module):
        base_filename = os.path.join(source_dir, "module." + module.getFullName())

        # Note: Could detect if the file system is cases sensitive in source_dir
        # or not, but that's probably not worth the effort. False positives do
        # no harm at all. We cannot use normcase, as macOS is not using one that
        # will tell us the truth.
        collision_filename = base_filename.lower()

        return base_filename, collision_filename

    seen_filenames = set()

    # First pass, check for collisions.
    for module in modules:
        if module.isPythonExtensionModule():
            continue

        _base_filename, collision_filename = _getModuleFilenames(module)

        if collision_filename in seen_filenames:
            collision_filenames.add(collision_filename)

        seen_filenames.add(collision_filename)

    # Our output.
    module_filenames = {}

    # Count up for colliding filenames as we go.
    collision_counts = {}

    # Second pass, this time sorted, so we get deterministic results. We will
    # apply an "@1"/"@2",... to disambiguate the filenames.
    for module in sorted(modules, key=lambda x: x.getFullName()):
        if module.isPythonExtensionModule():
            continue

        base_filename, collision_filename = _getModuleFilenames(module)

        if collision_filename in collision_filenames:
            collision_counts[collision_filename] = (
                collision_counts.get(collision_filename, 0) + 1
            )
            base_filename += "@%d" % collision_counts[collision_filename]

        module_filenames[module] = base_filename + ".c"

    return module_filenames


def makeSourceDirectory():
    """Get the full list of modules imported, create code for all of them."""
    # We deal with a lot of details here, but rather one by one, and split makes
    # no sense, pylint: disable=too-many-branches

    # assert main_module in ModuleRegistry.getDoneModules()

    # Lets check if the asked modules are actually present, and warn the
    # user if one of those was not found.
    for any_case_module in Options.getShallFollowModules():
        if "*" in any_case_module or "{" in any_case_module:
            continue

        if not ModuleRegistry.hasDoneModule(
            any_case_module
        ) and not ModuleRegistry.hasRootModule(any_case_module):
            general.warning(
                "Did not follow import to unused '%s', consider include options."
                % any_case_module
            )

    # Prepare code generation, i.e. execute finalization for it.
    for module in ModuleRegistry.getDoneModules():
        if module.isCompiledPythonModule():
            Finalization.prepareCodeGeneration(module)

    # Do some reporting and determine compiled module to work on
    compiled_modules = []

    for module in ModuleRegistry.getDoneModules():
        if module.isCompiledPythonModule():
            compiled_modules.append(module)

            if Options.isShowInclusion():
                inclusion_logger.info(
                    "Included compiled module '%s'." % module.getFullName()
                )
        elif module.isPythonExtensionModule():
            addExtensionModuleEntryPoint(module)

            if Options.isShowInclusion():
                inclusion_logger.info(
                    "Included extension module '%s'." % module.getFullName()
                )
        elif module.isUncompiledPythonModule():
            if Options.isShowInclusion():
                inclusion_logger.info(
                    "Included uncompiled module '%s'." % module.getFullName()
                )
        else:
            assert False, module

    # Pick filenames.
    source_dir = OutputDirectories.getSourceDirectoryPath()

    module_filenames = pickSourceFilenames(
        source_dir=source_dir, modules=compiled_modules
    )

    setupProgressBar(
        stage="C Source Generation",
        unit="module",
        total=len(compiled_modules),
    )

    # Generate code for compiled modules, this can be slow, so do it separately
    # with a progress bar.
    for module in compiled_modules:
        c_filename = module_filenames[module]

        reportProgressBar(
            item=module.getFullName(),
        )

        source_code = CodeGeneration.generateModuleCode(
            module=module,
            data_filename=os.path.basename(c_filename[:-2] + ".const"),
        )

        writeSourceCode(filename=c_filename, source_code=source_code)

    closeProgressBar()

    (
        helper_decl_code,
        helper_impl_code,
        constants_header_code,
        constants_body_code,
    ) = CodeGeneration.generateHelpersCode()

    writeSourceCode(
        filename=os.path.join(source_dir, "__helpers.h"), source_code=helper_decl_code
    )

    writeSourceCode(
        filename=os.path.join(source_dir, "__helpers.c"), source_code=helper_impl_code
    )

    writeSourceCode(
        filename=os.path.join(source_dir, "__constants.h"),
        source_code=constants_header_code,
    )

    writeSourceCode(
        filename=os.path.join(source_dir, "__constants.c"),
        source_code=constants_body_code,
    )


def _runPgoBinary():
    pgo_executable = OutputDirectories.getPgoRunExecutable()

    if not os.path.isfile(pgo_executable):
        general.sysexit("Error, failed to produce PGO binary '%s'" % pgo_executable)

    return callProcess(
        [getExternalUsePath(pgo_executable)] + Options.getPgoArgs(),
        shell=False,
    )


def _wasMsvcMode():
    if not isWin32Windows():
        return False

    return (
        getSconsReportValue(
            source_dir=OutputDirectories.getSourceDirectoryPath(), key="msvc_mode"
        )
        == "True"
    )


def _deleteMsvcPGOFiles(pgo_mode):
    assert _wasMsvcMode()

    msvc_pgc_filename = OutputDirectories.getResultBasePath(onefile=False) + "!1.pgc"
    deleteFile(msvc_pgc_filename, must_exist=False)

    if pgo_mode == "use":
        msvc_pgd_filename = OutputDirectories.getResultBasePath(onefile=False) + ".pgd"
        deleteFile(msvc_pgd_filename, must_exist=False)

    return msvc_pgc_filename


def _runCPgoBinary():
    # Note: For exit codes, we do not insist on anything yet, maybe we could point it out
    # or ask people to make scripts that buffer these kinds of errors, and take an error
    # instead as a serious failure.

    general.info(
        "Running created binary to produce C level PGO information:", style="blue"
    )

    if _wasMsvcMode():
        msvc_pgc_filename = _deleteMsvcPGOFiles(pgo_mode="generate")

        with withEnvironmentVarOverridden(
            "PATH",
            getSconsReportValue(
                source_dir=OutputDirectories.getSourceDirectoryPath(), key="PATH"
            ),
        ):
            exit_code_pgo = _runPgoBinary()

        pgo_data_collected = os.path.exists(msvc_pgc_filename)
    else:
        exit_code_pgo = _runPgoBinary()

        # gcc file suffix, spell-checker: ignore gcda
        gcc_constants_pgo_filename = os.path.join(
            OutputDirectories.getSourceDirectoryPath(), "__constants.gcda"
        )

        pgo_data_collected = os.path.exists(gcc_constants_pgo_filename)

    if exit_code_pgo != 0:
        pgo_logger.warning(
            """\
Error, the C PGO compiled program error exited. Make sure it works \
fully before using '--pgo-c' option."""
        )

    if not pgo_data_collected:
        pgo_logger.sysexit(
            """\
Error, no C PGO compiled program did not produce expected information, \
did the created binary run at all?"""
        )

    pgo_logger.info("Successfully collected C level PGO information.", style="blue")


def _runPythonPgoBinary():
    # Note: For exit codes, we do not insist on anything yet, maybe we could point it out
    # or ask people to make scripts that buffer these kinds of errors, and take an error
    # instead as a serious failure.

    pgo_filename = OutputDirectories.getPgoRunInputFilename()

    with withEnvironmentVarOverridden("NUITKA_PGO_OUTPUT", pgo_filename):
        exit_code = _runPgoBinary()

    if not os.path.exists(pgo_filename):
        general.sysexit(
            """\
Error, no Python PGO information produced, did the created binary
run (exit code %d) as expected?"""
            % exit_code
        )

    return pgo_filename


def runSconsBackend():
    # Scons gets transported many details, that we express as variables, and
    # have checks for them, leading to many branches and statements,
    # pylint: disable=too-many-branches,too-many-statements
    scons_options, env_values = getCommonSconsOptions()

    setPythonTargetOptions(scons_options)

    scons_options["source_dir"] = OutputDirectories.getSourceDirectoryPath()
    scons_options["nuitka_python"] = asBoolStr(isNuitkaPython())
    scons_options["debug_mode"] = asBoolStr(Options.is_debug)
    scons_options["debugger_mode"] = asBoolStr(Options.shallRunInDebugger())
    scons_options["python_debug"] = asBoolStr(Options.shallUsePythonDebug())
    scons_options["full_compat"] = asBoolStr(Options.is_full_compat)
    scons_options["experimental"] = ",".join(Options.getExperimentalIndications())
    scons_options["trace_mode"] = asBoolStr(Options.shallTraceExecution())
    scons_options["file_reference_mode"] = Options.getFileReferenceMode()
    scons_options["compiled_module_count"] = "%d" % len(
        ModuleRegistry.getCompiledModules()
    )

    if Options.isLowMemory():
        scons_options["low_memory"] = asBoolStr(True)

    scons_options["result_exe"] = OutputDirectories.getResultFullpath(onefile=False)

    if not Options.shallMakeModule():
        main_module = ModuleRegistry.getRootTopModule()
        assert main_module.isMainModule()

        main_module_name = main_module.getFullName()
        if main_module_name != "__main__":
            scons_options["main_module_name"] = main_module_name

    if Options.shallUseStaticLibPython():
        scons_options["static_libpython"] = getSystemStaticLibPythonPath()

    if isDebianPackagePython():
        scons_options["debian_python"] = asBoolStr(True)
    if isFedoraPackagePython():
        scons_options["fedora_python"] = asBoolStr(True)
    if isArchPackagePython():
        scons_options["arch_python"] = asBoolStr(True)
    if isApplePython():
        scons_options["apple_python"] = asBoolStr(True)
    if isPyenvPython():
        scons_options["pyenv_python"] = asBoolStr(True)

    if Options.getForcedStdoutPath():
        scons_options["forced_stdout_path"] = Options.getForcedStdoutPath()

    if Options.getForcedStderrPath():
        scons_options["forced_stderr_path"] = Options.getForcedStderrPath()

    if Options.isProfile():
        scons_options["profile_mode"] = asBoolStr(True)

    if Options.shallTreatUninstalledPython():
        scons_options["uninstalled_python"] = asBoolStr(True)

    if ModuleRegistry.getUncompiledTechnicalModules():
        scons_options["frozen_modules"] = str(
            len(ModuleRegistry.getUncompiledTechnicalModules())
        )

    if hasPythonFlagNoWarnings():
        scons_options["no_python_warnings"] = asBoolStr(True)

    if hasPythonFlagNoAsserts():
        scons_options["python_sysflag_optimize"] = str(
            2 if hasPythonFlagNoDocStrings() else 1
        )

        scons_options["python_flag_no_asserts"] = asBoolStr(True)

    if hasPythonFlagNoDocStrings():
        scons_options["python_flag_no_docstrings"] = asBoolStr(True)

    if hasPythonFlagNoAnnotations():
        scons_options["python_flag_no_annotations"] = asBoolStr(True)

    if python_version < 0x300 and sys.flags.py3k_warning:
        scons_options["python_sysflag_py3k_warning"] = asBoolStr(True)

    if python_version < 0x300 and (
        sys.flags.division_warning or sys.flags.py3k_warning
    ):
        scons_options["python_sysflag_division_warning"] = asBoolStr(True)

    if sys.flags.bytes_warning:
        scons_options["python_sysflag_bytes_warning"] = asBoolStr(True)

    if int(os.getenv("NUITKA_NOSITE_FLAG", Options.hasPythonFlagNoSite())):
        scons_options["python_sysflag_no_site"] = asBoolStr(True)

    if Options.hasPythonFlagTraceImports():
        scons_options["python_sysflag_verbose"] = asBoolStr(True)

    if Options.hasPythonFlagNoRandomization():
        scons_options["python_sysflag_no_randomization"] = asBoolStr(True)

    if python_version < 0x300 and sys.flags.unicode:
        scons_options["python_sysflag_unicode"] = asBoolStr(True)

    if python_version >= 0x370 and sys.flags.utf8_mode:
        scons_options["python_sysflag_utf8"] = asBoolStr(True)

    if hasPythonFlagNoBytecodeRuntimeCache():
        scons_options["python_sysflag_dontwritebytecode"] = asBoolStr(True)

    if hasPythonFlagNoCurrentDirectoryInPath():
        scons_options["python_sysflag_safe_path"] = asBoolStr(True)

    if hasPythonFlagUnbuffered():
        scons_options["python_sysflag_unbuffered"] = asBoolStr(True)

    if hasPythonFlagIsolated():
        scons_options["python_sysflag_isolated"] = asBoolStr(True)

    abiflags = getPythonABI()
    if abiflags:
        scons_options["abiflags"] = abiflags

    link_module_libs = getModuleLinkerLibs()
    if link_module_libs:
        scons_options["link_module_libs"] = ",".join(link_module_libs)

    # Allow plugins to build definitions.
    env_values.update(Plugins.getBuildDefinitions())

    if Options.shallCreatePythonPgoInput():
        scons_options["pgo_mode"] = "python"

        result = runScons(
            scons_options=scons_options,
            env_values=env_values,
            scons_filename="Backend.scons",
        )

        if not result:
            return result, scons_options

        # Need to make it usable before executing it.
        executePostProcessing(scons_options["result_exe"])
        _runPythonPgoBinary()

        return True, scons_options

        # Need to restart compilation from scratch here.
    if Options.isCPgoMode():
        # For C level PGO, we have a 2 pass system. TODO: Make it more global for onefile
        # and standalone mode proper support, which might need data files to be
        # there, which currently are not yet there, so it won't run.
        if Options.isCPgoMode():
            scons_options["pgo_mode"] = "generate"

            result = runScons(
                scons_options=scons_options,
                env_values=env_values,
                scons_filename="Backend.scons",
            )

            if not result:
                return result, scons_options

            # Need to make it usable before executing it.
            executePostProcessing(scons_options["result_exe"])
            _runCPgoBinary()
            scons_options["pgo_mode"] = "use"

    result = (
        runScons(
            scons_options=scons_options,
            env_values=env_values,
            scons_filename="Backend.scons",
        ),
        scons_options,
    )

    # Delete PGO files if asked to do that.
    if scons_options.get("pgo_mode") == "use" and _wasMsvcMode():
        _deleteMsvcPGOFiles(pgo_mode="use")

    return result


def callExecPython(args, add_path, uac):
    if add_path:
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] += ":" + Options.getOutputDir()
        else:
            os.environ["PYTHONPATH"] = Options.getOutputDir()

    # Add the main arguments, previous separated.
    args += Options.getPositionalArgs()[1:] + Options.getMainArgs()

    callExecProcess(args, uac=uac)


def _executeMain(binary_filename):
    # Wrap in debugger, unless the CMD file contains that call already.
    if Options.shallRunInDebugger() and not Options.shallCreateScriptFileForExecution():
        args = wrapCommandForDebuggerForExec(command=(binary_filename,))
    else:
        args = (binary_filename, binary_filename)

    callExecPython(
        args=args,
        add_path=False,
        uac=isWin32Windows() and Options.shallAskForWindowsAdminRights(),
    )


def _executeModule(tree):
    """Execute the extension module just created."""

    if python_version < 0x300:
        python_command_template = """\
import os, imp;\
assert os.path.normcase(os.path.abspath(os.path.normpath(\
imp.find_module('%(module_name)s')[1]))) == %(expected_filename)r,\
'Error, cannot launch extension module %(module_name)s, original package is in the way.'"""
    else:
        python_command_template = """\
import os, importlib.util;\
assert os.path.normcase(os.path.abspath(os.path.normpath(\
importlib.util.find_spec('%(module_name)s').origin))) == %(expected_filename)r,\
'Error, cannot launch extension module %(module_name)s, original package is in the way.'"""

    output_dir = os.path.normpath(Options.getOutputDir())
    if output_dir != ".":
        python_command_template = (
            """\
import sys; sys.path.insert(0, %(output_dir)r)
"""
            + python_command_template
        )

    python_command_template += ";__import__('%(module_name)s')"

    python_command = python_command_template % {
        "module_name": tree.getName(),
        "expected_filename": os.path.normcase(
            os.path.abspath(
                os.path.normpath(OutputDirectories.getResultFullpath(onefile=False))
            )
        ),
        "output_dir": output_dir,
    }

    if Options.shallRunInDebugger():
        args = wrapCommandForDebuggerForExec(
            command=(sys.executable, "-c", python_command)
        )
    else:
        args = (sys.executable, "python", "-c", python_command)

    callExecPython(args=args, add_path=True, uac=False)


def compileTree():
    source_dir = OutputDirectories.getSourceDirectoryPath()

    general.info("Completed Python level compilation and optimization.")

    if not Options.shallOnlyExecCCompilerCall():
        general.info("Generating source code for C backend compiler.")

        reportMemoryUsage(
            "before_c_code_generation",
            (
                "Total memory usage before generating C code:"
                if Options.isShowProgress() or Options.isShowMemory()
                else None
            ),
        )

        # Now build the target language code for the whole tree.
        makeSourceDirectory()

        bytecode_accessor = ConstantAccessor(
            data_filename="__bytecode.const", top_level_name="bytecode_data"
        )

        # This should take all bytecode values, even ones needed for frozen or
        # not produce anything.
        loader_code = LoaderCodes.getMetaPathLoaderBodyCode(bytecode_accessor)

        writeSourceCode(
            filename=os.path.join(source_dir, "__loader.c"), source_code=loader_code
        )

    else:
        source_dir = OutputDirectories.getSourceDirectoryPath()

        if not os.path.isfile(os.path.join(source_dir, "__helpers.h")):
            general.sysexit("Error, no previous build directory exists.")

    reportMemoryUsage(
        "before_running_scons",
        (
            "Total memory usage before running scons"
            if Options.isShowProgress() or Options.isShowMemory()
            else None
        ),
    )

    if Options.isShowMemory():
        InstanceCounters.printStats()

    Reports.doMissingOptimizationReport()

    if Options.shallNotDoExecCCompilerCall():
        return True, {}

    general.info("Running data composer tool for optimal constant value handling.")

    runDataComposer(source_dir)

    Plugins.writeExtraCodeFiles(onefile=False)

    general.info("Running C compilation via Scons.")

    # Run the Scons to build things.
    result, scons_options = runSconsBackend()

    return result, scons_options


def handleSyntaxError(e):
    # Syntax or indentation errors, output them to the user and abort. If
    # we are not in full compat, and user has not specified the Python
    # versions he wants, tell him about the potential version problem.
    error_message = SyntaxErrors.formatOutput(e)

    if not Options.is_full_compat:
        suggested_python_version_str = getSupportedPythonVersions()[-1]

        error_message += """

Nuitka is very syntax compatible with standard Python. It is currently running
with Python version '%s', you might want to specify more clearly with the use
of the precise Python interpreter binary and '-m nuitka', e.g. use this
'python%s -m nuitka' option, if that's not the one the program expects.
""" % (
            python_version_str,
            suggested_python_version_str,
        )

    # Important to have the same error
    sys.exit(error_message)


def _main():
    """Main program flow of Nuitka

    At this point, options will be parsed already, Nuitka will be executing
    in the desired version of Python with desired flags, and we just get
    to execute the task assigned.

    We might be asked to only re-compile generated C, dump only an XML
    representation of the internal node tree after optimization, etc.
    """

    # Main has to fulfill many options, leading to many branches and statements
    # to deal with them.  pylint: disable=too-many-branches,too-many-statements

    # In case we are in a PGO run, we read its information first, so it becomes
    # available for later parts.
    pgo_filename = getPythonPgoInput()
    if pgo_filename is not None:
        readPGOInputFile(pgo_filename)

    general.info(
        leader="Starting Python compilation with:",
        message="%s %s %s."
        % doNotBreakSpaces(
            "Version '%s'" % getNuitkaVersion(),
            "on Python %s (flavor '%s')" % (python_version_str, getPythonFlavorName()),
            "commercial grade '%s'" % (getCommercialVersion() or "not installed"),
        ),
    )

    reportMemoryUsage(
        "after_launch",
        (
            "Total memory usage before processing:"
            if Options.isShowProgress() or Options.isShowMemory()
            else None
        ),
    )

    # Initialize the importing layer from options, main filenames, debugging
    # options, etc.
    setupImportingFromOptions()

    Plugins.onCompilationStartChecks()

    addIncludedDataFilesFromFileOptions()
    addIncludedDataFilesFromPackageOptions()

    # Turn that source code into a node tree structure.
    try:
        main_module = _createMainModule()
    except (SyntaxError, IndentationError) as e:
        handleSyntaxError(e)

    addIncludedDataFilesFromPlugins()

    dumpTreeXML()

    # Make the actual compilation.
    result, scons_options = compileTree()

    # Exit if compilation failed.
    if not result:
        general.sysexit(
            message="Failed unexpectedly in Scons C backend compilation.",
            mnemonic="scons-backend-failure",
            reporting=True,
        )

    # Relaunch in case of Python PGO input to be produced.
    if Options.shallCreatePythonPgoInput():
        # Will not return.
        pgo_filename = OutputDirectories.getPgoRunInputFilename()
        general.info(
            "Restarting compilation using collected information from '%s'."
            % pgo_filename
        )
        reExecuteNuitka(pgo_filename=pgo_filename)

    if Options.shallNotDoExecCCompilerCall():
        if Options.isShowMemory():
            showMemoryTrace()

        sys.exit(0)

    executePostProcessing(scons_options["result_exe"])

    if not Options.shallOnlyExecCCompilerCall():
        data_file_paths = copyDataFiles(
            standalone_entry_points=getStandaloneEntryPoints()
        )

    if Options.isStandaloneMode():
        binary_filename = scons_options["result_exe"]

        setMainEntryPoint(binary_filename)

        for module in ModuleRegistry.getDoneModules():
            addIncludedEntryPoints(Plugins.considerExtraDlls(module))

        detectUsedDLLs(
            standalone_entry_points=getStandaloneEntryPoints(),
            source_dir=OutputDirectories.getSourceDirectoryPath(),
        )

        dist_dir = OutputDirectories.getStandaloneDirectoryPath()

        if not Options.shallOnlyExecCCompilerCall():
            copyDllsUsed(
                dist_dir=dist_dir,
                standalone_entry_points=getStandaloneEntryPoints(),
                data_file_paths=data_file_paths,
            )

    if Options.isStandaloneMode():
        Plugins.onStandaloneDistributionFinished(dist_dir)

        if Options.isOnefileMode():
            packDistFolderToOnefile(dist_dir)

            if Options.isRemoveBuildDir():
                general.info("Removing dist folder '%s'." % dist_dir)

                removeDirectory(
                    path=dist_dir,
                    logger=general,
                    ignore_errors=False,
                    extra_recommendation=None,
                )
            else:
                general.info(
                    "Keeping dist folder '%s' for inspection, no need to use it."
                    % dist_dir
                )

    # Remove the source directory (now build directory too) if asked to.
    source_dir = OutputDirectories.getSourceDirectoryPath()

    if Options.isRemoveBuildDir():
        general.info("Removing build directory '%s'." % source_dir)

        # Make sure the scons report is cached before deleting it.
        readSconsReport(source_dir)
        readSconsErrorReport(source_dir)

        removeDirectory(
            path=source_dir,
            logger=general,
            ignore_errors=False,
            extra_recommendation=None,
        )
        assert not os.path.exists(source_dir)
    else:
        general.info("Keeping build directory '%s'." % source_dir)

    final_filename = OutputDirectories.getResultFullpath(
        onefile=Options.isOnefileMode()
    )

    if Options.isStandaloneMode() and isMacOS():
        general.info(
            "Created binary that runs on macOS %s (%s) or higher."
            % (scons_options["macos_min_version"], scons_options["macos_target_arch"])
        )

        if scons_options["macos_target_arch"] != getArchitecture():
            general.warning(
                "It will only work as well as 'arch -%s %s %s' does."
                % (
                    scons_options["macos_target_arch"],
                    sys.executable,
                    Options.getMainEntryPointFilenames()[0],
                ),
                mnemonic="macos-cross-compile",
            )

    Plugins.onFinalResult(final_filename)

    if Options.shallMakeModule():
        base_path = OutputDirectories.getResultBasePath(onefile=False)

        if os.path.isdir(base_path) and getPackageDirFilename(base_path):
            general.warning(
                """\
The compilation result is hidden by package directory '%s'. Importing will \
not use compiled code while it exists because it has precedence while both \
exist, out e.g. '--output-dir=output' to sure is importable."""
                % base_path,
                mnemonic="compiled-package-hidden-by-package",
            )

    general.info("Successfully created '%s'." % getReportPath(final_filename))

    writeCompilationReports(aborted=False)

    run_filename = OutputDirectories.getResultRunFilename(
        onefile=Options.isOnefileMode()
    )

    # Execute the module immediately if option was given.
    if Options.shallExecuteImmediately():
        general.info("Launching '%s'." % run_filename)

        if Options.shallMakeModule():
            _executeModule(tree=main_module)
        else:
            _executeMain(run_filename)
    else:
        if run_filename != final_filename:
            general.info(
                "Execute it by launching '%s', the batch file needs to set environment."
                % run_filename
            )


def main():
    try:
        _main()
    except BaseException:
        try:
            writeCompilationReports(aborted=True)
        except KeyboardInterrupt:
            general.warning("""Report writing was prevented by user interrupt.""")
        except BaseException as e:  # Catch all the things, pylint: disable=broad-except
            general.warning(
                """\
Report writing was prevented by exception %r, use option \
'--experimental=debug-report-traceback' for full traceback."""
                % e
            )

            if isExperimental("debug-report-traceback"):
                raise

        raise


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
