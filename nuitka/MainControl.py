#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""This is the main actions of Nuitka.

This can do all the steps to translate one module to a target language using
the Python C/API, to compile it to either an executable or an extension
module, potentially with bytecode included and used library copied into
a distribution folder.

"""

import os
import sys

from nuitka.build.DataComposerInterface import runDataComposer
from nuitka.build.SconsInterface import provideStaticSourceFilesBackend
from nuitka.build.SconsUtils import (
    getSconsReportValue,
    readSconsErrorReport,
    readSconsReport,
)
from nuitka.code_generation.CodeGeneration import (
    generateHelpersCode,
    generateModuleCode,
)
from nuitka.code_generation.ConstantCodes import (
    addDistributionMetadataValue,
    getDistributionMetadataValues,
)
from nuitka.freezer.IncludedDataFiles import (
    addIncludedDataFilesFromFileOptions,
    addIncludedDataFilesFromFlavor,
    addIncludedDataFilesFromPackageOptions,
    addIncludedDataFilesFromPlugins,
    copyDataFiles,
)
from nuitka.freezer.IncludedEntryPoints import (
    addExtensionModuleEntryPoint,
    addIncludedEntryPoints,
    addMainEntryPoint,
    getStandaloneEntryPoints,
)
from nuitka.freezer.MacOSApp import addIncludedDataFilesFromMacOSAppOptions
from nuitka.freezer.MacOSDmg import createDmgFile
from nuitka.importing.Importing import locateModule, setupImportingFromOptions
from nuitka.importing.Recursion import (
    scanIncludedPackage,
    scanPluginFilenamePattern,
    scanPluginPath,
    scanPluginSinglePath,
)
from nuitka.optimizations.ValueTraces import setupValueTraceFromOptions
from nuitka.options.Options import (
    assumeYesForDownloads,
    getDebuggerName,
    getExperimentalIndications,
    getFileReferenceMode,
    getForcedStderrPath,
    getForcedStdoutPath,
    getMainArgs,
    getMainEntryPointFilenames,
    getMustIncludeModules,
    getMustIncludePackages,
    getOutputDir,
    getPgoArgs,
    getPositionalArgs,
    getPythonPgoInput,
    getShallFollowExtra,
    getShallFollowExtraFilePatterns,
    getShallFollowModules,
    getShallIncludeDistributionMetadata,
    getXMLDumpOutputFilename,
    hasPythonFlagIsolated,
    hasPythonFlagNoAnnotations,
    hasPythonFlagNoAsserts,
    hasPythonFlagNoBytecodeRuntimeCache,
    hasPythonFlagNoCurrentDirectoryInPath,
    hasPythonFlagNoDocStrings,
    hasPythonFlagNoRandomization,
    hasPythonFlagNoSite,
    hasPythonFlagNoWarnings,
    hasPythonFlagTraceImports,
    hasPythonFlagUnbuffered,
    isCompileTimeProfile,
    isCPgoMode,
    isExperimental,
    isLowMemory,
    isMultidistMode,
    isOnefileMode,
    isRemoveBuildDir,
    isRuntimeProfile,
    isShowInclusion,
    isShowMemory,
    isShowProgress,
    isStandaloneMode,
    shallAskForWindowsAdminRights,
    shallCreateDmgFile,
    shallCreatePythonPgoInput,
    shallCreateScriptFileForExecution,
    shallExecuteImmediately,
    shallMakeModule,
    shallMakePackage,
    shallNotDoExecCCompilerCall,
    shallOnlyExecCCompilerCall,
    shallRunInDebugger,
    shallTraceExecution,
    shallTreatUninstalledPython,
    shallUsePythonDebug,
    shallUseStaticLibPython,
)
from nuitka.plugins.Hooks import (
    considerExtraDlls,
    getBuildDefinitions,
    onBeforeCodeParsing,
    onCompilationStartChecks,
    onFinalResult,
    onGeneratedSourceCode,
    onModuleCompleteSet,
    onModuleInitialSet,
    onStandaloneDistributionFinished,
    writeExtraCodeFiles,
)
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
    isMonolithPy,
    isPyenvPython,
)
from nuitka.PythonVersions import (
    getModuleLinkerLibs,
    getPythonABI,
    getSupportedPythonVersions,
    isPythonWithGil,
    python_version,
    python_version_str,
)
from nuitka.Serialization import ConstantAccessor
from nuitka.Tracing import (
    code_generation_logger,
    doNotBreakSpaces,
    general,
    inclusion_logger,
    pgo_logger,
)
from nuitka.tree import SyntaxErrors
from nuitka.tree.ReformulationMultidist import createMultidistMainSourceCode
from nuitka.utils.Distributions import getDistribution, getDistributionName
from nuitka.utils.Execution import (
    callProcess,
    withEnvironmentVarOverridden,
    wrapCommandForDebuggerForExec,
)
from nuitka.utils.FileOperations import (
    changeFilenameExtension,
    deleteFile,
    getExternalUsePath,
    getNormalizedPathJoin,
    getReportPath,
    isFilesystemEncodable,
    openTextFile,
    removeDirectory,
)
from nuitka.utils.Importing import getPackageDirFilename
from nuitka.utils.InstanceCounters import printInstanceCounterStats
from nuitka.utils.MemoryUsage import reportMemoryUsage, showMemoryTrace
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.ReExecute import callExecProcess, reExecuteNuitka
from nuitka.utils.StaticLibraries import getSystemStaticLibPythonPath
from nuitka.utils.Timing import withProfiling
from nuitka.utils.Utils import getArchitecture, isMacOS, isWin32Windows
from nuitka.Version import getCommercialVersion, getNuitkaVersion

from . import ModuleRegistry, OutputDirectories
from .build.SconsInterface import (
    asBoolStr,
    cleanSconsDirectory,
    getCommonSconsOptions,
    runScons,
)
from .code_generation import LoaderCodes, Reports
from .finalizations import Finalization
from .freezer.Onefile import getCompressorPython, packDistFolderToOnefile
from .freezer.Standalone import (
    checkFreezingModuleSet,
    copyDllsUsed,
    detectUsedDLLs,
    signDistributionMacOS,
)
from .optimizations.Optimization import optimizeModules
from .pgo.PGO import readPGOInputFile
from .reports.Reports import writeCompilationReports
from .States import states
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

    onBeforeCodeParsing()

    # First, build the raw node tree from the source code.
    if isMultidistMode():
        assert not shallMakeModule()

        main_module = buildMainModuleTree(
            source_code=createMultidistMainSourceCode(),
        )
    else:
        main_module = buildMainModuleTree(
            source_code=None,
        )

    OutputDirectories.setMainModule(main_module)

    for distribution_name in getShallIncludeDistributionMetadata():
        distribution = getDistribution(distribution_name)

        if distribution is None:
            return general.sysexit(
                "Error, could not find distribution '%s' for which metadata was asked to be included."
                % distribution_name
            )

        real_distribution_name = getDistributionName(distribution)

        if real_distribution_name != distribution_name:
            general.warning(
                """\
