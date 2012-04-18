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
""" Optimizations of builtins to builtin calls.

"""
from nuitka.nodes.NodeMakingHelpers import makeRaiseExceptionReplacementExpressionFromInstance

from nuitka.nodes.CallNode import CPythonExpressionCall

from nuitka.nodes.ParameterSpec import ParameterSpec, TooManyArguments, matchCall

from nuitka.Utils import python_version

import sys

class BuiltinParameterSpec( ParameterSpec ):
    def __init__( self, name, arg_names, default_count, list_star_arg = None, dict_star_arg = None ):
        ParameterSpec.__init__(
            self,
            name           = name,
            normal_args    = arg_names,
            list_star_arg  = list_star_arg,
            dict_star_arg  = dict_star_arg,
            default_count  = default_count
        )

        self.builtin = __builtins__[ name ]

    def __repr__( self ):
        return "<BuiltinParameterSpec %s>" % self.name

    def getName( self ):
        return self.name

    def simulateCall( self, given_values ):
        # Using star dict call for simulation and catch any exception as really fatal,
        # pylint: disable=W0142,W0703

        try:
            given_normal_args = given_values[ : len( self.normal_args ) ]

            if self.list_star_arg:
                given_list_star_args = given_values[ len( self.normal_args ) ]
            else:
                given_list_star_args = None

            if self.dict_star_arg:
                given_dict_star_args = given_values[ -1 ]
            else:
                given_dict_star_args = None

            arg_dict = {}

            for arg_name, given_value in zip( self.normal_args, given_normal_args ):
                assert type( given_value ) not in ( tuple, list ), ( "do not like a tuple %s" % ( given_value, ))

                if given_value is not None:
                    arg_dict[ arg_name ] = given_value.getCompileTimeConstant()

            if given_dict_star_args:
                for given_dict_star_arg in given_dict_star_args:
                    arg_name = given_dict_star_arg.getKey()
                    arg_value = given_dict_star_arg.getValue()

                    arg_dict[ arg_name.getCompileTimeConstant() ] = arg_value.getCompileTimeConstant()

        except Exception as e:
            sys.exit( "Fatal problem: %r" % e )

        if given_list_star_args:
            return self.builtin(
                *( value.getCompileTimeConstant() for value in given_list_star_args ),
                **arg_dict
            )
        else:
            return self.builtin( **arg_dict )


class BuiltinParameterSpecNoKeywords( BuiltinParameterSpec ):

    def allowsKeywords( self ):
        return False

    def simulateCall( self, given_values ):
        # Using star dict call for simulation and catch any exception as really fatal,
        # pylint: disable=W0142,W0703

        try:
            if self.list_star_arg:
                given_list_star_arg = given_values[ len( self.normal_args ) ]
            else:
                given_list_star_arg = None

            arg_list = []
            refuse_more = False

            for _arg_name, given_value in zip( self.normal_args, given_values ):
                assert type( given_value ) not in ( tuple, list ), ( "do not like tuple %s" % ( given_value, ))

                if given_value is not None:
                    if not refuse_more:
                        arg_list.append( given_value.getCompileTimeConstant() )
                    else:
                        assert False
                else:
                    refuse_more = True

            if given_list_star_arg is not None:
                arg_list += [ value.getCompileTimeConstant() for value in given_list_star_arg ]
        except Exception as e:
            sys.exit( e )

        return self.builtin( *arg_list )


class BuiltinParameterSpecExceptions( BuiltinParameterSpec ):
    def __init__( self, name, default_count ):
        # TODO: Parameter default_count makes no sense for exceptions probably.
        BuiltinParameterSpec.__init__(
            self,
            name          = name,
            arg_names     = (),
            default_count = default_count,
            list_star_arg = "args"
        )

    def allowsKeywords( self ):
        return False

    def getKeywordRefusalText( self ):
        return "exceptions.%s does not take keyword arguments" % self.name


    def getCallableName( self ):
        return "exceptions." + self.getName()

builtin_int_spec = BuiltinParameterSpec( "int", ( "x", "base" ), 2 )
# This builtin is only available for Python2
if python_version < 300:
    builtin_long_spec = BuiltinParameterSpec( "long", ( "x", "base" ), 2 )
    builtin_execfile_spec = BuiltinParameterSpecNoKeywords( "execfile", ( "filename", "globals", "locals" ), 2 )

