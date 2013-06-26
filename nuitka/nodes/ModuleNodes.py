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
""" Module/Package nodes

The top of the tree. Packages are also modules. Modules are what hold a program
together and cross-module optimizations are the most difficult to tackle.
"""

from .NodeBases import (
    ClosureGiverNodeBase,
    ChildrenHavingMixin
)

from .IndicatorMixins import MarkContainsTryExceptIndicator
from nuitka.SourceCodeReferences import SourceCodeReference
from nuitka.nodes.FutureSpecs import FutureSpec

from nuitka import Variables, Utils

from nuitka.oset import OrderedSet

class PythonModule( ChildrenHavingMixin, ClosureGiverNodeBase,
                    MarkContainsTryExceptIndicator ):
    """ Module

        The module is the only possible root of a tree. When there are many
        modules they form a forrest.
    """

    kind = "PYTHON_MODULE"

    named_children = ( "body", )

    def __init__( self, name, package, source_ref ):
        assert type(name) is str, type(name)
        assert "." not in name, name
        assert package is None or ( type( package ) is str and package != "" )

        ClosureGiverNodeBase.__init__(
            self,
            name        = name,
            code_prefix = "module",
            source_ref  = source_ref
        )

        ChildrenHavingMixin.__init__(
            self,
            values = {}
        )

        MarkContainsTryExceptIndicator.__init__( self )

        self.package = package

        self.variables = set()

        # The list functions contained in that module.
        self.functions = OrderedSet()

        self.active_functions = OrderedSet()

    def getDetails( self ):
        return {
            "filename" : self.source_ref.getFilename(),
            "package"  : self.package,
            "name"     : self.name
        }

    def asXml( self ):
        # The class is new style, false alarm: pylint: disable=E1002
        result = super( PythonModule, self ).asXml()

        for function_body in self.functions:
            result.append( function_body.asXml() )

        return result

    getBody = ChildrenHavingMixin.childGetter( "body" )
    setBody = ChildrenHavingMixin.childSetter( "body" )

    def isPythonModule( self ):
        return True

    def getParent( self ):
        assert False

    def getParentVariableProvider( self ):
        return None

    def getVariables( self ):
        return self.variables

    def getFilename( self ):
        return self.source_ref.getFilename()

    def getPackage( self ):
        return self.package

    def getFullName( self ):
        if self.package:
            return self.package + "." + self.getName()
        else:
            return self.getName()

    def getVariableForAssignment( self, variable_name ):
        result = self.getProvidedVariable( variable_name )

        return result.makeReference( self )

    def getVariableForReference( self, variable_name ):
        result = self.getProvidedVariable( variable_name )

        return result.makeReference( self )

    def getVariableForClosure( self, variable_name ):
        return self.getProvidedVariable(
            variable_name = variable_name
        )

    def createProvidedVariable( self, variable_name ):
        result = Variables.ModuleVariable(
            module        = self,
            variable_name = variable_name
        )

        assert result not in self.variables
        self.variables.add( result )

        return result

    def isEarlyClosure( self ):
        # Modules should immediately closure variables on use.
        # pylint: disable=R0201
        return True

    def isMainModule( self ):
        return False

    def isInternalModule( self ):
        return False

    def getCodeName( self ):
        return "module_" + self.getFullName().replace( ".", "__" ).replace( "-", "_" )

    def addFunction( self, function_body ):
        assert function_body not in self.functions

        self.functions.add( function_body )

    def getFunctions( self ):
        return self.functions

    def startTraversal( self ):
        self.active_functions = OrderedSet()

    def addUsedFunction( self, function_body ):
        assert function_body in self.functions

        assert function_body.isExpressionFunctionBody()

        if function_body not in self.active_functions:
            self.active_functions.add( function_body )

    def getUsedFunctions( self ):
        return self.active_functions

    def getOutputFilename( self ):
        main_filename = self.getFilename()

        if main_filename.endswith( ".py" ):
            return main_filename[:-3]
        else:
            return main_filename


class SingleCreationMixin:
    created = set()

    def __init__( self ):
        assert self.__class__ not in self.created
        self.created.add( self.__class__ )


class PythonMainModule( PythonModule, SingleCreationMixin ):
    kind = "PYTHON_MAIN_MODULE"

    def __init__( self, main_added, source_ref ):
        PythonModule.__init__(
            self,
            name        = "__main__",
            package     = None,
            source_ref  = source_ref
        )

        SingleCreationMixin.__init__( self )

        self.main_added = main_added

    def isMainModule( self ):
        return True

    def getOutputFilename( self ):
        if self.main_added:
            return Utils.dirname( self.getFilename() )
        else:
            return PythonModule.getOutputFilename( self )


class PythonInternalModule( PythonModule, SingleCreationMixin ):
    kind = "PYTHON_INTERNAL_MODULE"

    def __init__( self ):
        PythonModule.__init__(
            self,
            name        = "__internal__",
            package     = None,
            source_ref  = SourceCodeReference.fromFilenameAndLine(
                filename    = "internal",
                line        = 0,
                future_spec = FutureSpec(),
                inside_exec = False
            )
        )

        SingleCreationMixin.__init__( self )

    def isInternalModule( self ):
        return True

    def getOutputFilename( self ):
        return "__internal"


class PythonPackage( PythonModule ):
    kind = "PYTHON_PACKAGE"

    def __init__( self, name, package, source_ref ):
        assert name

        PythonModule.__init__(
            self,
            name       = name,
            package    = package,
            source_ref = source_ref
        )

    def getOutputFilename( self ):
        return Utils.dirname( self.getFilename() )