Warning, the distribution specified as '--include-distribution-metadata=%s' is really named '%s', \
use the correct name instead."""
                % (distribution_name, real_distribution_name)
            )

        addDistributionMetadataValue(
            distribution_name=real_distribution_name,
            distribution=distribution,
            reason="user requested",
        )

    # First remove old object files and old generated files, old binary or
    # module, and standalone mode program directory if any, they can only do
    # harm.
    source_dir = OutputDirectories.getSourceDirectoryPath(onefile=False, create=True)

    if not shallOnlyExecCCompilerCall():
        cleanSconsDirectory(source_dir)

        # Prepare the ".dist" directory, throwing away what was there before.
        if isStandaloneMode():
            OutputDirectories.initStandaloneDirectory(logger=general)

    # Delete result file, to avoid confusion with previous build and to
    # avoid locking issues after the build.
    deleteFile(
        path=OutputDirectories.getResultFullpath(onefile=False, real=True),
        must_exist=False,
    )
    if isOnefileMode():
        deleteFile(
            path=OutputDirectories.getResultFullpath(onefile=True, real=True),
            must_exist=False,
        )

        # Also make sure we inform the user in case the compression is not possible.
        getCompressorPython()

    # Second, do it for the directories given.
    for plugin_filename in getShallFollowExtra():
        scanPluginPath(plugin_filename=plugin_filename, module_package=None)

    for pattern in getShallFollowExtraFilePatterns():
        scanPluginFilenamePattern(pattern=pattern)

    # For packages, include the full suite.
    if shallMakePackage():
        scanIncludedPackage(main_module.getFullName())

    for package_name in getMustIncludePackages():
        scanIncludedPackage(package_name)

    for module_name in getMustIncludeModules():
        module_name, module_filename, module_kind, finding = locateModule(
            module_name=ModuleName(module_name),
            parent_package=None,
            level=0,
        )

        if finding != "absolute":
            return inclusion_logger.sysexit(
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
    onModuleInitialSet()

    # Then optimize the tree and potentially recursed modules.
    # TODO: The passed filename is really something that should come from
    # a command line option, it's a filename for the graph, which might not
    # need a default at all.
    optimizeModules(main_module.getOutputFilename())

    # Freezer may have concerns for some modules.
    if isStandaloneMode():
        checkFreezingModuleSet()

    # Check if distribution meta data is included, that cannot be used.
    for distribution_name, meta_data_value in getDistributionMetadataValues():
        if not ModuleRegistry.hasDoneModule(meta_data_value.module_name):
            return inclusion_logger.sysexit(
                "Error, including metadata for distribution '%s' without including related package '%s'."
                % (distribution_name, meta_data_value.module_name)
            )

    # Allow plugins to comment on final module set.
    onModuleCompleteSet()

    if isExperimental("check_xml_persistence"):
        for module in ModuleRegistry.getRootModules():
            if module.isMainModule():
                return module

        assert False
    else:
        # Main module might change behind our back, look it up again.
        return main_module


def dumpTreeXML():
    filename = getXMLDumpOutputFilename()

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
        nice_filename = getNormalizedPathJoin(
            source_dir, "module." + module.getFullName()
        )

        # Note: Could detect if the file system is cases sensitive in source_dir
        # or not, but that's probably not worth the effort. False positives do
        # no harm at all. We cannot use normcase, as macOS is not using one that
        # will tell us the truth.
        collision_filename = getNormalizedPathJoin(
            source_dir, "module." + module.getFullName().asString().lower()
        )

        # When the filename becomes to long to add ".const", we use a hash name
        # instead.
        hash_filename = getNormalizedPathJoin(
            source_dir,
            "module.hashed_" + module.getFullName().asLegalFilename(name_limit=1),
        )

        return nice_filename, collision_filename, hash_filename

    colliding_filenames = set()

    # First pass, check for collisions.
    for module in modules:
        if module.isPythonExtensionModule():
            continue

        _nice_filename, collision_filename, _hash_filename = _getModuleFilenames(module)

        if collision_filename in colliding_filenames:
            collision_filenames.add(collision_filename)

        colliding_filenames.add(collision_filename)

    # Our output.
    module_filenames = {}

    # Second pass, handle collisions and encoding issues for filenames.
    for module in modules:
        if module.isPythonExtensionModule():
            continue

        nice_filename, collision_filename, hash_filename = _getModuleFilenames(module)

        base_filename = os.path.basename(nice_filename)

        # Allow for longer suffixes that .c, we use .const and might use others
        # as well in the C compiler and make sure we use only file system
        # encodable names.
        if (
            collision_filename in collision_filenames
            or len(base_filename) > 240
            or not isFilesystemEncodable(base_filename)
        ):
            nice_filename = hash_filename

        module_filenames[module] = nice_filename + ".c"

    return module_filenames


def makeSourceDirectory():
    """Get the full list of modules imported, create code for all of them."""
    # We deal with a lot of details here, but rather one by one, and split makes
    # no sense, pylint: disable=too-many-branches

    # assert main_module in ModuleRegistry.getDoneModules()

    # Lets check if the asked modules are actually present, and warn the
    # user if one of those was not found.
    for any_case_module in getShallFollowModules():
        if "*" in any_case_module or "{" in any_case_module:
            continue

        if not ModuleRegistry.hasDoneModule(
            any_case_module
        ) and not ModuleRegistry.hasRootModule(any_case_module):
            general.warning(
                "Did not follow import to unused '%s', consider include "
                % any_case_module
            )

    # Prepare code generation, i.e. execute finalization for it.
    for current_module in ModuleRegistry.getDoneModules():
        if current_module.isCompiledPythonModule():
            Finalization.prepareCodeGeneration(current_module)

    # Do some reporting and determine compiled module to work on
    compiled_modules = []

    for current_module in ModuleRegistry.getDoneModules():
        if current_module.isCompiledPythonModule():
            compiled_modules.append(current_module)

            if isShowInclusion():
                inclusion_logger.info(
                    "Included compiled module '%s'." % current_module.getFullName()
                )
        elif current_module.isPythonExtensionModule():
            if isShowInclusion():
                inclusion_logger.info(
                    "Included extension module '%s'." % current_module.getFullName()
                )
        elif current_module.isUncompiledPythonModule():
            if isShowInclusion():
                inclusion_logger.info(
                    "Included uncompiled module '%s'." % current_module.getFullName()
                )
        else:
            assert False, current_module

    # Pick filenames.
    source_dir = OutputDirectories.getSourceDirectoryPath(onefile=False, create=False)

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
    for current_module in compiled_modules:
        module_name = current_module.getFullName()
        c_filename = module_filenames[current_module]

        reportProgressBar(
            item=module_name,
        )

        source_code = generateModuleCode(
            module=current_module,
            data_filename=changeFilenameExtension(
                os.path.basename(c_filename), ".const"
            ),
        )

        writeSourceCode(
            filename=c_filename,
            source_code=source_code,
            logger=code_generation_logger,
            assume_yes_for_downloads=assumeYesForDownloads(),
        )

    closeProgressBar()

    (
        helper_decl_code,
        helper_impl_code,
        constants_header_code,
        constants_body_code,
    ) = generateHelpersCode()

    writeSourceCode(
        filename=getNormalizedPathJoin(source_dir, "__helpers.h"),
        source_code=helper_decl_code,
        logger=code_generation_logger,
        assume_yes_for_downloads=assumeYesForDownloads(),
    )

    writeSourceCode(
        filename=getNormalizedPathJoin(source_dir, "__helpers.c"),
        source_code=helper_impl_code,
        logger=code_generation_logger,
        assume_yes_for_downloads=assumeYesForDownloads(),
    )

    writeSourceCode(
        filename=getNormalizedPathJoin(source_dir, "__constants.h"),
        source_code=constants_header_code,
        logger=code_generation_logger,
        assume_yes_for_downloads=assumeYesForDownloads(),
    )

    writeSourceCode(
        filename=getNormalizedPathJoin(source_dir, "__constants.c"),
        source_code=constants_body_code,
        logger=code_generation_logger,
        assume_yes_for_downloads=assumeYesForDownloads(),
    )


def _runPgoBinary():
    pgo_executable = OutputDirectories.getPgoRunExecutable()

    if not os.path.isfile(pgo_executable):
        return general.sysexit(
            "Error, failed to produce PGO binary '%s'" % pgo_executable
        )

    return callProcess(
        [getExternalUsePath(pgo_executable)] + getPgoArgs(),
        shell=False,
    )


def _wasMsvcMode():
    if not isWin32Windows():
        return False

    return (
        getSconsReportValue(
            source_dir=OutputDirectories.getSourceDirectoryPath(
                onefile=False, create=False
            ),
            key="msvc_mode",
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
                source_dir=OutputDirectories.getSourceDirectoryPath(
                    onefile=False, create=False
                ),
                key="PATH",
            ),
        ):
            exit_code_pgo = _runPgoBinary()

        pgo_data_collected = os.path.exists(msvc_pgc_filename)
    else:
        exit_code_pgo = _runPgoBinary()

        # gcc file suffix, spell-checker: ignore gcda
        gcc_constants_pgo_filename = getNormalizedPathJoin(
            OutputDirectories.getSourceDirectoryPath(onefile=False, create=False),
            "__constants.gcda",
        )

        pgo_data_collected = os.path.exists(gcc_constants_pgo_filename)

    if exit_code_pgo != 0:
        pgo_logger.warning(
            """\
