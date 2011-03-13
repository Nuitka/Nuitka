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
""" This module maintains the parameter specification classes.

These are used for function, lambdas, generators. They are also a factory
for the respective variable objects. One of the difficulty of Python and
its parameter parsing is that they are allowed to be nested like this:

(a,b), c

Much like in assignments, which are very similar to parameters, except
that parameters may also be assigned from a dictionary, they are no less
flexible.

"""

from nuitka import Variables

class ParameterSpecTuple:
    def __init__( self, normal_args, nest_count = 1 ):
        self.normal_args = tuple( normal_args )
        self.nest_count = nest_count

        self.owner = None
        self.normal_variables = None

    def getNormalParameters( self ):
        return self.normal_variables

    def setOwner( self, owner ):
        self.owner = owner

        self.normal_variables = []

        for count, normal_arg in enumerate( self.normal_args ):
            if type( normal_arg ) == str:
                normal_variable = Variables.ParameterVariable( self.owner, normal_arg )
            elif type( normal_arg ) == tuple:
                sub_parameter_spec = ParameterSpecTuple(
                    normal_args = normal_arg,
                    nest_count  = self.nest_count + 1
                )
                sub_parameter_spec.setOwner( self.owner )

                sub_parameter_name = "Unpackable_%s_%s" % (
                    self.nest_count,
                    count+1
                )

                normal_variable = Variables.NestedParameterVariable(
                    self.owner,
                    sub_parameter_name,
                    sub_parameter_spec
                )
            else:
                assert False, normal_arg

            self.normal_variables.append( normal_variable )

    def getVariables( self ):
        result = []

        for variable in self.normal_variables:
            if variable.isNestedParameterVariable():
                result += variable.getVariables()
            else:
                result.append( variable )

        return result

    def getAllVariables( self ):
        result = self.normal_variables[:]

        for variable in self.normal_variables:
            if variable.isNestedParameterVariable():
                result += variable.getAllVariables()

        return result

    def getTopLevelVariables( self ):
        return self.normal_variables

    def getParameterNames( self ):
        return Variables.getNames( self.getVariables() )

class ParameterSpec( ParameterSpecTuple ):
    def __init__( self, normal_args, list_star_arg, dict_star_arg, default_count ):
        assert None not in normal_args

        self.nest_count = 1

        ParameterSpecTuple.__init__( self, normal_args )

        self.list_star_arg = list_star_arg
        self.dict_star_arg = dict_star_arg

        self.list_star_variable = None
        self.dict_star_variable = None

        self.default_count = default_count

        for count, normal_arg in enumerate( normal_args ):
            if normal_arg in normal_args[ count+1:] or normal_arg in ( list_star_arg, dict_star_arg ):
                raise SyntaxError( "Duplicate argument detected" )

    def __repr__( self ):
        parts = [ str(normal_arg) for normal_arg in self.normal_args ]

        if self.list_star_arg is not None:
            parts.append( "*%s" % self.list_star_arg )

        if self.dict_star_variable is not None:
            parts.append( "**%s" % self.dict_star_variable )

        if parts:
            return "<ParameterSpec %s>" % ",".join( parts )
        else:
            return "<NoParameters>"

    def setOwner( self, owner ):
        ParameterSpecTuple.setOwner( self, owner )

        if self.list_star_arg:
            self.list_star_variable = Variables.ParameterVariable( owner, self.list_star_arg )
        else:
            self.list_star_variable = None

        if self.dict_star_arg:
            self.dict_star_variable = Variables.ParameterVariable( owner, self.dict_star_arg )
        else:
            self.dict_star_variable = None

    def isEmpty( self ):
        return len( self.normal_args ) == 0 and self.list_star_arg is None and self.dict_star_arg is None

    def getDefaultParameterVariables( self ):
        result = ParameterSpecTuple.getTopLevelVariables( self )

        return result[ len( self.normal_args ) - self.default_count : ]

    def getDefaultParameterNames( self ):
        return self.normal_args[ len( self.normal_args ) - self.default_count : ]

    def getDefaultParameterCount( self ):
        return self.default_count

    def hasDefaultParameters( self ):
        return self.getDefaultParameterCount() > 0

    def getVariables( self ):
        result = ParameterSpecTuple.getVariables( self )

        if self.list_star_variable is not None:
            result.append( self.list_star_variable )

        if self.dict_star_variable is not None:
            result.append( self.dict_star_variable )

        return result

    def getAllVariables( self ):
        result = ParameterSpecTuple.getAllVariables( self )

        if self.list_star_variable is not None:
            result.append( self.list_star_variable )

        if self.dict_star_variable is not None:
            result.append( self.dict_star_variable )

        return result


    def getListStarArgName( self ):
        return self.list_star_arg

    def getListStarArgVariable( self ):
        return self.list_star_variable

    def getDictStarArgName( self ):
        return self.dict_star_arg

    def getDictStarArgVariable( self ):
        return self.dict_star_variable
