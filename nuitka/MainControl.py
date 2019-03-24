#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
import shutil
import sys
from logging import info, warning

from nuitka.finalizations.FinalizeMarkups import getImportedNames
from nuitka.freezer.Standalone import copyDataFiles
from nuitka.importing import Importing, Recursion
from nuitka.Options import getPythonFlags
from nuitka.plugins.Plugins import Plugins
from nuitka.PostProcessing import executePostProcessing
from nuitka.PythonVersions import (
    getPythonABI,
    getSupportedPythonVersions,
    isUninstalledPython,
    python_version,
    python_version_str,
)
from nuitka.tree import SyntaxErrors
from nuitka.utils import Execution, InstanceCounters, MemoryUsage, Utils
from nuitka.utils.AppDirs import getCacheDir
from nuitka.utils.FileOperations import (
    deleteFile,
    hasFilenameExtension,
    listDir,
    makePath,
    removeDirectory,
)

from . import ModuleRegistry, Options, TreeXML
from .build import SconsInterface
from .codegen import CodeGeneration, ConstantCodes, Reports
from .finalizations import Finalization
from .freezer.BytecodeModuleFreezer import generateBytecodeFrozenCode
from .freezer.Standalone import copyUsedDLLs, detectEarlyImports
from .optimizations import Optimization
from .tree import Building


def createNodeTree(filename):
    """ Create a node tree.

    Turn that source code into a node tree structure. If recursion into
    imported modules is available, more trees will be available during
    optimization, or immediately through recursed directory paths.

    """

    # First, build the raw node tree from the source code.
    main_module = Building.buildModuleTree(
        filename=filename,
        package=None,
        is_top=True,
        is_main=not Options.shallMakeModule(),
    )
    ModuleRegistry.addRootModule(main_module)

    # First remove old object files and old generated files, old binary or
    # module, and standalone mode program directory if any, they can only do
    # harm.
    source_dir = getSourceDirectoryPath(main_module)

    if not Options.shallOnlyExecCCompilerCall():
        cleanSourceDirectory(source_dir)

    # Prepare the ".dist" directory, throwing away what was there before.
    if Options.isStandaloneMode():
        standalone_dir = getStandaloneDirectoryPath(main_module)
        removeDirectory(path=standalone_dir, ignore_errors=True)
        makePath(standalone_dir)

    deleteFile(path=getResultFullpath(main_module), must_exist=False)

    # Second, do it for the directories given.
    for plugin_filename in Options.getShallFollowExtra():
        Recursion.checkPluginPath(plugin_filename=plugin_filename, module_package=None)

    for pattern in Options.getShallFollowExtraFilePatterns():
        Recursion.checkPluginFilenamePattern(pattern=pattern)

    for package_name in Options.getMustIncludePackages():
        package_package, package_directory, kind = Importing.findModule(
            importing=None,
            module_name=package_name,
            parent_package=None,
            level=0,
            warn=False,
        )

        if kind != "absolute":
            sys.exit("Error, failed to locate package %r." % package_name)

        Recursion.checkPluginPath(
            plugin_filename=package_directory, module_package=package_package
        )

    for module_name in Options.getMustIncludeModules():
        module_package, module_filename, kind = Importing.findModule(
            importing=None,
            module_name=module_name,
            parent_package=None,
            level=0,
            warn=False,
        )

        if kind != "absolute":
            sys.exit("Error, failed to locate module %r." % module_name)

        Recursion.checkPluginSinglePath(
            plugin_filename=module_filename, module_package=module_package
        )

    # Then optimize the tree and potentially recursed modules.
    Optimization.optimize(main_module.getOutputFilename())

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


def getTreeFilenameWithSuffix(tree, suffix):
    return tree.getOutputFilename() + suffix


def getSourceDirectoryPath(main_module):
    assert main_module.isCompiledPythonModule()

    return Options.getOutputPath(
        path=os.path.basename(getTreeFilenameWithSuffix(main_module, ".build"))
    )


def getStandaloneDirectoryPath(main_module):
    return Options.getOutputPath(
        path=os.path.basename(getTreeFilenameWithSuffix(main_module, ".dist"))
    )


def getResultBasepath(main_module):
    assert main_module.isCompiledPythonModule()

    if Options.isStandaloneMode():
        return os.path.join(
            getStandaloneDirectoryPath(main_module),
            os.path.basename(getTreeFilenameWithSuffix(main_module, "")),
        )
    else:
        return Options.getOutputPath(
            path=os.path.basename(getTreeFilenameWithSuffix(main_module, ""))
        )