Error, the C PGO compiled program error exited. Make sure it works \
fully before using '--pgo-c' option."""
        )

    if not pgo_data_collected:
        return pgo_logger.sysexit(
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
        return general.sysexit(
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

    scons_options["source_dir"] = OutputDirectories.getSourceDirectoryPath(
        onefile=False, create=False
    )
    scons_options["monolithpy"] = asBoolStr(isMonolithPy())
    scons_options["debug_mode"] = asBoolStr(states.is_debug)
    scons_options["debugger_mode"] = asBoolStr(shallRunInDebugger())
    scons_options["python_debug"] = asBoolStr(shallUsePythonDebug())
    scons_options["full_compat"] = asBoolStr(states.is_full_compat)
    scons_options["experimental"] = ",".join(getExperimentalIndications())
    scons_options["trace_mode"] = asBoolStr(shallTraceExecution())
    scons_options["file_reference_mode"] = getFileReferenceMode()
    scons_options["compiled_module_count"] = "%d" % len(
        ModuleRegistry.getCompiledModules()
    )

    if isLowMemory():
        scons_options["low_memory"] = asBoolStr(True)

    scons_options["result_exe"] = OutputDirectories.getResultFullpath(
        onefile=False, real=False
    )

    if not shallMakeModule():
        main_module = ModuleRegistry.getRootTopModule()
        assert main_module.isMainModule()

        main_module_name = main_module.getFullName()
        if main_module_name != "__main__":
            scons_options["main_module_name"] = main_module_name

    if shallUseStaticLibPython():
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

    if getForcedStdoutPath():
        scons_options["forced_stdout_path"] = getForcedStdoutPath()

    if getForcedStderrPath():
        scons_options["forced_stderr_path"] = getForcedStderrPath()

    if isRuntimeProfile():
        scons_options["profile_mode"] = asBoolStr(True)

    if shallTreatUninstalledPython():
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

    if int(os.getenv("NUITKA_NOSITE_FLAG", hasPythonFlagNoSite())):
        scons_options["python_sysflag_no_site"] = asBoolStr(True)

    if hasPythonFlagTraceImports():
        scons_options["python_sysflag_verbose"] = asBoolStr(True)

    if hasPythonFlagNoRandomization():
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
    env_values.update(getBuildDefinitions())

    if shallCreatePythonPgoInput():
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
    if isCPgoMode():
        # For C level PGO, we have a 2 pass system. TODO: Make it more global for onefile
        # and standalone mode proper support, which might need data files to be
        # there, which currently are not yet there, so it won't run.
        if isCPgoMode():
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
            os.environ["PYTHONPATH"] += ":" + getOutputDir()
        else:
            os.environ["PYTHONPATH"] = getOutputDir()

    # Add the main arguments, previous separated.
    args += getPositionalArgs()[1:] + getMainArgs()

    callExecProcess(args, uac=uac)


def _executeMain(binary_filename):
    # Wrap in debugger, unless the CMD file contains that call already.
    if shallRunInDebugger() and not shallCreateScriptFileForExecution():
        args = wrapCommandForDebuggerForExec(
            command=(binary_filename,),
            debugger=getDebuggerName(),
        )
    else:
        args = (binary_filename, binary_filename)

    callExecPython(
        args=args,
        add_path=False,
        uac=isWin32Windows() and shallAskForWindowsAdminRights(),
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

    output_dir = os.path.normpath(getOutputDir())
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
                os.path.normpath(
                    OutputDirectories.getResultFullpath(onefile=False, real=True)
                )
            )
        ),
        "output_dir": output_dir,
    }

    if shallRunInDebugger():
        args = wrapCommandForDebuggerForExec(
            command=(sys.executable, "-c", python_command),
            debugger=getDebuggerName(),
        )
    else:
        args = (sys.executable, "python", "-c", python_command)

    callExecPython(args=args, add_path=True, uac=False)


def compileTree():
    source_dir = OutputDirectories.getSourceDirectoryPath(onefile=False, create=False)

    general.info("Completed Python level compilation and optimization.")

    if not shallOnlyExecCCompilerCall():
        general.info("Generating source code for C backend compiler.")

        reportMemoryUsage(
            "before_c_code_generation",
            (
                "Total memory usage before generating C code"
                if isShowProgress() or isShowMemory()
                else None
            ),
        )

        # Now build the target language code for the whole tree.
        with withProfiling(
            name="code-generation",
            logger=code_generation_logger,
            enabled=isCompileTimeProfile(),
        ):
            makeSourceDirectory()

        bytecode_accessor = ConstantAccessor(
            data_filename="__bytecode.const", top_level_name="bytecode_data"
        )

        # This should take all bytecode values, even ones needed for frozen or
        # not produce anything.
        loader_code = LoaderCodes.getMetaPathLoaderBodyCode(bytecode_accessor)

        writeSourceCode(
            filename=getNormalizedPathJoin(source_dir, "__loader.c"),
            source_code=loader_code,
            logger=code_generation_logger,
            assume_yes_for_downloads=assumeYesForDownloads(),
        )

    else:
        source_dir = OutputDirectories.getSourceDirectoryPath(
            onefile=False, create=False
        )

        if not os.path.isfile(os.path.join(source_dir, "__helpers.h")):
            general.sysexit("Error, no previous build directory exists.")

    reportMemoryUsage(
        "before_running_scons",
        (
            "Total memory usage before running scons"
            if isShowProgress() or isShowMemory()
            else None
        ),
    )

    if isShowMemory():
        printInstanceCounterStats()

    Reports.doMissingOptimizationReport()

    if shallNotDoExecCCompilerCall():
        return True, {}

    general.info("Running data composer tool for optimal constant value handling.")

    runDataComposer(source_dir)  # TODO: This should be a hook too

    writeExtraCodeFiles(onefile=False)

    provideStaticSourceFilesBackend(source_dir=source_dir)

    onGeneratedSourceCode(source_dir, onefile=False)

    general.info("Running C compilation via Scons.")

    # Run the Scons to build things.
    result, scons_options = runSconsBackend()

    return result, scons_options


def handleSyntaxError(e):
    # Syntax or indentation errors, output them to the user and abort. If
    # we are not in full compat, and user has not specified the Python
    # versions he wants, tell him about the potential version problem.
    error_message = SyntaxErrors.formatOutput(e)

    if not states.is_full_compat:
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


def _considerPgoInput():
    pgo_filename = getPythonPgoInput()
    if pgo_filename is not None:
        readPGOInputFile(pgo_filename)


def _detectEarlyDLLs():
    assert isStandaloneMode()
    modules = ModuleRegistry.getDoneModules()

    for module in modules:
        if module.isPythonExtensionModule():
            addExtensionModuleEntryPoint(module)

        addIncludedEntryPoints(considerExtraDlls(module))

    detectUsedDLLs(
        standalone_entry_points=getStandaloneEntryPoints(),
        source_dir=OutputDirectories.getSourceDirectoryPath(
            onefile=False, create=False
        ),
    )


def _detectLateDLLs(scons_options):
    assert isStandaloneMode()
    binary_filename = scons_options["result_exe"]

    detectUsedDLLs(
        standalone_entry_points=(addMainEntryPoint(binary_filename),),
        source_dir=OutputDirectories.getSourceDirectoryPath(
            onefile=False, create=False
        ),
    )


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

    general.info(
        leader="Starting Python compilation with:",
        message="%s %s %s."
        % doNotBreakSpaces(
            "Version '%s'" % getNuitkaVersion(),
            "on Python %s (flavor '%s'%s)"
            % (
                python_version_str,
                getPythonFlavorName(),
                ("" if isPythonWithGil() else " no GIL"),
            ),
            "commercial grade '%s'" % (getCommercialVersion() or "not installed"),
        ),
    )

    # In case we are in a PGO run, we read its information first, so it becomes
    # available for later parts.
    _considerPgoInput()

    reportMemoryUsage(
        "after_launch",
        (
            "Total memory usage before processing"
            if isShowProgress() or isShowMemory()
            else None
        ),
    )

    # Initialize the importing layer from options, main filenames, debugging
    # options, etc.
    setupImportingFromOptions()

    # Initialize value tracing if requested.
    setupValueTraceFromOptions()

    # Let the plugins know we are starting compilation and they should make their checks.
    onCompilationStartChecks()

    addIncludedDataFilesFromFlavor()
    addIncludedDataFilesFromFileOptions()
    addIncludedDataFilesFromPackageOptions()

    # Turn that source code into a node tree structure.
    try:
        main_module = _createMainModule()
    except (SyntaxError, IndentationError) as e:
        return handleSyntaxError(e)

    addIncludedDataFilesFromMacOSAppOptions()
    addIncludedDataFilesFromPlugins()

    dumpTreeXML()

    # Detect DLLs used so far.
    if isStandaloneMode():
        _detectEarlyDLLs()

    # Make the actual C compilation.
    result, scons_options = compileTree()

    # Exit if compilation failed.
    if not result:
        general.sysexit(
            message="Failed unexpectedly in Scons C backend compilation.",
            mnemonic="scons-backend-failure",
            reporting=True,
        )

    # Relaunch in case of Python PGO input to be produced.
    if shallCreatePythonPgoInput():
        # Will not return.
        pgo_filename = OutputDirectories.getPgoRunInputFilename()
        general.info(
            "Restarting compilation using collected information from '%s'."
            % pgo_filename
        )
        reExecuteNuitka(pgo_filename=pgo_filename)

    if shallNotDoExecCCompilerCall():
        if isShowMemory():
            showMemoryTrace()

        sys.exit(0)

    executePostProcessing(scons_options["result_exe"])

    if isStandaloneMode():
        _detectLateDLLs(scons_options)

        dist_dir = OutputDirectories.getStandaloneDirectoryPath(bundle=True, real=False)

        if not shallOnlyExecCCompilerCall():
            main_standalone_entry_point, copy_standalone_entry_points = copyDllsUsed(
                dist_dir=dist_dir,
                standalone_entry_points=getStandaloneEntryPoints(),
            )

            data_file_paths = copyDataFiles(
                standalone_entry_points=getStandaloneEntryPoints()
            )

            if isMacOS():
                signDistributionMacOS(
                    dist_dir=dist_dir,
                    data_file_paths=data_file_paths,
                    main_standalone_entry_point=main_standalone_entry_point,
                    copy_standalone_entry_points=copy_standalone_entry_points,
                )

            dist_dir = OutputDirectories.renameStandaloneDirectory(dist_dir)

        onStandaloneDistributionFinished(
            dist_dir=dist_dir,
            standalone_binary=OutputDirectories.getResultFullpath(
                onefile=False, real=True
            ),
        )

        if isOnefileMode():
            packDistFolderToOnefile(dist_dir)

            if isRemoveBuildDir():
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
    source_dir = OutputDirectories.getSourceDirectoryPath(onefile=False, create=False)

    if isRemoveBuildDir():
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
        onefile=isOnefileMode(), real=True
    )

    if isStandaloneMode() and isMacOS():
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
                    getMainEntryPointFilenames()[0],
                ),
                mnemonic="macos-cross-compile",
            )

    onFinalResult(final_filename)

    if shallMakeModule():
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

    # Archive creations, installer creations go here.
    if shallCreateDmgFile():
        createDmgFile(general)

    writeCompilationReports(aborted=False)

    run_filename = OutputDirectories.getResultRunFilename(onefile=isOnefileMode())

    # Execute the module immediately if option was given.
    if shallExecuteImmediately():
        general.info("Launching '%s'." % run_filename)

        if shallMakeModule():
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
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
