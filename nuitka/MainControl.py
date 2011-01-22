#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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

from __future__ import print_function

from . import (
    CodeGeneration,
    TreeOperations,
    TreeBuilding,
    Optimization,
    Generator,
    Contexts,
    Options,
    Utils
)

import sys, os

def createNodeTree( filename ):
    """ Create a node tree.

    Turn that source code into a node tree structure. If recursion into imported modules
    is available, more trees will be available during optimization.

    """

    # First build the raw node tree from the source code.
    result = TreeBuilding.buildModuleTree(
        filename = filename,
        package  = None,
        is_main  = not Options.shallMakeModule()
    )

    # Then optimize the tree.
    result = Optimization.optimizeTree( result )

    return result

def dumpTree( tree ):
    print( "Analysis -> Tree Result" )

    print( "*" * 80 )
    print( "*" * 80 )
    print("*" * 80)
    tree.dump()
    print( "*" * 80 )
    print( "*" * 80 )
    print( "*" * 80 )


def displayTree( tree ):
    # Import only locally so the Qt4 dependency doesn't normally come into play.
    import TreeDisplay

    TreeDisplay.displayTreeInspector( tree )

def _couldBeNone( node ):
    if node is None:
        return True
    elif node.isDictionaryCreation():
        return False
    elif node.isBuiltinGlobals() or node.isBuiltinLocals() or node.isBuiltinDir() or node.isBuiltinVars():
        return False
    else:
        # assert False, node
        return True

class _OverflowCheckVisitor:
    def __init__( self, checked_node ):
        self.result = False

        self.is_class = checked_node.getParent().isClassReference()

    def __call__( self, node ):
        if node.isStatementImportStarExternal():
            self.result = True

            raise TreeOperations.ExitVisit

        if node.isStatementExec() and _couldBeNone( node.getGlobals() ):
            self.result = True

            raise TreeOperations.ExitVisit

        if self.is_class and node.isBuiltinLocals():
            self.result = True

            raise TreeOperations.ExitVisit

    def getResult( self ):
        return self.result


def checkOverflowNeed( node ):
    visitor = _OverflowCheckVisitor( node )

    TreeOperations.visitScope( node, visitor )

    return visitor.getResult()

# TODO: Integrate this with optimizations framework. It should become something that is
# done in a similar way.
class _PrepareCodeGenerationVisitor:
    def __call__( self, node ):
        if node.isFunctionReference() or node.isClassReference():
            if checkOverflowNeed( node.getBody() ):
                node.markAsLocalsDict()

        if node.isStatementBreak() or node.isStatementContinue():
            search = node.getParent()

            crossed_try = False

            while not search.isStatementForLoop() and not search.isStatementWhileLoop():
                last_search = search
                search = search.getParent()

                if search.isStatementTryFinally() and last_search == search.getBlockTry():
                    crossed_try = True

            if crossed_try:
                search.markAsExceptionBreakContinue()
                node.markAsExceptionBreakContinue()

        if node.isStatementRaiseException() and node.isReraiseException():
            search = node.getParent()

            crossed_except = False

            while not search.isParentVariableProvider():
                if search.isStatementsSequence():
                    if search.getParent().isStatementTryExcept():
                        if search in search.getParent().getExceptionCatchBranches():
                            crossed_except = True
                            break

                search = search.getParent()

            if crossed_except:
                node.markAsReraiseLocal()

        if node.isStatementExecInline() and node.provider.isFunctionReference():
            for variable in node.getProvidedVariables():
                if variable.isLocalVariable():
                    node.provider.registerProvidedVariable( variable )

def _prepareCodeGeneration( tree ):
    visitor = _PrepareCodeGenerationVisitor()

    TreeOperations.visitTree( tree, visitor )

def makeModuleSource( tree ):
    _prepareCodeGeneration( tree )

    source_code = CodeGeneration.generateModuleCode(
        module         = tree,
        module_name    = tree.getName(),
        global_context = Contexts.PythonGlobalContext(),
        stand_alone    = True
    )

    return source_code