def getResultFullpath(main_module):
    """ Get the final output binary result full path.

    """

    result = getResultBasepath(main_module)

    if Options.shallMakeModule():
        result += Utils.getSharedLibrarySuffix()
    else:
        if Options.getOutputFilename() is not None:
            result = Options.getOutputFilename()
        elif Utils.getOS() == "Windows":
            result += ".exe"
        elif not Options.isStandaloneMode():
            result += ".bin"

    return result


def cleanSourceDirectory(source_dir):
    extensions = (
        ".bin",
        ".c",
        ".cpp",
        ".exp",
        ".h",
        ".lib",
        ".manifest",
        ".o",
        ".obj",
        ".os",
        ".rc",
        ".res",
        ".S",
        ".txt",
    )

    if os.path.isdir(source_dir):
        for path, _filename in listDir(source_dir):
            if hasFilenameExtension(path, extensions):
                deleteFile(path, must_exist=True)
    else:
        makePath(source_dir)


def pickSourceFilenames(source_dir, modules):
    collision_filenames = set()
    seen_filenames = set()

    # Our output.
    module_filenames = {}

    def getFilenames(module):
        base_filename = os.path.join(
            source_dir,
            "module." + module.getFullName()
            if not module.isInternalModule()
            else module.getFullName(),
        )

        # Note: Could detect if the file system is cases sensitive in source_dir
        # or not, but that's probably not worth the effort. False positives do
        # no harm at all.
        collision_filename = os.path.normcase(base_filename)

        return base_filename, collision_filename

    # First pass, check for collisions.
    for module in modules:
        if module.isPythonShlibModule():
            continue

        base_filename = base_filename, collision_filename = getFilenames(module)

        if collision_filename in seen_filenames:
            collision_filenames.add(collision_filename)

        seen_filenames.add(collision_filename)

    # Count up for colliding filenames.
    collision_counts = {}

    # Second pass, this time sorted, so we get deterministic results. We will
    # apply an @1/@2 to disambiguate the filenames.
    for module in sorted(modules, key=lambda x: x.getFullName()):
        if module.isPythonShlibModule():
            continue

        base_filename = base_filename, collision_filename = getFilenames(module)

        if collision_filename in collision_filenames:
            collision_counts[collision_filename] = (
                collision_counts.get(collision_filename, 0) + 1
            )
            hash_suffix = "@%d" % collision_counts[collision_filename]
        else:
            hash_suffix = ""

        base_filename += hash_suffix

        module_filenames[module] = base_filename + ".c"

    return module_filenames


standalone_entry_points = []


