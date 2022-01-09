#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" This is the main actions of Nuitka.

This can do all the steps to translate one module to a target language using
the Python C/API, to compile it to either an executable or an extension
module, potentially with bytecode included and used library copied into
a distribution folder.

"""

import os
import sys

from nuitka.build.DataComposerInterface import runDataComposer
from nuitka.build.SconsUtils import getSconsReportValue
from nuitka.constants.Serialization import ConstantAccessor
from nuitka.freezer.IncludedEntryPoints import (
    addIncludedEntryPoints,
    addShlibEntryPoint,
    getStandaloneEntryPoints,
    setMainEntryPoint,
)
from nuitka.freezer.Standalone import copyDataFiles
from nuitka.importing import Importing, Recursion
from nuitka.Options import (
    getPythonPgoInput,
    hasPythonFlagNoAsserts,
    hasPythonFlagNoWarnings,
)
from nuitka.plugins.Plugins import Plugins
from nuitka.PostProcessing import executePostProcessing
from nuitka.Progress import (
    closeProgressBar,
    reportProgressBar,
    setupProgressBar,
)
from nuitka.PythonFlavors import (
    isAnacondaPython,
    isApplePython,
    isDebianPackagePython,
    isMSYS2MingwPython,
    isNuitkaPython,
    isPyenvPython,
)
from nuitka.PythonVersions import (
    getPythonABI,
    getSupportedPythonVersions,
    getSystemPrefixPath,
    python_version,
    python_version_str,
)
from nuitka.Tracing import general, inclusion_logger
from nuitka.tree import SyntaxErrors
from nuitka.utils import InstanceCounters, MemoryUsage
from nuitka.utils.Execution import (
    callProcess,
    withEnvironmentVarOverriden,
    wrapCommandForDebuggerForExec,
)
from nuitka.utils.FileOperations import (
    deleteFile,
    getDirectoryRealPath,
    getExternalUsePath,
    makePath,
    putTextFileContents,
    removeDirectory,
)
from nuitka.utils.Importing import getSharedLibrarySuffix
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.ReExecute import callExecProcess, reExecuteNuitka
from nuitka.utils.StaticLibraries import getSystemStaticLibPythonPath
from nuitka.utils.Utils import getArchitecture, getOS, isWin32Windows
from nuitka.Version import getCommercialVersion, getNuitkaVersion

from . import ModuleRegistry, Options, OutputDirectories, TreeXML
from .build import SconsInterface
from .codegen import CodeGeneration, LoaderCodes, Reports
from .finalizations import Finalization
from .freezer.Onefile import packDistFolderToOnefile
from .freezer.Standalone import copyUsedDLLs
from .optimizations.Optimization import optimizeModules
from .pgo.PGO import readPGOInputFile
from .Reports import writeCompilationReport
from .tree import Building


def _createNodeTree(filename):
    """Create a node tree.

    Turn that source code into a node tree structure. If recursion into
    imported modules is available, more trees will be available during
    optimization, or immediately through recursed directory paths.

    """

    # Many cases to deal with, pylint: disable=too-many-branches

    # First, build the raw node tree from the source code.
    main_module = Building.buildMainModuleTree(
        filename=filename,
        is_main=not Options.shallMakeModule(),
    )

    # First remove old object files and old generated files, old binary or
    # module, and standalone mode program directory if any, they can only do
    # harm.
    source_dir = OutputDirectories.getSourceDirectoryPath()

    if not Options.shallOnlyExecCCompilerCall():
        SconsInterface.cleanSconsDirectory(source_dir)

    # Prepare the ".dist" directory, throwing away what was there before.
    if Options.isStandaloneMode():
        standalone_dir = OutputDirectories.getStandaloneDirectoryPath()
        removeDirectory(path=standalone_dir, ignore_errors=True)
        makePath(standalone_dir)

    # Delete result file, to avoid confusion with previous build and to
    # avoid locking issues after the build.
    deleteFile(
        path=OutputDirectories.getResultFullpath(onefile=False), must_exist=False
    )
    if Options.isOnefileMode():
        deleteFile(
            path=OutputDirectories.getResultFullpath(onefile=True), must_exist=False
        )

    # Second, do it for the directories given.
    for plugin_filename in Options.getShallFollowExtra():
        Recursion.checkPluginPath(plugin_filename=plugin_filename, module_package=None)

    for pattern in Options.getShallFollowExtraFilePatterns():
        Recursion.checkPluginFilenamePattern(pattern=pattern)

    for package_name in Options.getMustIncludePackages():
        package_name, package_directory, kind = Importing.locateModule(
            module_name=ModuleName(package_name),
            parent_package=None,
            level=0,
        )

        if kind != "absolute":
            inclusion_logger.sysexit(
                "Error, failed to locate package %r you asked to include."
                % package_name.asString()
            )

        Recursion.checkPluginPath(
            plugin_filename=package_directory,
            module_package=package_name.getPackageName(),
        )

    for module_name in Options.getMustIncludeModules():
        module_name, module_filename, kind = Importing.locateModule(
            module_name=ModuleName(module_name),
            parent_package=None,
            level=0,
        )

        if kind != "absolute":
            inclusion_logger.sysexit(
                "Error, failed to locate module '%s' you asked to include."
                % module_name.asString()
            )

        Recursion.checkPluginSinglePath(
            plugin_filename=module_filename, module_package=module_name.getPackageName()
        )

    # Allow plugins to add more modules based on the initial set being complete.
    Plugins.onModuleInitialSet()

    # Then optimize the tree and potentially recursed modules.
    optimizeModules(main_module.getOutputFilename())

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


def dumpTreeXML(tree):
    xml_root = tree.asXml()
    TreeXML.dump(xml_root)


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
        if module.isPythonShlibModule():
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
        if module.isPythonShlibModule():
            continue

        base_filename, collision_filename = _getModuleFilenames(module)

        if collision_filename in collision_filenames:
            collision_counts[collision_filename] = (
                collision_counts.get(collision_filename, 0) + 1
            )
            base_filename += "@%d" % collision_counts[collision_filename]

        module_filenames[module] = base_filename + ".c"

    return module_filenames


standalone_entry_points = []


def makeSourceDirectory():
    """Get the full list of modules imported, create code for all of them."""
    # We deal with a lot of details here, but rather one by one, and split makes
    # no sense, pylint: disable=too-many-branches

    # assert main_module in ModuleRegistry.getDoneModules()

    # We might have chosen to include it as bytecode, and only compiled it for
    # fun, and to find its imports. In this case, now we just can drop it. Or
    # a module may shadow a frozen module, but be a different one, then we can
    # drop the frozen one.
    # TODO: This really should be done when the compiled module comes into
    # existence.
    for module in ModuleRegistry.getDoneModules():
        if module.isCompiledPythonModule():
            uncompiled_module = ModuleRegistry.getUncompiledModule(
                module_name=module.getFullName(),
                module_filename=module.getCompileTimeFilename(),
            )

            if uncompiled_module is not None:
                # We now need to decide which one to keep, compiled or uncompiled
                # module. Some uncompiled modules may have been asked by the user
                # or technically required. By default, frozen code if it exists
                # is preferred, as it will be from standalone mode adding it.
                if (
                    uncompiled_module.isUserProvided()
                    or uncompiled_module.isTechnical()
                ):
                    ModuleRegistry.removeDoneModule(module)
                else:
                    ModuleRegistry.removeUncompiledModule(uncompiled_module)

    # Lets check if the asked modules are actually present, and warn the
    # user if one of those was not found.
    for any_case_module in Options.getShallFollowModules():
        if "*" in any_case_module or "{" in any_case_module:
            continue

        for module in ModuleRegistry.getDoneModules():
            if module.getFullName() == any_case_module:
                break
        else:
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
        elif module.isPythonShlibModule():
            addShlibEntryPoint(module)

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
            data_filename=os.path.basename(c_filename + "onst"),  # Really .const
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

    msvc_pgc_filename = OutputDirectories.getResultBasepath(onefile=False) + "!1.pgc"
    deleteFile(msvc_pgc_filename, must_exist=False)

    if pgo_mode == "use":
        msvc_pgd_filename = OutputDirectories.getResultBasepath(onefile=False) + ".pgd"
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

        with withEnvironmentVarOverriden(
            "PATH",
            getSconsReportValue(
                source_dir=OutputDirectories.getSourceDirectoryPath(), key="PATH"
            ),
        ):
            _exit_code = _runPgoBinary()

        pgo_data_collected = os.path.exists(msvc_pgc_filename)
    else:
        _exit_code = _runPgoBinary()

        gcc_constants_pgo_filename = os.path.join(
            OutputDirectories.getSourceDirectoryPath(), "__constants.gcda"
        )

        pgo_data_collected = os.path.exists(gcc_constants_pgo_filename)

    if not pgo_data_collected:
        general.sysexit(
            "Error, no PGO information produced, did the created binary run at all?"
        )

    general.info("Successfully collected C level PGO information.", style="blue")


def _runPythonPgoBinary():
    # Note: For exit codes, we do not insist on anything yet, maybe we could point it out
    # or ask people to make scripts that buffer these kinds of errors, and take an error
    # instead as a serious failure.

    pgo_filename = OutputDirectories.getPgoRunInputFilename()

    with withEnvironmentVarOverriden("NUITKA_PGO_OUTPUT", pgo_filename):
        _exit_code = _runPgoBinary()

    if not os.path.exists(pgo_filename):
        general.sysexit(
            "Error, no Python PGO information produced, did the created binary run at all?"
        )

    return pgo_filename


def runSconsBackend(quiet):
    # Scons gets transported many details, that we express as variables, and
    # have checks for them, leading to many branches and statements,
    # pylint: disable=too-many-branches,too-many-statements

    asBoolStr = SconsInterface.asBoolStr

    options = {
        "result_name": OutputDirectories.getResultBasepath(onefile=False),
        "source_dir": OutputDirectories.getSourceDirectoryPath(),
        "nuitka_python": asBoolStr(isNuitkaPython()),
        "debug_mode": asBoolStr(Options.is_debug),
        "python_debug": asBoolStr(Options.isPythonDebug()),
        "unstripped_mode": asBoolStr(Options.isUnstripped()),
        "module_mode": asBoolStr(Options.shallMakeModule()),
        "full_compat": asBoolStr(Options.is_fullcompat),
        "experimental": ",".join(Options.getExperimentalIndications()),
        "trace_mode": asBoolStr(Options.shallTraceExecution()),
        "python_version": python_version_str,
        "target_arch": getArchitecture(),
        "python_prefix": getDirectoryRealPath(getSystemPrefixPath()),
        "nuitka_src": SconsInterface.getSconsDataPath(),
        "module_count": "%d"
        % (
            1
            + len(ModuleRegistry.getDoneModules())
            + len(ModuleRegistry.getUncompiledNonTechnicalModules())
        ),
    }

    if Options.isLowMemory():
        options["low_memory"] = asBoolStr(True)

    if not Options.shallMakeModule():
        options["result_exe"] = OutputDirectories.getResultFullpath(onefile=False)

        main_module = ModuleRegistry.getRootTopModule()
        assert main_module.isMainModule()

        main_module_name = main_module.getFullName()
        if main_module_name != "__main__":
            options["main_module_name"] = main_module_name

    if Options.shallUseStaticLibPython():
        options["static_libpython"] = getSystemStaticLibPythonPath()

    if isDebianPackagePython():
        options["debian_python"] = asBoolStr(True)

    if isMSYS2MingwPython():
        options["msys2_mingw_python"] = asBoolStr(True)

    if isAnacondaPython():
        options["anaconda_python"] = asBoolStr(True)

    if isApplePython():
        options["apple_python"] = asBoolStr(True)

    if isPyenvPython():
        options["pyenv_python"] = asBoolStr(True)

    if Options.isStandaloneMode():
        options["standalone_mode"] = asBoolStr(True)

    if Options.isOnefileMode():
        options["onefile_mode"] = asBoolStr(True)

        if Options.isOnefileTempDirMode():
            options["onefile_temp_mode"] = asBoolStr(True)

    if Options.getForcedStdoutPath():
        options["forced_stdout_path"] = Options.getForcedStdoutPath()

    if Options.getForcedStderrPath():
        options["forced_stderr_path"] = Options.getForcedStderrPath()

    if Options.shallTreatUninstalledPython():
        options["uninstalled_python"] = asBoolStr(True)

    if ModuleRegistry.getUncompiledTechnicalModules():
        options["frozen_modules"] = str(
            len(ModuleRegistry.getUncompiledTechnicalModules())
        )

    if getOS() == "Windows":
        options["noelf_mode"] = asBoolStr(True)

    if Options.isProfile():
        options["profile_mode"] = asBoolStr(True)

    if hasPythonFlagNoWarnings():
        options["no_python_warnings"] = asBoolStr(True)

    if hasPythonFlagNoAsserts():
        options["python_sysflag_optimize"] = asBoolStr(True)

    if python_version < 0x300 and sys.flags.py3k_warning:
        options["python_sysflag_py3k_warning"] = asBoolStr(True)

    if python_version < 0x300 and (
        sys.flags.division_warning or sys.flags.py3k_warning
    ):
        options["python_sysflag_division_warning"] = asBoolStr(True)

    if sys.flags.bytes_warning:
        options["python_sysflag_bytes_warning"] = asBoolStr(True)

    if int(os.environ.get("NUITKA_NOSITE_FLAG", Options.hasPythonFlagNoSite())):
        options["python_sysflag_no_site"] = asBoolStr(True)

    if Options.hasPythonFlagTraceImports():
        options["python_sysflag_verbose"] = asBoolStr(True)

    if Options.hasPythonFlagNoRandomization():
        options["python_sysflag_no_randomization"] = asBoolStr(True)

    if python_version < 0x300 and sys.flags.unicode:
        options["python_sysflag_unicode"] = asBoolStr(True)

    if python_version >= 0x370 and sys.flags.utf8_mode:
        options["python_sysflag_utf8"] = asBoolStr(True)

    abiflags = getPythonABI()
    if abiflags:
        options["abiflags"] = abiflags

    if Options.shallMakeModule():
        options["module_suffix"] = getSharedLibrarySuffix(preferred=True)

    SconsInterface.setCommonOptions(options)

    if Options.shallCreatePgoInput():
        options["pgo_mode"] = "python"

        result = SconsInterface.runScons(
            options=options, quiet=quiet, scons_filename="Backend.scons"
        )
        if not result:
            return result, options

        # Need to make it usable before executing it.
        executePostProcessing()
        _runPythonPgoBinary()

        return True, options

        # Need to restart compilation from scratch here.
    if Options.isPgoMode():
        # For C level PGO, we have a 2 pass system. TODO: Make it more global for onefile
        # and standalone mode proper support, which might need data files to be
        # there, which currently are not yet there, so it won't run.
        if Options.isPgoMode():
            options["pgo_mode"] = "generate"
            result = SconsInterface.runScons(
                options=options, quiet=quiet, scons_filename="Backend.scons"
            )

            if not result:
                return result, options

            # Need to make it usable before executing it.
            executePostProcessing()
            _runCPgoBinary()
            options["pgo_mode"] = "use"

    result = (
        SconsInterface.runScons(
            options=options, quiet=quiet, scons_filename="Backend.scons"
        ),
        options,
    )

    if options.get("pgo_mode") == "use" and _wasMsvcMode():
        _deleteMsvcPGOFiles(pgo_mode="use")

    return result


def writeSourceCode(filename, source_code):
    # Prevent accidental overwriting. When this happens the collision detection
    # or something else has failed.
    assert not os.path.isfile(filename), filename

    putTextFileContents(filename=filename, contents=source_code, encoding="latin1")


def writeBinaryData(filename, binary_data):
    # Prevent accidental overwriting. When this happens the collision detection
    # or something else has failed.
    assert not os.path.isfile(filename), filename

    assert type(binary_data) is bytes

    with open(filename, "wb") as output_file:
        output_file.write(binary_data)


def callExecPython(args, clean_path, add_path):
    old_python_path = os.environ.get("PYTHONPATH")

    if clean_path and old_python_path is not None:
        os.environ["PYTHONPATH"] = ""

    if add_path:
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] += ":" + Options.getOutputDir()
        else:
            os.environ["PYTHONPATH"] = Options.getOutputDir()

    # We better flush these, "os.execl" won't do it anymore.
    sys.stdout.flush()
    sys.stderr.flush()

    # Add the main arguments, previous separated.
    args += Options.getPositionalArgs()[1:] + Options.getMainArgs()

    callExecProcess(args)


def executeMain(binary_filename, clean_path):
    if Options.shallRunInDebugger():
        args = wrapCommandForDebuggerForExec(binary_filename)
    else:
        args = (binary_filename, binary_filename)

    callExecPython(clean_path=clean_path, add_path=False, args=args)


def executeModule(tree, clean_path):

    if python_version < 0x340:
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

    python_command_template += ";__import__('%(module_name)s')"

    python_command = python_command_template % {
        "module_name": tree.getName(),
        "expected_filename": os.path.normcase(
            os.path.abspath(
                os.path.normpath(OutputDirectories.getResultFullpath(onefile=False))
            )
        ),
    }

    if Options.shallRunInDebugger():
        args = wrapCommandForDebuggerForExec(sys.executable, "-c", python_command)
    else:
        args = (sys.executable, "python", "-c", python_command)

    callExecPython(clean_path=clean_path, add_path=True, args=args)


def compileTree():
    source_dir = OutputDirectories.getSourceDirectoryPath()

    general.info("Completed Python level compilation and optimization.")

    if not Options.shallOnlyExecCCompilerCall():
        general.info("Generating source code for C backend compiler.")

        if Options.isShowProgress() or Options.isShowMemory():
            general.info(
                "Total memory usage before generating C code: {memory}:".format(
                    memory=MemoryUsage.getHumanReadableProcessMemoryUsage()
                )
            )
        # Now build the target language code for the whole tree.
        makeSourceDirectory()

        bytecode_accessor = ConstantAccessor(
            data_filename="__bytecode.const", top_level_name="bytecode_data"
        )

        # This should take all bytecode values, even ones needed for frozen or
        # not produce anything.
        loader_code = LoaderCodes.getMetapathLoaderBodyCode(bytecode_accessor)

        writeSourceCode(
            filename=os.path.join(source_dir, "__loader.c"), source_code=loader_code
        )

    else:
        source_dir = OutputDirectories.getSourceDirectoryPath()

        if not os.path.isfile(os.path.join(source_dir, "__helpers.h")):
            general.sysexit("Error, no previous build directory exists.")

    if Options.isShowProgress() or Options.isShowMemory():
        general.info(
            "Total memory usage before running scons: {memory}:".format(
                memory=MemoryUsage.getHumanReadableProcessMemoryUsage()
            )
        )

    if Options.isShowMemory():
        InstanceCounters.printStats()

    if Options.is_debug:
        Reports.doMissingOptimizationReport()

    if Options.shallNotDoExecCCompilerCall():
        return True, {}

    general.info("Running data composer tool for optimal constant value handling.")

    blob_filename = runDataComposer(source_dir)
    Plugins.onDataComposerResult(blob_filename)

    for filename, source_code in Plugins.getExtraCodeFiles().items():
        target_dir = os.path.join(source_dir, "plugins")

        if not os.path.isdir(target_dir):
            makePath(target_dir)

        writeSourceCode(
            filename=os.path.join(target_dir, filename), source_code=source_code
        )

    general.info("Running C compilation via Scons.")

    # Run the Scons to build things.
    result, options = runSconsBackend(quiet=not Options.isShowScons())

    return result, options


def handleSyntaxError(e):
    # Syntax or indentation errors, output them to the user and abort. If
    # we are not in full compat, and user has not specified the Python
    # versions he wants, tell him about the potential version problem.
    error_message = SyntaxErrors.formatOutput(e)

    if not Options.is_fullcompat:
        if python_version < 0x300:
            suggested_python_version_str = getSupportedPythonVersions()[-1]
        else:
            suggested_python_version_str = "2.7"

        error_message += """

