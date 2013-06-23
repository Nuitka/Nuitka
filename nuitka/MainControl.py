#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" This is the main control actions of Nuitka, for use in several main programs.

This can do all the steps to translate one module to a target language using the Python
C/API, to compile it to either an executable or an extension module.

"""

from .tree import (
    Recursion,
    Building
)

from . import (
    ModuleRegistry,
    Tracing,
    TreeXML,
    Options,
    Utils
)

from .build import SconsInterface

from .codegen import CodeGeneration

from .optimizations import Optimization
from .finalizations import Finalization

import sys, os

def createNodeTree( filename ):
    """ Create a node tree.

    Turn that source code into a node tree structure. If recursion into
    imported modules is available, more trees will be available during
    optimization, or immediately through recursed directory paths.

    """

    # First, build the raw node tree from the source code.
    result = Building.buildModuleTree(
        filename = filename,
        package  = None,
        is_top   = True,
        is_main  = not Options.shallMakeModule()
    )
    ModuleRegistry.addRootModule( result )

    # Second, do it for the directories given.
    for plugin_filename in Options.getShallFollowExtra():
        Recursion.checkPluginPath(
            plugin_filename = plugin_filename,
            module_package  = None
        )

    # Then optimize the tree and potentially recursed modules.
    Optimization.optimize()

    return result

def dumpTree( tree ):
    Tracing.printLine( "Analysis -> Tree Result" )

    Tracing.printSeparator()
    Tracing.printSeparator()
    Tracing.printSeparator()

    tree.dump()

    Tracing.printSeparator()
    Tracing.printSeparator()
    Tracing.printSeparator()

def dumpTreeXML( tree ):
    xml_root = tree.asXml()
    TreeXML.dump( xml_root )

def displayTree( tree ):
    # Import only locally so the Qt4 dependency doesn't normally come into play when it's
    # not strictly needed, pylint: disable=W0404
    from .gui import TreeDisplay

    TreeDisplay.displayTreeInspector( tree )

def getTreeFilenameWithSuffix( tree, suffix ):
    return tree.getOutputFilename() + suffix

def getSourceDirectoryPath( main_module ):
    assert main_module.isPythonModule()

    return Options.getOutputPath(
        path = Utils.basename(
            getTreeFilenameWithSuffix( main_module, ".build" )
        )
    )

def getResultPath( main_module ):
    assert main_module.isPythonModule()

    return Options.getOutputPath(
        path = Utils.basename(
            getTreeFilenameWithSuffix( main_module, "" )
        )
    )

def _cleanSourceDirectory( source_dir ):
    if Utils.isDir( source_dir ):
        for path, _filename in Utils.listDir( source_dir ):
            if Utils.getExtension( path ) in ( ".cpp", ".hpp", ".o", ".os" ):
                Utils.deleteFile( path, True )
    else:
        Utils.makePath( source_dir )

    static_source_dir = Utils.joinpath( source_dir, "static" )

    if Utils.isDir( static_source_dir ):
        for path, _filename in sorted( Utils.listDir( static_source_dir ) ):
            if Utils.getExtension( path ) in ( ".o", ".os" ):
                Utils.deleteFile( path, True )

def _pickSourceFilenames( source_dir, modules ):
    collision_filenames = set()
    seen_filenames = set()

    for module in sorted( modules, key = lambda x : x.getFullName() ):
        base_filename = Utils.joinpath( source_dir, module.getFullName() )

        # Note: Could detect if the filesystem is cases sensitive in source_dir
        # or not, but that's probably not worth the effort.
        collision_filename = Utils.normcase( base_filename )

        if collision_filename in seen_filenames:
            collision_filenames.add( collision_filename )

        seen_filenames.add( collision_filename )

    collision_counts = {}

    module_filenames = {}

    for module in sorted( modules, key = lambda x : x.getFullName() ):
        base_filename = Utils.joinpath(
            source_dir,
            "module." + module.getFullName()
              if not module.isInternalModule()
            else module.getFullName()
        )

        collision_filename = Utils.normcase( base_filename )

        if collision_filename in collision_filenames:
            collision_counts[ collision_filename ] = collision_counts.get( collision_filename, 0 ) + 1
            hash_suffix = "@%d" % collision_counts[ collision_filename ]
        else:
            hash_suffix = ""

        base_filename += hash_suffix

        cpp_filename = base_filename + ".cpp"
        hpp_filename = base_filename + ".hpp"

        module_filenames[ module ] = ( cpp_filename, hpp_filename )

    return module_filenames

def makeSourceDirectory( main_module ):
    assert main_module.isPythonModule()

    source_dir = getSourceDirectoryPath( main_module )

    # First remove old object files and old generated files, they can only do harm.
    _cleanSourceDirectory( source_dir )

    # The global context used to generate code.
    global_context = CodeGeneration.makeGlobalContext()

    # Get the full list of modules imported, create code for all of them.
    modules = ModuleRegistry.getDoneModules()
    assert main_module in modules

    # Sometimes we need to talk about all modules except main module.
    other_modules = tuple(
        m
        for m in
        modules
        if not m.isMainModule() and not m.isInternalModule()
    )

    # Prepare code generation, i.e. execute finalization for it.
    for module in sorted( modules, key = lambda x : x.getFullName() ):
        Finalization.prepareCodeGeneration( module )

    # Pick filenames.
    module_filenames = _pickSourceFilenames(
        source_dir = source_dir,
        modules    = modules
    )

    module_hpps = []

    for module in sorted( modules, key = lambda x : x.getFullName() ):
        cpp_filename, hpp_filename = module_filenames[ module ]

        source_code, header_code, module_context = \
          CodeGeneration.generateModuleCode(
            global_context = global_context,
            module         = module,
            module_name    = module.getFullName(),
            other_modules  = other_modules if module.isMainModule() else ()
        )

        # The main of an executable module gets a bit different code.
        if module is main_module and not Options.shallMakeModule():
            source_code = CodeGeneration.generateMainCode(
                context = module_context,
                module  = module,
                codes   = source_code
            )

        module_hpps.append( hpp_filename )

        writeSourceCode(
            filename     = cpp_filename,
            source_code  = source_code
        )

        writeSourceCode(
            filename     = hpp_filename,
            source_code  = header_code
        )

    writeSourceCode(
        filename    = Utils.joinpath( source_dir, "__constants.hpp" ),
        source_code = CodeGeneration.generateConstantsDeclarationCode(
            context = global_context
        )
    )

    writeSourceCode(
        filename    = Utils.joinpath( source_dir, "__constants.cpp" ),
        source_code = CodeGeneration.generateConstantsDefinitionCode(
            context = global_context
        )
    )

    helper_decl_code, helper_impl_code = CodeGeneration.generateHelpersCode()

    writeSourceCode(
        filename    = Utils.joinpath( source_dir, "__helpers.hpp" ),
        source_code = helper_decl_code
    )

    writeSourceCode(
        filename    = Utils.joinpath( source_dir, "__helpers.cpp" ),
        source_code = helper_impl_code
    )

    module_hpp_include = [
        '#include "%s"\n' % Utils.basename( module_hpp )
        for module_hpp in
        module_hpps
    ]

    writeSourceCode(
        filename    = Utils.joinpath( source_dir, "__modules.hpp" ),
        source_code = "".join( module_hpp_include )
    )

def runScons( main_module, quiet ):
    python_version = "%d.%d" % ( sys.version_info[0], sys.version_info[1] )

    if hasattr( sys, "abiflags" ):
        # The Python3 for some platforms has sys.abiflags pylint: disable=E1101
        if Options.options.python_debug is not None or hasattr( sys, "getobjects" ):
            if sys.abiflags.startswith( "d" ):
                python_version += sys.abiflags
            else:
                python_version += "d" + sys.abiflags
        else:
            python_version += sys.abiflags
    elif Options.options.python_debug is not None or hasattr( sys, "getobjects" ):
        python_version += "_d"

    def asBoolStr( value ):
        return "true" if value else "false"

    options = {
        "name"           : Utils.basename( getTreeFilenameWithSuffix( main_module, "" ) ),
        "result_file"    : getResultPath( main_module ),
        "source_dir"     : getSourceDirectoryPath( main_module ),
        "debug_mode"     : asBoolStr( Options.isDebug() ),
        "unstriped_mode" : asBoolStr( Options.isUnstriped() ),
        "module_mode"    : asBoolStr( Options.shallMakeModule() ),
        "optimize_mode"  : asBoolStr( Options.isOptimize() ),
        "full_compat"    : asBoolStr( Options.isFullCompat() ),
        "experimental"   : asBoolStr( Options.isExperimental() ),
        "python_version" : python_version,
        "lto_mode"       : asBoolStr( Options.isLto() ),
        "clang_mode"     : asBoolStr( Options.isClang() )
    }

    if Options.isWindowsTarget():
        options[ "win_target" ] = "true"

    if Options.shallDisableConsoleWindow():
        options[ "win_disable_console" ] = "true"

    if Options.isPortableMode():
        options[ "portable_mode" ] = "true"

    return SconsInterface.runScons( options, quiet ), options

def writeSourceCode( filename, source_code ):
    # Prevent accidental overwriting. When this happens the collision detection or
    # something else has failed.
    assert not Utils.isFile( filename ), filename

    if Utils.python_version >= 300:
        with open( filename, "wb" ) as output_file:
            output_file.write( source_code.encode( "latin1" ) )
    else:
        with open( filename, "w" ) as output_file:
            output_file.write( source_code )


def callExec( args, clean_path, add_path ):
    old_python_path = os.environ.get( "PYTHONPATH", None )

    if clean_path and old_python_path is not None:
        os.environ[ "PYTHONPATH" ] = ""

    if add_path:
        os.environ[ "PYTHONPATH" ] = os.environ.get( "PYTHONPATH", "" ) + ":" + Options.getOutputDir()

    # We better flush these, "os.execl" won't do it anymore.
    sys.stdout.flush()
    sys.stderr.flush()

    args += Options.getMainArgs()

    # That's the API of execl, pylint: disable=W0142
    os.execl( *args )

    if old_python_path is not None:
        os.environ[ "PYTHONPATH" ] = old_python_path
    else:
        del os.environ[ "PYTHONPATH" ]


def executeMain( binary_filename, tree, clean_path ):
    main_filename = tree.getFilename()

    if Options.isPortableMode():
        name = binary_filename
    elif main_filename.endswith( ".py" ):
        name = main_filename[:-3]
    else:
        name = main_filename

    name = os.path.abspath( name )

    if not Options.isWindowsTarget() or os.name == "nt":
        args = ( binary_filename, name )
    else:
        args = ( "/usr/bin/wine", "wine", binary_filename )

    callExec(
        clean_path = clean_path,
        add_path   = False,
        args       = args
    )

def executeModule( tree, clean_path ):
    python_command = "__import__( '%s' )" % tree.getName()

    if os.name == "nt":
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

def compileTree( main_module ):
    if not Options.shallOnlyExecGcc():
        # Now build the target language code for the whole tree.
        makeSourceDirectory(
            main_module = main_module
        )
    else:
        source_dir = getSourceDirectoryPath( main_module )

        if not Utils.isFile( Utils.joinpath( source_dir, "__helpers.hpp" ) ):
            sys.exit( "Error, no previous build directory exists." )


    # Run the Scons to build things.
    result, options = runScons(
        main_module  = main_module,
        quiet        = not Options.isShowScons()
    )

    return result, options