def makeSourceDirectory(main_module):
    """ Get the full list of modules imported, create code for all of them.

    """
    # We deal with a lot of details here, but rather one by one, and split makes
    # no sense, pylint: disable=too-many-branches,too-many-locals,too-many-statements

    assert main_module.isCompiledPythonModule()

    # The global context used to generate code.
    global_context = CodeGeneration.makeGlobalContext()

    # assert main_module in ModuleRegistry.getDoneModules()

    # We might have chosen to include it as bytecode, and only compiled it for
    # fun, and to find its imports. In this case, now we just can drop it. Or
    # a module may shadow a frozen module, but be a different one, then we can
    # drop the frozen one.
    # TODO: This really should be done when the compiled module comes into
    # existence.
    for module in ModuleRegistry.getDoneUserModules():
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

    # Lets check if the recurse-to modules are actually present, and warn the
    # user if one of those was not found.
    for any_case_module in Options.getShallFollowModules():
        if "*" in any_case_module or "{" in any_case_module:
            continue

        for module in ModuleRegistry.getDoneUserModules():
            if module.getFullName() == any_case_module:
                break
        else:
            warning("Didn't recurse to '%s', apparently not used." % any_case_module)

    # Prepare code generation, i.e. execute finalization for it.
    for module in ModuleRegistry.getDoneModules():
        if module.isCompiledPythonModule():
            Finalization.prepareCodeGeneration(module)

    # Pick filenames.
    source_dir = getSourceDirectoryPath(main_module)

    module_filenames = pickSourceFilenames(
        source_dir=source_dir, modules=ModuleRegistry.getDoneModules()
    )

    # First pass, generate code and use constants doing so, but prepare the
    # final code generation only, because constants code will be added at the
    # end only.
    prepared_modules = {}

    for module in ModuleRegistry.getDoneModules():
        if module.isCompiledPythonModule():
            c_filename = module_filenames[module]

            try:
                prepared_modules[c_filename] = CodeGeneration.prepareModuleCode(
                    global_context=global_context,
                    module=module,
                    module_name=module.getFullName(),
                )
            except Exception:
                warning("Problem creating code for module %r." % module)
                raise

            # Main code constants need to be allocated already too.
            if module is main_module and not Options.shallMakeModule():
                prepared_modules[c_filename][1].getConstantCode(0)

    # Second pass, generate the actual module code into the files.
    for module in ModuleRegistry.getDoneModules():
        if module.isCompiledPythonModule():
            c_filename = module_filenames[module]

            template_values, module_context = prepared_modules[c_filename]

            source_code = CodeGeneration.generateModuleCode(
                module_context=module_context, template_values=template_values
            )

            writeSourceCode(filename=c_filename, source_code=source_code)

            if Options.isShowInclusion():
                info("Included compiled module '%s'." % module.getFullName())
        elif module.isPythonShlibModule():
            target_filename = os.path.join(
                getStandaloneDirectoryPath(main_module),
                *module.getFullName().split(".")
            )
            target_filename += Utils.getSharedLibrarySuffix()

            target_dir = os.path.dirname(target_filename)

            if not os.path.isdir(target_dir):
                makePath(target_dir)

            shutil.copyfile(module.getFilename(), target_filename)

            standalone_entry_points.append(
                (module.getFilename(), target_filename, module.getPackage())
            )
        elif module.isUncompiledPythonModule():
            pass
        else:
            assert False, module

    writeSourceCode(
        filename=os.path.join(source_dir, "__constants.c"),
        source_code=ConstantCodes.getConstantsDefinitionCode(context=global_context),
    )

    helper_decl_code, helper_impl_code = CodeGeneration.generateHelpersCode(
        ModuleRegistry.getDoneUserModules()
    )

    writeSourceCode(
        filename=os.path.join(source_dir, "__helpers.h"), source_code=helper_decl_code
    )

    writeSourceCode(
        filename=os.path.join(source_dir, "__helpers.c"), source_code=helper_impl_code
    )


def _asBoolStr(value):
    return "true" if value else "false"


def runScons(main_module, quiet):
    # Scons gets transported many details, that we express as variables, and
    # have checks for them, leading to many branches and statements,
    # pylint: disable=too-many-branches,too-many-statements

    options = {
        "name": os.path.basename(getTreeFilenameWithSuffix(main_module, "")),
        "result_name": getResultBasepath(main_module),
        "source_dir": getSourceDirectoryPath(main_module),
        "debug_mode": _asBoolStr(Options.isDebug()),
        "python_debug": _asBoolStr(Options.isPythonDebug()),
        "unstripped_mode": _asBoolStr(Options.isUnstripped()),
        "module_mode": _asBoolStr(Options.shallMakeModule()),
        "full_compat": _asBoolStr(Options.isFullCompat()),
        "experimental": ",".join(Options.getExperimentalIndications()),
        "trace_mode": _asBoolStr(Options.shallTraceExecution()),
        "python_version": python_version_str,
        "target_arch": Utils.getArchitecture(),
        "python_prefix": sys.prefix,
        "nuitka_src": SconsInterface.getSconsDataPath(),
        "nuitka_cache": getCacheDir(),
        "module_count": "%d"
        % (
            1
            + len(ModuleRegistry.getDoneUserModules())
            + len(ModuleRegistry.getUncompiledNonTechnicalModules())
        ),
    }

    if not Options.shallMakeModule():
        options["result_exe"] = getResultFullpath(main_module)

    # Ask Scons to cache on Windows, except where the directory is thrown
    # away. On non-Windows you can should use ccache instead.
    if not Options.isRemoveBuildDir() and Utils.getOS() == "Windows":
        options["cache_mode"] = "true"

    if Options.isLto():
        options["lto_mode"] = "true"

    # For AnaConda default to trying static lib python library, which
    # normally is just not available or if it is even unusable.
    if "Anaconda" in sys.version:
        options["static_libpython"] = "true"

    if Options.shallDisableConsoleWindow():
        options["win_disable_console"] = "true"

    if Options.isStandaloneMode():
        options["standalone_mode"] = "true"

    if (
        not Options.isStandaloneMode()
        and not Options.shallMakeModule()
        and isUninstalledPython()
    ):
        options["uninstalled_python"] = "true"

    if ModuleRegistry.getUncompiledTechnicalModules():
        options["frozen_modules"] = str(
            len(ModuleRegistry.getUncompiledTechnicalModules())
        )

    if Options.isShowScons():
        options["show_scons"] = "true"

    if Options.isMingw64():
        options["mingw_mode"] = "true"

    if Options.getMsvcVersion():
        msvc_version = Options.getMsvcVersion()

        msvc_version = msvc_version.replace("exp", "Exp")
        if "." not in msvc_version:
            msvc_version += ".0"

        options["msvc_version"] = msvc_version

    if Options.isClang():
        options["clang_mode"] = "true"

    if Options.getIconPath():
        options["icon_path"] = Options.getIconPath()

    if Options.isProfile():
        options["profile_mode"] = "true"

    if "no_warnings" in getPythonFlags():
        options["no_python_warnings"] = "true"

    if "no_asserts" in getPythonFlags():
        options["python_sysflag_optimize"] = "true"

    if python_version < 300 and sys.flags.py3k_warning:
        options["python_sysflag_py3k_warning"] = "true"

    if python_version < 300 and (sys.flags.division_warning or sys.flags.py3k_warning):
        options["python_sysflag_division_warning"] = "true"

    if sys.flags.bytes_warning:
        options["python_sysflag_bytes_warning"] = "true"

    if int(os.environ.get("NUITKA_SITE_FLAG", "no_site" in Options.getPythonFlags())):
        options["python_sysflag_no_site"] = "true"

    if "trace_imports" in Options.getPythonFlags():
        options["python_sysflag_verbose"] = "true"

    if python_version < 300 and sys.flags.unicode:
        options["python_sysflag_unicode"] = "true"

    if python_version >= 370 and sys.flags.utf8_mode:
        options["python_sysflag_utf8"] = "true"

    abiflags = getPythonABI()
    if abiflags:
        options["abiflags"] = abiflags

    return SconsInterface.runScons(options, quiet), options