Nuitka is very syntax compatible with standard Python. It is currently running
with Python version '%s', you might want to specify more clearly with the use
of the precise Python interpreter binary and '-m nuitka', e.g. use this
'python%s -m nuitka' option, if that's not the one the program expects.
""" % (
            python_version_str,
            suggested_python_version_str,
        )

    sys.exit(error_message)


def main():
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

    if not Options.shallDumpBuiltTreeXML():
        general.info(
            "Starting Python compilation with Nuitka %r on Python %r commercial %r."
            % (getNuitkaVersion(), python_version_str, getCommercialVersion())
        )

    filename = Options.getPositionalArgs()[0]

    # Inform the importing layer about the main script directory, so it can use
    # it when attempting to follow imports.
    Importing.setMainScriptDirectory(
        main_dir=os.path.dirname(os.path.abspath(filename))
    )

    # Turn that source code into a node tree structure.
    try:
        main_module = _createNodeTree(filename=filename)
    except (SyntaxError, IndentationError) as e:
        handleSyntaxError(e)

    if Options.shallDumpBuiltTreeXML():
        # XML output only.
        for module in ModuleRegistry.getDoneModules():
            dumpTreeXML(module)
    else:
        # Make the actual compilation.
        result, options = compileTree()

        # Exit if compilation failed.
        if not result:
            sys.exit(1)

        # Relaunch in case of Python PGO input to be produced.
        if Options.shallCreatePgoInput():
            # Will not return.
            pgo_filename = OutputDirectories.getPgoRunInputFilename()
            general.info(
                "Restarting compilation using collected information from '%s'."
                % pgo_filename
            )
            reExecuteNuitka(pgo_filename=pgo_filename)

        if Options.shallNotDoExecCCompilerCall():
            if Options.isShowMemory():
                MemoryUsage.showMemoryTrace()

            sys.exit(0)

        executePostProcessing()

        if Options.isStandaloneMode():
            binary_filename = options["result_exe"]

            setMainEntryPoint(binary_filename)

            dist_dir = OutputDirectories.getStandaloneDirectoryPath()

            for module in ModuleRegistry.getDoneModules():
                addIncludedEntryPoints(Plugins.considerExtraDlls(dist_dir, module))

            copyUsedDLLs(
                source_dir=OutputDirectories.getSourceDirectoryPath(),
                dist_dir=dist_dir,
                standalone_entry_points=getStandaloneEntryPoints(),
            )

            copyDataFiles(dist_dir=dist_dir)

            Plugins.onStandaloneDistributionFinished(dist_dir)

            if Options.isOnefileMode():
                packDistFolderToOnefile(dist_dir, binary_filename)

                if Options.isRemoveBuildDir():
                    general.info("Removing dist folder %r." % dist_dir)

                    removeDirectory(path=dist_dir, ignore_errors=False)
                else:
                    general.info(
                        "Keeping dist folder %r for inspection, no need to use it."
                        % dist_dir
                    )

        # Remove the source directory (now build directory too) if asked to.
        source_dir = OutputDirectories.getSourceDirectoryPath()

        if Options.isRemoveBuildDir():
            general.info("Removing build directory %r." % source_dir)

            removeDirectory(path=source_dir, ignore_errors=False)
            assert not os.path.exists(source_dir)
        else:
            general.info("Keeping build directory %r." % source_dir)

        final_filename = OutputDirectories.getResultFullpath(
            onefile=Options.isOnefileMode()
        )

        if "macos_minversion" in options:
            general.info(
                "Created binary that runs on macOS %s or higher."
                % options["macos_minversion"]
            )

        Plugins.onFinalResult(final_filename)

        general.info("Successfully created %r." % final_filename)

        report_filename = Options.getCompilationReportFilename()

        if report_filename:
            writeCompilationReport(report_filename)

        # Execute the module immediately if option was given.
        if Options.shallExecuteImmediately():
            run_filename = OutputDirectories.getResultRunFilename(
                onefile=Options.isOnefileMode()
            )

            general.info("Launching %r." % run_filename)

            if Options.shallMakeModule():
                executeModule(
                    tree=main_module,
                    clean_path=Options.shallClearPythonPathEnvironment(),
                )
            else:
                executeMain(
                    binary_filename=run_filename,
                    clean_path=Options.shallClearPythonPathEnvironment(),
                )
