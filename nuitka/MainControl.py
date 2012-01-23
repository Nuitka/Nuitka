#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" This is the main control actions of Nuitka, for use in several main programs.

This can do all the steps to translate one module to a target language using the Python
C/API, to compile it to either an executable or an extension module.

"""

from . import (
    TreeRecursion,
    TreeBuilding,
    Tracing,
    TreeXML,
    Options,
    Utils
)

from .build import SconsInterface

from .codegen import CodeGeneration

from .transform.optimizations import Optimization
from .transform.finalizations import Finalization

import sys, os, shutil

def createNodeTree( filename ):
    """ Create a node tree.

    Turn that source code into a node tree structure. If recursion into imported modules
    is available, more trees will be available during optimization.

    """

    # First, build the raw node tree from the source code.
    result = TreeBuilding.buildModuleTree(
        filename = filename,
        package  = None,
        is_main  = not Options.shallMakeModule()
    )

    # Second, do it for the directories given.
    for plugin_filename in Options.getShallFollowExtra():
        TreeRecursion.checkPluginPath(
            plugin_filename = plugin_filename,
            module_package  = None
        )

    # Then optimize the tree and potentially recursed modules.
    result = Optimization.optimizeWhole(
        main_module = result
    )

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

def _prepareCodeGeneration( tree ):
    Finalization.prepareCodeGeneration( tree )

def makeModuleSource( tree ):
    _prepareCodeGeneration( tree )

    source_code = CodeGeneration.generateModuleCode(
        module         = tree,
        module_name    = tree.getName(),
        global_context = CodeGeneration.makeGlobalContext()
    )

    return source_code

def getTreeFilenameWithSuffix( tree, suffix ):
    main_filename = tree.getFilename()

    if main_filename.endswith( ".py" ):
        return main_filename[:-3] + suffix
    else:
        return main_filename + suffix

def getSourceDirectoryPath( main_module ):
    assert main_module.isModule()

    return Options.getOutputPath(
        path = Utils.basename(
            getTreeFilenameWithSuffix( main_module, ".build" )
        )
    )

def getResultPath( main_module ):
    assert main_module.isModule()

    return Options.getOutputPath(
        path = Utils.basename(
            getTreeFilenameWithSuffix( main_module, "" )
        )
    )

def makeSourceDirectory( main_module ):
    assert main_module.isModule()

    source_dir = getSourceDirectoryPath( main_module )

    if os.path.exists( source_dir ):
        for path, filename in Utils.listDir( source_dir ):
            if Utils.getExtension( path ) in ( ".cpp", ".hpp", ".o", ".os" ):
                os.unlink( path )
    else:
        os.makedirs( source_dir )

    static_source_dir = Utils.joinpath( source_dir, "static" )

    if os.path.exists( static_source_dir ):
        for path, filename in sorted( Utils.listDir( static_source_dir ) ):
            path = Utils.joinpath( static_source_dir, filename )

            if Utils.getExtension( path ) in ( ".o", ".os" ):
                os.unlink( path )

    global_context = CodeGeneration.makeGlobalContext()

    other_modules = Optimization.getOtherModules()

    if main_module in other_modules:
        other_modules.remove( main_module )

    for other_module in sorted( other_modules, key = lambda x : x.getFullName() ):
        _prepareCodeGeneration( other_module )

    module_hpps = []

    collision_filenames = set()
    seen_filenames = set()

    for other_module in sorted( other_modules, key = lambda x : x.getFullName() ):
        base_filename = Utils.joinpath( source_dir, other_module.getFullName() )

        collision_filename = os.path.normcase( base_filename )

        if collision_filename in seen_filenames:
            collision_filenames.add( collision_filename )

        seen_filenames.add( collision_filename )

    collision_count = {}

    for collision_filename in collision_filenames:
        collision_count[ collision_filename ] = 1

    for other_module in sorted( other_modules, key = lambda x : x.getFullName() ):
        base_filename = Utils.joinpath( source_dir, other_module.getFullName() )

        # TODO: Actually the case sensitivity of build dir should be detected.
        collision_filename = os.path.normcase( base_filename )

        if collision_filename in collision_filenames:
            hash_suffix = "@%d" % collision_count[ collision_filename ]
            collision_count[ collision_filename ] += 1
        else:
            hash_suffix = ""

        base_filename += hash_suffix

        cpp_filename = base_filename + ".cpp"
        hpp_filename = base_filename + ".hpp"

        other_module_code = CodeGeneration.generateModuleCode(
            global_context = global_context,
            module         = other_module,
            module_name    = other_module.getFullName()
        )

        module_hpps.append( hpp_filename )

        writeSourceCode(
            filename     = cpp_filename,
            source_code  = other_module_code
        )

        writeSourceCode(
            filename     = hpp_filename,
            source_code  = CodeGeneration.generateModuleDeclarationCode(
                module_name = other_module.getFullName()
            )
        )

    _prepareCodeGeneration( main_module )

    main_module_name = main_module.getName()

    cpp_filename = Utils.joinpath( source_dir, "__main__.cpp" )
    hpp_filename = Utils.joinpath( source_dir, "__main__.hpp" )

    # Create code for the main module.
    source_code = CodeGeneration.generateModuleCode(
        module         = main_module,
        module_name    = main_module_name,
        global_context = global_context
    )

    if not Options.shallMakeModule():
        source_code = CodeGeneration.generateMainCode(
            codes         = source_code,
            other_modules = other_modules
        )

    writeSourceCode(
        filename    = cpp_filename,
        source_code = source_code
    )

    writeSourceCode(
        filename    = hpp_filename,
        source_code = CodeGeneration.generateModuleDeclarationCode(
            module_name = main_module_name
        )
    )

    module_hpps.append( "__main__.hpp" )

    writeSourceCode(
        filename    = Utils.joinpath( source_dir, "__constants.cpp" ),
        source_code = CodeGeneration.generateConstantsDefinitionCode(
            context = global_context
        )
    )

    module_hpp_include = [
        '#include "%s"\n' % Utils.basename( module_hpp )
        for module_hpp in
        module_hpps
    ]

    writeSourceCode(
        filename    = Utils.joinpath( source_dir, "__constants.hpp" ),
        source_code = CodeGeneration.generateConstantsDeclarationCode(
            context = global_context
        )
    )

    writeSourceCode(
        filename    = Utils.joinpath( source_dir, "__reverses.hpp" ),
        source_code = CodeGeneration.generateReversionMacrosCode(
            context = global_context
        )
    )

    writeSourceCode(
        filename    = Utils.joinpath( source_dir, "__modules.hpp" ),
        source_code = "".join( module_hpp_include )
    )

def runScons( tree, quiet ):
    if Options.options.python_version is not None:
        python_version = Options.options.python_version
    else:
        python_version = "%d.%d" % ( sys.version_info[0], sys.version_info[1] )

        if Utils.getPythonVersion() >= 320:
            # The Python3 really has sys.abiflags pylint: disable=E1101
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
        "name"           : Utils.basename( getTreeFilenameWithSuffix( tree, "" ) ),
        "result_file"    : getResultPath( tree ),
        "source_dir"     : getSourceDirectoryPath( tree ),
        "debug_mode"     : asBoolStr( Options.isDebug() ),
        "unstriped_mode" : asBoolStr( Options.isUnstriped() ),
        "module_mode"    : asBoolStr( Options.shallMakeModule() ),
        "optimize_mode"  : asBoolStr( Options.isOptimize() ),
        "python_version" : python_version,
        "lto_mode"       : asBoolStr( Options.isLto() ),
    }

    if Options.isWindowsTarget():
        options[ "win_target" ] = "true"

    return SconsInterface.runScons( options, quiet ), options

def writeSourceCode( filename, source_code ):
    assert not os.path.exists( filename ), filename

    open( filename, "w" ).write( source_code )

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

    if main_filename.endswith( ".py" ):
        name = Utils.basename( main_filename[:-3]  )
    else:
        name = Utils.basename( main_filename )

    if not Options.isWindowsTarget() or "win" in sys.platform:
        args = ( binary_filename, name )
    else:
        args = ( "/usr/bin/wine", name, binary_filename )

    callExec(
        clean_path = clean_path,
        add_path   = False,
        args       = args
    )

def executeModule( tree, clean_path ):
    args = (
        sys.executable,
        "python",
        "-c",
        "__import__( '%s' )" % tree.getName(),
    )

    callExec(
        clean_path = clean_path,
        add_path   = True,
        args       = args
    )

def compileTree( tree ):
    if not Options.shallOnlyExecGcc():
        # Now build the target language code for the whole tree.
        makeSourceDirectory(
            main_module = tree
        )

    # Run the Scons to build things.
    result, options = runScons(
        tree  = tree,
        quiet = not Options.isShowScons()
    )

    # Exit if compilation failed.
    if not result:
        sys.exit( 1 )

    # Remove the source directory (now build directory too) if asked to.
    if Options.isRemoveBuildDir():
        shutil.rmtree( getSourceDirectoryPath( tree ) )

    # Execute the module immediately if option was given.
    if Options.shallExecuteImmediately():
        if Options.shallMakeModule():
            executeModule(
                tree       = tree,
                clean_path = Options.shallClearPythonPathEnvironment()
            )
        else:
            executeMain(
                binary_filename = options[ "result_file" ] + ".exe",
                tree            = tree,
                clean_path      = Options.shallClearPythonPathEnvironment()
            )