def writeSourceCode(filename, source_code):
    # Prevent accidental overwriting. When this happens the collision detection
    # or something else has failed.
    assert not os.path.isfile(filename), filename

    if python_version >= 300:
        with open(filename, "wb") as output_file:
            output_file.write(source_code.encode("latin1"))
    else:
        with open(filename, "w") as output_file:
            output_file.write(source_code)


def writeBinaryData(filename, binary_data):
    # Prevent accidental overwriting. When this happens the collision detection
    # or something else has failed.
    assert not os.path.isfile(filename), filename

    assert type(binary_data) is bytes

    with open(filename, "wb") as output_file:
        output_file.write(binary_data)


def callExecPython(args, clean_path, add_path):
    old_python_path = os.environ.get("PYTHONPATH", None)

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

    Execution.callExec(args)


def executeMain(binary_filename, clean_path):
    args = (binary_filename, binary_filename)

    if Options.shallRunInDebugger():
        gdb_path = Execution.getExecutablePath("gdb")

        if gdb_path is None:
            sys.exit("Error, no 'gdb' binary found in path.")

        args = (gdb_path, "gdb", "-ex=run", "-ex=where", "--args", binary_filename)

    callExecPython(clean_path=clean_path, add_path=False, args=args)


def executeModule(tree, clean_path):
    python_command = "__import__('%s')" % tree.getName()

    args = (sys.executable, "python", "-c", python_command)

    callExecPython(clean_path=clean_path, add_path=True, args=args)


def compileTree(main_module):
    source_dir = getSourceDirectoryPath(main_module)

    if not Options.shallOnlyExecCCompilerCall():
        # Now build the target language code for the whole tree.
        makeSourceDirectory(main_module=main_module)

        frozen_code = generateBytecodeFrozenCode()

        if frozen_code is not None:
            writeSourceCode(
                filename=os.path.join(source_dir, "__frozen.c"), source_code=frozen_code
            )

        writeBinaryData(
            filename=os.path.join(source_dir, "__constants.bin"),
            binary_data=ConstantCodes.stream_data.getBytes(),
        )
    else:
        source_dir = getSourceDirectoryPath(main_module)

        if not os.path.isfile(os.path.join(source_dir, "__helpers.h")):
            sys.exit("Error, no previous build directory exists.")

    if Options.isShowProgress() or Options.isShowMemory():
        info(
            "Total memory usage before running scons: {memory}:".format(
                memory=MemoryUsage.getHumanReadableProcessMemoryUsage()
            )
        )

    if Options.isShowMemory():
        InstanceCounters.printStats()

    if Options.isDebug():
        Reports.doMissingOptimizationReport()

    if Options.shallNotDoExecCCompilerCall():
        return True, {}

    # Run the Scons to build things.
    result, options = runScons(main_module=main_module, quiet=not Options.isShowScons())

    return result, options


