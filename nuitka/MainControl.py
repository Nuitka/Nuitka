#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
the Python C/API, to compile it to either an executable or an extension module.

"""

import os
import shutil
import subprocess
import sys
from logging import info, warning

from . import (
    Importing,
    ModuleRegistry,
    Options,
    SyntaxErrors,
    Tracing,
    TreeXML,
    Utils
)
from .build import SconsInterface
from .codegen import CodeGeneration, ConstantCodes
from .finalizations import Finalization
from .freezer.BytecodeModuleFreezer import (
    addFrozenModule,
    generateBytecodeFrozenCode,
    getFrozenModuleCount
)
from .freezer.Standalone import (
    copyUsedDLLs,
    detectEarlyImports,
    detectLateImports
)
from .optimizations import Optimization
from .tree import Building, Recursion


def createNodeTree(filename):
    """ Create a node tree.

    Turn that source code into a node tree structure. If recursion into
    imported modules is available, more trees will be available during
    optimization, or immediately through recursed directory paths.

    """

    # First, build the raw node tree from the source code.
    main_module = Building.buildModuleTree(
        filename = filename,
        package  = None,
        is_top   = True,
        is_main  = not Options.shallMakeModule()
    )
    ModuleRegistry.addRootModule(main_module)

    # First remove old object files and old generated files, old binary or
    # module, and standalone mode program directory if any, they can only do
    # harm.
    source_dir = getSourceDirectoryPath(main_module)

    if not Options.shallOnlyExecCppCall():
        cleanSourceDirectory(source_dir)

    if Options.isStandaloneMode():
        standalone_dir = getStandaloneDirectoryPath(main_module)
        shutil.rmtree(standalone_dir, ignore_errors = True)
        Utils.makePath(standalone_dir)
    Utils.deleteFile(
        path       = getResultFullpath(main_module),
        must_exist = False
    )

    # Second, do it for the directories given.
    for plugin_filename in Options.getShallFollowExtra():
        Recursion.checkPluginPath(
            plugin_filename = plugin_filename,
            module_package  = None
        )

    # Then optimize the tree and potentially recursed modules.
    Optimization.optimize()

    return main_module

def dumpTreeXML(tree):
    xml_root = tree.asXml()
    TreeXML.dump(xml_root)


def displayTree(tree):
    # Import only locally so the Qt4 dependency doesn't normally come into play
    # when it's not strictly needed.
    from .gui import TreeDisplay

    TreeDisplay.displayTreeInspector(tree)


def getTreeFilenameWithSuffix(tree, suffix):
    return tree.getOutputFilename() + suffix


def getSourceDirectoryPath(main_module):
    assert main_module.isPythonModule()

    return Options.getOutputPath(
        path = Utils.basename(
            getTreeFilenameWithSuffix(main_module, ".build")
        )
    )


def getStandaloneDirectoryPath(main_module):
    return Options.getOutputPath(
        path = Utils.basename(
            getTreeFilenameWithSuffix(main_module, ".dist")
        )
    )


def getResultBasepath(main_module):
    assert main_module.isPythonModule()

    if Options.isStandaloneMode():
        return Utils.joinpath(
            getStandaloneDirectoryPath(main_module),
            Utils.basename(
                getTreeFilenameWithSuffix(main_module, "")
            )
        )
    else:
        return Options.getOutputPath(
            path = Utils.basename(
                getTreeFilenameWithSuffix(main_module, "")
            )
        )


def getResultFullpath(main_module):
    result = getResultBasepath(main_module)

    if Options.shallMakeModule():
        if Utils.getOS() == "Windows":
            result += ".pyd"
        else:
            result += ".so"
    else:
        result += ".exe"

    return result


def cleanSourceDirectory(source_dir):
    if Utils.isDir(source_dir):
        for path, _filename in Utils.listDir(source_dir):
            if Utils.getExtension(path) in (".cpp", ".hpp", ".c", ".o", ".os",
                                            ".obj", ".bin", ".res", ".rc",
                                            ".manifest"):
                Utils.deleteFile(path, True)
    else:
        Utils.makePath(source_dir)

    static_source_dir = Utils.joinpath(
        source_dir,
        "static"
    )

    if Utils.isDir(static_source_dir):
        for path, _filename in Utils.listDir(static_source_dir):
            if Utils.getExtension(path) in (".o", ".os", ".obj"):
                Utils.deleteFile(path, True)

    win32_source_dir = Utils.joinpath(
        static_source_dir,
        "win32_ucontext_src"
    )

    if Utils.getOS() == "Windows":
        Utils.deleteFile(
            Utils.joinpath(win32_source_dir, "fibers_win32.obj"),
            False
        )


def pickSourceFilenames(source_dir, modules):
    collision_filenames = set()
    seen_filenames = set()

    # Our output.
    module_filenames = {}

    def getFilenames(module):
        base_filename =  Utils.joinpath(
            source_dir,
            "module." + module.getFullName()
              if not module.isInternalModule() else
            module.getFullName()
        )

        # Note: Could detect if the file system is cases sensitive in source_dir
        # or not, but that's probably not worth the effort. False positives do
        # no harm at all.
        collision_filename = Utils.normcase(base_filename)

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

    # Second pass, this time sorted, so we get determistic results. We will
    # apply an @1/@2 to disambiguate the filenames.
    for module in sorted(modules, key = lambda x : x.getFullName()):
        if module.isPythonShlibModule():
            continue

        base_filename = base_filename, collision_filename = getFilenames(module)

        if collision_filename in collision_filenames:
            collision_counts[ collision_filename ] = \
              collision_counts.get(collision_filename, 0) + 1
            hash_suffix = "@%d" % collision_counts[ collision_filename ]
        else:
            hash_suffix = ""

        base_filename += hash_suffix

        module_filenames[module] = base_filename + ".cpp"

    return module_filenames


standalone_entry_points = []

def makeSourceDirectory(main_module):
    # We deal with a lot of details here, but rather one by one, and split makes
    # no sense, pylint: disable=R0914,R0912

    assert main_module.isPythonModule()

    # The global context used to generate code.
    global_context = CodeGeneration.makeGlobalContext()

    # Get the full list of modules imported, create code for all of them.
    modules = ModuleRegistry.getDoneModules()
    assert main_module in modules

    # Sometimes we need to talk about all modules except main module.
    other_modules = ModuleRegistry.getDoneUserModules()

    # Lets check if the recurse-to modules are actually present, and warn the
    # user if one was not found.
    for any_case_module in Options.getShallFollowModules():
        for module in other_modules:
            if module.getFullName() == any_case_module:
                break
        else:
            warning(
                "Didn't recurse to '%s', apparently not used." % \
                any_case_module
            )

    # Prepare code generation, i.e. execute finalization for it.
    for module in sorted(modules, key = lambda x : x.getFullName()):
        if module.isPythonModule():
            Finalization.prepareCodeGeneration(module)

    # Pick filenames.
    source_dir = getSourceDirectoryPath(main_module)

    module_filenames = pickSourceFilenames(
        source_dir = source_dir,
        modules    = modules
    )

    # First pass, generate code and use constants doing so, but prepare the
    # final code generation only, because constants code will be added at the
    # end only.
    prepared_modules = {}

    for module in sorted(modules, key = lambda x : x.getFullName()):
        if module.isPythonModule():
            cpp_filename = module_filenames[module]

            prepared_modules[cpp_filename] = CodeGeneration.prepareModuleCode(
                global_context = global_context,
                module         = module,
                module_name    = module.getFullName(),
                other_modules  = other_modules
                                   if module is main_module else
                                 ()
            )

            # Main code constants need to be allocated already too.
            if module is main_module and not Options.shallMakeModule():
                prepared_modules[cpp_filename][1].getConstantCode(0)


    for module in sorted(modules, key = lambda x : x.getFullName()):
        if module.isPythonModule():
            cpp_filename = module_filenames[module]

            template_values, module_context = prepared_modules[cpp_filename]

            source_code = CodeGeneration.generateModuleCode(
                module_context  = module_context,
                template_values = template_values
            )

            # The main of an executable module gets a bit different code.
            if module is main_module and not Options.shallMakeModule():
                source_code = CodeGeneration.generateMainCode(
                    main_module = main_module,
                    context     = module_context,
                    codes       = source_code
                )

            writeSourceCode(
                filename    = cpp_filename,
                source_code = source_code
            )

            if Options.isShowInclusion():
                info("Included compiled module '%s'.", module.getFullName())

        elif module.isPythonShlibModule():
            target_filename = Utils.joinpath(
                getStandaloneDirectoryPath(main_module),
                *module.getFullName().split('.')
            )

            if Utils.getOS() == "Windows":
                target_filename += ".pyd"
            else:
                target_filename += ".so"

            target_dir = Utils.dirname(target_filename)

            if not Utils.isDir(target_dir):
                Utils.makePath(target_dir)

            shutil.copy(
                module.getFilename(),
                target_filename
            )

            standalone_entry_points.append(
                (target_filename, module.getPackage())
            )
        else:
            assert False, module

    writeSourceCode(
        filename    = Utils.joinpath(source_dir, "__constants.cpp"),
        source_code = ConstantCodes.getConstantsDefinitionCode(
            context = global_context
        )
    )

    helper_decl_code, helper_impl_code = CodeGeneration.generateHelpersCode()

    writeSourceCode(
        filename    = Utils.joinpath(source_dir, "__helpers.hpp"),
        source_code = helper_decl_code
    )

    writeSourceCode(
        filename    = Utils.joinpath(source_dir, "__helpers.cpp"),
        source_code = helper_impl_code
    )


def runScons(main_module, quiet):
    # Scons gets transported many details, that we express as variables, and
    # have checks for them, leading to many branches, pylint: disable=R0912

    python_version = "%d.%d" % (sys.version_info[0], sys.version_info[1])

    if hasattr(sys, "abiflags"):
        if Options.isPythonDebug() or \
           hasattr(sys, "getobjects"):
            if sys.abiflags.startswith('d'):
                python_version += sys.abiflags
            else:
                python_version += 'd' + sys.abiflags
        else:
            python_version += sys.abiflags

    def asBoolStr(value):
        return "true" if value else "false"

    options = {
        "name"           : Utils.basename(
            getTreeFilenameWithSuffix(main_module, "")
        ),
        "result_name"    : getResultBasepath(main_module),
        "source_dir"     : getSourceDirectoryPath(main_module),
        "debug_mode"     : asBoolStr(Options.isDebug()),
        "python_debug"   : asBoolStr(Options.isPythonDebug()),
        "unstripped_mode" : asBoolStr(Options.isUnstripped()),
        "module_mode"    : asBoolStr(Options.shallMakeModule()),
        "optimize_mode"  : asBoolStr(Options.isOptimize()),
        "full_compat"    : asBoolStr(Options.isFullCompat()),
        "experimental"   : asBoolStr(Options.isExperimental()),
        "python_version" : python_version,
        "target_arch"    : Utils.getArchitecture(),
        "python_prefix"  : sys.prefix,
        "nuitka_src"     : SconsInterface.getSconsDataPath(),
        "module_count"   : "%d" % (
            len(ModuleRegistry.getDoneUserModules()) + 1
        )
    }

    # Ask Scons to cache on Windows, except where the directory is thrown
    # away. On non-Windows you can should use ccache instead.
    if not Options.isRemoveBuildDir() and Utils.getOS() == "Windows":
        options["cache_mode"] = "true"

    if Options.isLto():
        options["lto_mode"] = "true"

    if Options.shallDisableConsoleWindow():
        options["win_disable_console"] = "true"

    if Options.isStandaloneMode():
        options["standalone_mode"] = "true"

    if getFrozenModuleCount():
        options["frozen_modules"] = str(
            getFrozenModuleCount()
        )

    if Options.isShowScons():
        options["show_scons"] = "true"

    if Options.isMingw():
        options["mingw_mode"] = "true"

    if Options.getMsvcVersion():
        msvc_version = Options.getMsvcVersion()

        msvc_version = msvc_version.replace("exp", "Exp")
        if '.' not in msvc_version:
            msvc_version += ".0"

        options["msvc_version"] = msvc_version

    if Options.isClang():
        options["clang_mode"] = "true"

    if Options.getIconPath():
        options["icon_path"] = Options.getIconPath()

    return SconsInterface.runScons(options, quiet), options


def writeSourceCode(filename, source_code):
    # Prevent accidental overwriting. When this happens the collision detection
    # or something else has failed.
    assert not Utils.isFile(filename), filename

    if Utils.python_version >= 300:
        with open(filename, "wb") as output_file:
            output_file.write(source_code.encode("latin1"))
    else:
        with open(filename, 'w') as output_file:
            output_file.write(source_code)


def writeBinaryData(filename, binary_data):
    # Prevent accidental overwriting. When this happens the collision detection
    # or something else has failed.
    assert not Utils.isFile(filename), filename

    assert type(binary_data) is bytes

    with open(filename, "wb") as output_file:
        output_file.write(binary_data)


def callExec(args, clean_path, add_path):
    old_python_path = os.environ.get("PYTHONPATH", None)

    if clean_path and old_python_path is not None:
        os.environ["PYTHONPATH"] = ""

    if add_path:
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] += ':' + Options.getOutputDir()
        else:
            os.environ["PYTHONPATH"] = Options.getOutputDir()

    # We better flush these, "os.execl" won't do it anymore.
    sys.stdout.flush()
    sys.stderr.flush()

    # Add the main arguments, previous separated.
    args += Options.getMainArgs()

    Utils.callExec(args)


def executeMain(binary_filename, tree, clean_path):
    main_filename = tree.getFilename()

    if Options.isStandaloneMode():
        name = binary_filename
    elif main_filename.endswith(".py"):
        name = main_filename[:-3]
    else:
        name = main_filename

    name = Utils.abspath(name)

    args = (binary_filename, name)

    callExec(
        clean_path = clean_path,
        add_path   = False,
        args       = args
    )


def executeModule(tree, clean_path):
    python_command = "__import__('%s')" % tree.getName()

    if Utils.getOS() == "Windows":
        python_command = '"%s"' % python_command

    args = (
        sys.executable,
        "python",
        "-c",
        python_command,
    )

    callExec(
        clean_path = clean_path,
        add_path   = True,
        args       = args
    )


def compileTree(main_module):
    source_dir = getSourceDirectoryPath(main_module)

    if not Options.shallOnlyExecCppCall():
        # Now build the target language code for the whole tree.
        makeSourceDirectory(
            main_module = main_module
        )

        if Options.isStandaloneMode():
            for late_import in detectLateImports():
                addFrozenModule(late_import)

        if getFrozenModuleCount():
            frozen_code = generateBytecodeFrozenCode()

            writeSourceCode(
                filename    = Utils.joinpath(
                    source_dir,
                    "__frozen.cpp"
                ),
                source_code = frozen_code
            )

        writeBinaryData(
            filename    = Utils.joinpath(source_dir, "__constants.bin"),
            binary_data = ConstantCodes.stream_data.getBytes()
        )
    else:
        source_dir = getSourceDirectoryPath(main_module)

        if not Utils.isFile(Utils.joinpath(source_dir, "__helpers.hpp")):
            sys.exit("Error, no previous build directory exists.")

    if Options.isShowProgress():
        Tracing.printLine(
            "Total memory usage before running scons: {memory}:".format(
                memory = Utils.getHumanReadableProcessMemoryUsage()
            )
        )

    # Run the Scons to build things.
    result, options = runScons(
        main_module = main_module,
        quiet       = not Options.isShowScons()
    )

    return result, options


data_files = []

def main():
    """ Main program flow of Nuitka

        At this point, options will be parsed already, Nuitka will be executing
        in the desired version of Python with desired flags, and we just get
        to execute the task assigned.

        We might be asked to only re-compile generated C++, dump only an XML
        representation of the internal node tree after optimization, etc.
    """

    # Main has to fullfil many options, leading to many branches and statements
    # to deal with them.  pylint: disable=R0912

    positional_args = Options.getPositionalArgs()
    assert len(positional_args) > 0

    filename = Options.getPositionalArgs()[0]

    # Inform the importing layer about the main script directory, so it can use
    # it when attempting to follow imports.
    Importing.setMainScriptDirectory(
        main_dir = Utils.dirname(Utils.abspath(filename))
    )

    # Detect to be frozen modules if any, so we can consider to not recurse
    # to them.
    if Options.isStandaloneMode():
        for early_import in detectEarlyImports():
            addFrozenModule(early_import)

            if early_import[0] == "site":
                origin_prefix_filename = Utils.joinpath(
                    Utils.dirname(early_import[3]),
                    "orig-prefix.txt"
                )

                if Utils.isFile(origin_prefix_filename):
                    data_files.append(
                        (filename, "orig-prefix.txt")
                    )

    # Turn that source code into a node tree structure.
    try:
        main_module = createNodeTree(
            filename = filename
        )
    except (SyntaxError, IndentationError) as e:
        # Syntax or indentation errors, output them to the user and abort.
        sys.exit(
            SyntaxErrors.formatOutput(e)
        )

    if Options.shallDumpBuiltTreeXML():
        for module in ModuleRegistry.getDoneModules():
            dumpTreeXML(module)
    elif Options.shallDisplayBuiltTree():
        displayTree(main_module)
    else:
        result, options = compileTree(
            main_module = main_module
        )

        # Exit if compilation failed.
        if not result:
            sys.exit(1)

        # Remove the source directory (now build directory too) if asked to.
        if Options.isRemoveBuildDir():
            shutil.rmtree(
                getSourceDirectoryPath(main_module)
            )

        if Options.isStandaloneMode():
            binary_filename = options["result_name"] + ".exe"

            standalone_entry_points.insert(
                0,
                (binary_filename, None)
            )

            if Utils.getOS() == "NetBSD":
                warning("Standalone mode on NetBSD is not functional, due to $ORIGIN linkage not being supported.")

            copyUsedDLLs(
                dist_dir                = getStandaloneDirectoryPath(
                    main_module
                ),
                binary_filename         = binary_filename,
                standalone_entry_points = standalone_entry_points
            )

            for source_filename, target_filename in data_files:
                shutil.copy2(
                    source_filename,
                    Utils.joinpath(
                        getStandaloneDirectoryPath(main_module),
                        target_filename
                    )
                )

        # Modules should not be executable, but Scons creates them like it, fix
        # it up here.
        if Utils.getOS() != "Windows" and Options.shallMakeModule():
            subprocess.call(
                (
                    "chmod",
                    "-x",
                    getResultFullpath(main_module)
                )
            )

        # Execute the module immediately if option was given.
        if Options.shallExecuteImmediately():
            if Options.shallMakeModule():
                executeModule(
                    tree       = main_module,
                    clean_path = Options.shallClearPythonPathEnvironment()
                )
            else:
                executeMain(
                    binary_filename = getResultFullpath(main_module),
                    tree            = main_module,
                    clean_path      = Options.shallClearPythonPathEnvironment()
                )