builtin_bool_spec = BuiltinParameterSpec( "bool", ( "x", ), 1 )
builtin_float_spec = BuiltinParameterSpec( "float", ( "x", ), 1 )
builtin_str_spec = BuiltinParameterSpec( "str", ( "object", ), 1 )
builtin_len_spec = BuiltinParameterSpecNoKeywords( "len", ( "object", ), 0 )
builtin_dict_spec = BuiltinParameterSpec( "dict", (), 0, "list_args", "dict_args" )
builtin_len_spec = BuiltinParameterSpecNoKeywords( "len", ( "object", ), 0 )
builtin_tuple_spec = BuiltinParameterSpec( "tuple", ( "sequence", ), 1 )
builtin_list_spec = BuiltinParameterSpec( "list", ( "sequence", ), 1 )
builtin_import_spec = BuiltinParameterSpec( "__import__", ( "name", "globals", "locals", "fromlist", "level" ), 4 )
builtin_open_spec = BuiltinParameterSpec( "open", ( "name", "mode", "buffering" ), 2 )
builtin_chr_spec = BuiltinParameterSpecNoKeywords( "chr", ( "i", ), 0 )
builtin_ord_spec = BuiltinParameterSpecNoKeywords( "ord", ( "c", ), 0 )
builtin_bin_spec = BuiltinParameterSpecNoKeywords( "bin", ( "number", ), 0 )
builtin_oct_spec = BuiltinParameterSpecNoKeywords( "oct", ( "number", ), 0 )
builtin_hex_spec = BuiltinParameterSpecNoKeywords( "hex", ( "number", ), 0 )
builtin_range_spec = BuiltinParameterSpecNoKeywords( "range", ( "start", "stop", "step" ), 2 )
builtin_repr_spec = BuiltinParameterSpecNoKeywords( "repr", ( "object", ), 0 )

builtin_dir_spec = BuiltinParameterSpecNoKeywords( "dir", ( "object", ), 0 )
builtin_vars_spec = BuiltinParameterSpecNoKeywords( "vars", ( "object", ), 0 )

builtin_locals_spec = BuiltinParameterSpecNoKeywords( "locals", (), 0 )
builtin_globals_spec = BuiltinParameterSpecNoKeywords( "globals", (), 0 )


def extractBuiltinArgs( node, builtin_spec, builtin_class ):
    # These cannot be handled.
    if node.getStarListArg() is not None or node.getStarDictArg() is not None:
        return None

    try:
        pairs = tuple(
            ( pair.getKey().getConstant(), pair.getValue() )
            for pair in
            node.getNamedArgumentPairs()
        )

        if pairs and not builtin_spec.allowsKeywords():
            raise TooManyArguments(
                TypeError( builtin_spec.getKeywordRefusalText() )
            )

        args_dict = matchCall(
            func_name     = builtin_spec.getName(),
            args          = builtin_spec.getArgumentNames(),
            star_list_arg = builtin_spec.getStarListArgumentName(),
            star_dict_arg = builtin_spec.getStarDictArgumentName(),
            num_defaults  = builtin_spec.getDefaultCount(),
            positional    = node.getPositionalArguments(),
            pairs         = pairs
        )
    except TooManyArguments as e:
        return CPythonExpressionCall(
            called_expression = makeRaiseExceptionReplacementExpressionFromInstance(
                expression     = node,
                exception      = e.getRealException()
            ),
            positional_args   = node.getPositionalArguments(),
            list_star_arg     = node.getStarListArg(),
            dict_star_arg     = node.getStarDictArg(),
            pairs             = node.getNamedArgumentPairs(),
            source_ref        = node.getSourceReference()
        )

    args_list = []

    for argument_name in builtin_spec.getArgumentNames():
        args_list.append( args_dict[ argument_name ] )

    if builtin_spec.getStarListArgumentName() is not None:
        args_list.append( args_dict[ builtin_spec.getStarListArgumentName() ] )

    if builtin_spec.getStarDictArgumentName() is not None:
        args_list.append( args_dict[ builtin_spec.getStarDictArgumentName() ] )

    # Using list reference for passing the arguments without names, pylint: disable=W0142
    return builtin_class(
        source_ref = node.getSourceReference(),
        *args_list
    )