def handleSyntaxError(e):
    # Syntax or indentation errors, output them to the user and abort. If
    # we are not in full compat, and user has not specified the Python
    # versions he wants, tell him about the potential version problem.
    error_message = SyntaxErrors.formatOutput(e)

    if not Options.isFullCompat():
        if python_version < 300:
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
    """ Main program flow of Nuitka

        At this point, options will be parsed already, Nuitka will be executing
        in the desired version of Python with desired flags, and we just get
        to execute the task assigned.

        We might be asked to only re-compile generated C, dump only an XML
        representation of the internal node tree after optimization, etc.
    """

    # Main has to fulfill many options, leading to many branches and statements
    # to deal with them.  pylint: disable=too-many-branches
    filename = Options.getPositionalArgs()[0]

    # Inform the importing layer about the main script directory, so it can use
    # it when attempting to follow imports.
    Importing.setMainScriptDirectory(
        main_dir=os.path.dirname(os.path.abspath(filename))
    )

    # Detect to be frozen modules if any, so we can consider to not recurse
    # to them.
    if Options.isStandaloneMode():
        for module in detectEarlyImports():
            ModuleRegistry.addUncompiledModule(module)

    # Turn that source code into a node tree structure.
    try:
        main_module = createNodeTree(filename=filename)
    except (SyntaxError, IndentationError) as e:
        handleSyntaxError(e)

    if Options.shallDumpBuiltTreeXML():
        # XML output only.
        for module in ModuleRegistry.getDoneModules():
            dumpTreeXML(module)
    else:
        # Make the actual compilation.
        result, options = compileTree(main_module=main_module)

        # Exit if compilation failed.
        if not result:
            sys.exit(1)

        if Options.shallNotDoExecCCompilerCall():
            if Options.isShowMemory():
                MemoryUsage.showMemoryTrace()

            sys.exit(0)

        executePostProcessing(getResultFullpath(main_module))

        if Options.isStandaloneMode():
            binary_filename = options["result_exe"]

            standalone_entry_points.insert(0, (binary_filename, binary_filename, None))

            dist_dir = getStandaloneDirectoryPath(main_module)

            for module in ModuleRegistry.getDoneUserModules():
                standalone_entry_points.extend(
                    Plugins.considerExtraDlls(dist_dir, module)
                )

            copyUsedDLLs(
                source_dir=getSourceDirectoryPath(main_module),
                dist_dir=dist_dir,
                standalone_entry_points=standalone_entry_points,
            )

            data_files = []
            for module in ModuleRegistry.getDoneModules():
                data_files.extend(Plugins.considerDataFiles(module))

            copyDataFiles(dist_dir=dist_dir, data_files=data_files)

            Plugins.onStandaloneDistributionFinished(dist_dir)

        # Remove the source directory (now build directory too) if asked to.
        if Options.isRemoveBuildDir():
            removeDirectory(
                path=getSourceDirectoryPath(main_module), ignore_errors=False
            )

        if Options.shallMakeModule() and Options.shallCreatePyiFile():
            pyi_filename = getResultBasepath(main_module) + ".pyi"

            with open(pyi_filename, "w") as pyi_file:
                pyi_file.write(
                    """\
# This file was generated by Nuitka and describes the types of the
# created shared library.

# At this time it lists only the imports made and can be used by the
# tools that bundle libraries, including Nuitka itself. For instance
# standalone mode usage of the created library will need it.

# In the future, this will also contain type information for values
# in the module, so IDEs will use this. Therefore please include it
# when you make software releases of the extension module that it
# describes.

%(imports)s

# This is not Python source even if it looks so. Make it clear for
# now. This was decided by PEP 484 designers.
__name__ = ...

"""
                    % {
                        "imports": "\n".join(
                            "import %s" % module_name
                            for module_name in getImportedNames()
                        )
                    }
                )

        # Execute the module immediately if option was given.
        if Options.shallExecuteImmediately():
            if Options.shallMakeModule():
                executeModule(
                    tree=main_module,
                    clean_path=Options.shallClearPythonPathEnvironment(),
                )
            else:
                executeMain(
                    binary_filename=getResultFullpath(main_module),
                    clean_path=Options.shallClearPythonPathEnvironment(),
                )