def makeSourceDirectory( main_module ):
    assert main_module.isModule()

    name = Utils.basename( main_module.getFilename() ).replace( ".py", "" )

    source_dir = Options.getOutputPath( name + ".build" )

    if not source_dir.endswith( "/" ):
        source_dir += "/"

    if os.path.exists( source_dir ):
        os.system( "rm -f '" + source_dir + "'/*.cpp '" + source_dir + "'/*.hpp" )
    else:
        os.makedirs( source_dir )

    global_context = Contexts.PythonGlobalContext()

    other_modules = Optimization.getOtherModules()

    if main_module in other_modules:
        other_modules.remove( main_module )

    for other_module in sorted( other_modules, key = lambda x : x.getName() ):
        _prepareCodeGeneration( other_module )

    module_hpps = []

    for other_module in sorted( other_modules, key = lambda x : x.getName() ):
        other_module_code = CodeGeneration.generateModuleCode(
            global_context = global_context,
            module         = other_module,
            module_name    = other_module.getFullName(),
            stand_alone    = False
        )

        writeSourceCode(
            cpp_filename = source_dir + other_module.getFullName() + ".cpp",
            source_code  = other_module_code
        )

        module_hpp = source_dir + other_module.getFullName() + ".hpp"

        module_hpps.append(
            module_hpp
        )

        writeSourceCode(
            cpp_filename = module_hpp,
            source_code  = Generator.getModuleDeclarationCode(
                other_module.getFullName()
            )
        )

    _prepareCodeGeneration( main_module )

    main_module_name = main_module.getName()

    # Create code for the main module.
    source_code = CodeGeneration.generateModuleCode(
        module         = main_module,
        module_name    = main_module_name,
        global_context = global_context,
        stand_alone    = True
    )

    if not Options.shallMakeModule():
        source_code = Generator.getMainCode(
            codes         = source_code,
            other_modules = other_modules
        )

    writeSourceCode(
        cpp_filename = source_dir + "__main__.cpp",
        source_code  = source_code
    )

    writeSourceCode(
        cpp_filename = source_dir + "__constants.cpp",
        source_code  = Generator.getConstantsDefinitionCode(
            context = global_context
        )
    )

    module_hpp_include = [
        '#include "%s"\n' % Utils.basename( module_hpp )
        for module_hpp in
        module_hpps
    ]

    writeSourceCode(
        cpp_filename = source_dir + "__constants.hpp",
        source_code  = Generator.getConstantsDeclarationCode(
            context = global_context
        ) + "\n".join( module_hpp_include )
    )


def runScons( tree, quiet ):
    name = Utils.basename( tree.getFilename() ).replace( ".py", "" )

    def asBoolStr( value ):
        return "true" if value else "false"

    result_file = Options.getOutputPath( name )
    source_dir = Options.getOutputPath( name + ".build" )

    options = {
        "name"           : name,
        "result_file"    : result_file,
        "source_dir"     : source_dir,
        "debug_mode"     : asBoolStr( Options.isDebug() ),
        "module_mode"    : asBoolStr( Options.shallMakeModule() ),
        "optimize_mode"  : asBoolStr( Options.isOptimize() ),
        "python_version" : Options.options.python_version if Options.options.python_version is not None else "%d.%d" % ( sys.version_info[0], sys.version_info[1] ),
        "python_debug"   : asBoolStr( Options.options.python_debug if Options.options.python_debug is not None else hasattr( sys, "getobjects" ) ),
        "lto_mode"       : asBoolStr( Options.isLto() ),
    }

    scons_command = """scons %(quiet)s -f %(scons_file)s --jobs %(job_limit)d %(options)s""" % {
        "quiet"      : " --quiet " if quiet else " ",
        "scons_file" : os.environ[ "NUITKA_SCONS" ] + "/SingleExe.scons",
        "job_limit"  : Options.getJobLimit(),
        "options"    : " ".join( "%s=%s" % ( key, value ) for key, value in options.items() )
    }

    if Options.isShowScons():
        print( "Scons command:", scons_command )

    return 0 == os.system( scons_command ), options

def writeSourceCode( cpp_filename, source_code ):
    open( cpp_filename, "w" ).write( source_code )

def executeMain( output_filename, tree ):
    name = Utils.basename( tree.getFilename() ).replace( ".py", ".exe" )

    os.execl( output_filename, name, *Options.getMainArgs() )

def executeModule( tree ):
    __import__( tree.getName() )
