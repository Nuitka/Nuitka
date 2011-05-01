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
""" Replace builtins with alternative implementations more optimized or capable of the task.

TODO: Split in two phases, such that must be replaced (locals(), globals() and such that
are just a good idea to replace (range(), etc)
"""

from .OptimizeBase import (
    OptimizationDispatchingVisitorBase,
    getConstantComputationReplacementNode,
    makeRaiseExceptionReplacementExpressionFromInstance
)

from nuitka import Importing, Nodes

from nuitka.Utils import getPythonVersion

import math, sys

_builtin_names = [ str( x ) for x in __builtins__.keys() ]
assert "int" in _builtin_names, __builtins__.keys()

from nuitka.nodes.ParameterSpec import ParameterSpec, TooManyArguments

class BuiltinParameterSpec( ParameterSpec ):
    def __init__( self, name, arg_names, default_count, list_star_arg = None, dict_star_arg = None ):
        self.name = name
        self.builtin = __builtins__[ name ]

        ParameterSpec.__init__(
            self,
            normal_args    = arg_names,
            list_star_arg  = list_star_arg,
            dict_star_arg  = dict_star_arg,
            default_count  = default_count
        )

    def __repr__( self ):
        return "<BuiltinParameterSpec %s>" % self.name

    def getName( self ):
        return self.name

    def simulateCall( self, given_values ):
        # Using star dict call for simulation, pylint: disable=W0142

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
                    arg_dict[ arg_name ] = given_value.getConstant()

            if given_dict_star_args:
                for given_dict_star_arg in given_dict_star_args:
                    arg_name = given_dict_star_arg.getKey()
                    arg_value = given_dict_star_arg.getValue()

                    arg_dict[ arg_name.getConstant() ] = arg_value.getConstant()

        except Exception, e:
            sys.exit( "Fatal problem: %r" % e )

        if given_list_star_args:
            return self.builtin( *( value.getConstant() for value in given_list_star_args ), **arg_dict )
        else:
            return self.builtin( **arg_dict )

class BuiltinParameterSpecNoKeywords( BuiltinParameterSpec ):

    def allowsKeywords( self ):
        return False

    def simulateCall( self, given_values ):
        # Using star list call for simulation, pylint: disable=W0142

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
                        arg_list.append( given_value.getConstant() )
                    else:
                        assert False
                else:
                    refuse_more = True

            if given_list_star_arg is not None:
                arg_list += [ value.getConstant() for value in given_list_star_arg ]
        except Exception, e:
            sys.exit( e )

        return self.builtin( *arg_list )


builtin_int_spec = BuiltinParameterSpec( "int", ( "x", "base" ), 2 )
builtin_long_spec = BuiltinParameterSpec( "long", ( "x", "base" ), 2 )
builtin_bool_spec = BuiltinParameterSpec( "bool", ( "x", ), 1 )
builtin_float_spec = BuiltinParameterSpec( "float", ( "x", ), 1 )
builtin_str_spec = BuiltinParameterSpec( "str", ( "object", ), 1 )
builtin_len_spec = BuiltinParameterSpec( "len", ( "object", ), 0 )
builtin_dict_spec = BuiltinParameterSpec( "dict", (), 2, "list_args", "dict_args" )
builtin_tuple_spec = BuiltinParameterSpecNoKeywords( "tuple", ( "iterable", ), 1 )
builtin_list_spec = BuiltinParameterSpecNoKeywords( "list", ( "iterable", ), 1 )
builtin_chr_spec = BuiltinParameterSpecNoKeywords( "chr", ( "i", ), 1 )
builtin_ord_spec = BuiltinParameterSpecNoKeywords( "ord", ( "c", ), 1 )
builtin_range_spec = BuiltinParameterSpecNoKeywords( "range", ( "start", "stop", "step" ), 2 )

class ReplaceBuiltinsVisitor( OptimizationDispatchingVisitorBase ):
    """ Replace calls to builtin names by builtin nodes if possible or necessary.

    """

    # Many methods of this class could be functions, but we want it scoped on the class
    # level anyway. pylint: disable=R0201

    def __init__( self ):
        OptimizationDispatchingVisitorBase.__init__(
            self,
            dispatch_dict = {
                "globals"    : self.globals_extractor,
                "locals"     : self.locals_extractor,
                "dir"        : self.dir_extractor,
                "vars"       : self.vars_extractor,
                "eval"       : self.eval_extractor,
                "execfile"   : self.execfile_extractor,
                "__import__" : self.import_extractor,
                "chr"        : self.chr_extractor,
                "ord"        : self.ord_extractor,
                "type"       : self.type_extractor,
                "range"      : self.range_extractor,
                "tuple"      : self.tuple_extractor,
                "list"       : self.list_extractor,
                "dict"       : self.dict_extractor,
                "float"      : self.float_extractor,
                "str"        : self.str_extractor,
                "bool"       : self.bool_extractor,
                "int"        : self.int_extractor,
                "long"       : self.long_extractor,
# TODO: There is a case of len overload in the CPython test suite that we do not yet
# discover, because we have no test for write to module level variable yet, which is
# a potential breaker for every builtin replacement.
#                "len"        : self.len_extractor,
            }
        )

    def getKey( self, node ):
        if node.isExpressionFunctionCall():
            called = node.getCalledExpression()

            if called.isExpressionVariableRef():
                variable = called.getVariable()

                assert variable is not None, node

                if variable.isModuleVariable() or variable.isMaybeLocalVariable():
                    if variable.getName() in ( "dict", "float", "int", "long", "str", "unicode", "bool" ):
                        return variable.getName()

                    else:
                        if node.hasOnlyPositionalArguments():
                            return variable.getName()


    def onNodeWasReplaced( self, old_node ):
        assert old_node.isExpressionFunctionCall

        called = old_node.getCalledExpression()

        assert called.isExpressionVariableRef()
        variable = called.getVariable()

        owner = variable.getOwner()

        owner.reconsiderVariable( variable )

        if owner.isExpressionFunctionBody():
            self.signalChange(
                "var_usage",
                owner.getSourceReference(),
                message = "Reduced variable '%s' usage of function %s." % ( variable.getName(), owner )
            )

    def dir_extractor( self, node ):
        # Only treat the empty dir() call, leave the others alone for now.
        if not node.isEmptyCall():
            return None

        return Nodes.CPythonExpressionBuiltinDir(
            source_ref = node.getSourceReference()
        )

    def vars_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 0:
            return Nodes.CPythonExpressionBuiltinLocals(
                source_ref = node.getSourceReference()
            )
        elif len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinVars(
                source     = positional_args[ 0 ],
                source_ref = node.getSourceReference()
            )
        else:
            assert False

    def eval_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        return Nodes.CPythonExpressionBuiltinEval(
            source_code  = positional_args[0],
            globals_arg  = positional_args[1] if len( positional_args ) > 1 else None,
            locals_arg   = positional_args[2] if len( positional_args ) > 2 else None,
            source_ref   = node.getSourceReference()
        )

    def execfile_extractor( self, node ):
        assert node.parent.isStatementExpressionOnly()

        positional_args = node.getPositionalArguments()

        source_ref = node.getSourceReference()

        source_node = Nodes.CPythonExpressionFunctionCall(
            called_expression = Nodes.CPythonExpressionAttributeLookup(
                expression     = Nodes.CPythonExpressionBuiltinOpen(
                    filename   = positional_args[0],
                    mode       = Nodes.makeConstantReplacementNode(
                        constant = "rU",
                        node     = node
                    ),
                    buffering  = None,
                    source_ref = source_ref
                ),
                attribute_name = "read",
                source_ref     = source_ref
            ),
            positional_args   = (),
            pairs             = (),
            list_star_arg     = None,
            dict_star_arg     = None,
            source_ref        = source_ref
        )

        return Nodes.CPythonStatementExec(
            source_code  = source_node,
            globals_arg  = positional_args[1] if len( positional_args ) > 1 else None,
            locals_arg   = positional_args[2] if len( positional_args ) > 2 else None,
            source_ref   = source_ref
        )

    def import_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1 and positional_args[0].isExpressionConstantRef():
            module_name = positional_args[0].getConstant()
            source_ref = node.getSourceReference()

            if type( module_name ) is str and "." not in module_name:
                _module_package, module_name, _module_filename = Importing.findModule(
                    module_name    = module_name,
                    parent_package = node.getParentModule().getPackage(),
                    level          = 0 if source_ref.getFutureSpec().isAbsoluteImport() else 1
                )

                return Nodes.CPythonExpressionBuiltinImport(
                    module_name = module_name,
                    source_ref  = source_ref
                )
    def type_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinType1(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
            )
        elif len( positional_args ) == 3:
            return Nodes.CPythonExpressionBuiltinType3(
                type_name  = positional_args[0],
                bases      = positional_args[1],
                type_dict  = positional_args[2],
                source_ref = node.getSourceReference()
            )

    def _extractBuiltinArgs( self, node, builtin_spec, builtin_class ):
        # TODO: These could be handled too.
        if node.getStarListArg() is not None or node.getStarDictArg() is not None:
            return

        try:
            args = builtin_spec.matchCallSpec(
                name      = builtin_spec.getName(),
                call_spec = node
            )

            # Using list reference for passing the arguments without names, pylint: disable=W0142
            return builtin_class(
                *args,
                source_ref = node.getSourceReference()
            )
        except TooManyArguments, e:
            return Nodes.CPythonExpressionFunctionCall(
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

    def dict_extractor( self, node ):
        # The dict is a bit strange in that it accepts a position parameter, or not, but
        # won't have a default.

        def wrapExpressionBuiltinDictCreation( positional_args, pairs, source_ref ):
            if len( positional_args ) > 1:
                return Nodes.CPythonExpressionFunctionCall(
                    called_expression = makeRaiseExceptionReplacementExpressionFromInstance(
                        expression     = node,
                        exception      = TypeError( "dict expected at most 1 arguments, got %d" % len( positional_args ) )
                    ),
                    positional_args   = positional_args,
                    list_star_arg     = None,
                    dict_star_arg     = None,
                    pairs             = pairs,
                    source_ref        = source_ref
                )

            return Nodes.CPythonExpressionBuiltinDict(
                pos_arg    = positional_args[0] if positional_args else None,
                pairs      = pairs,
                source_ref = node.getSourceReference()
            )


        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = wrapExpressionBuiltinDictCreation,
            builtin_spec  = builtin_dict_spec
        )

    def chr_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinChr,
            builtin_spec  = builtin_chr_spec
        )

    def ord_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinOrd,
            builtin_spec  = builtin_ord_spec
        )

    def range_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinRange,
            builtin_spec  = builtin_range_spec
        )

    def len_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinLen,
            builtin_spec  = builtin_len_spec
        )

    def tuple_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinTuple,
            builtin_spec  = builtin_tuple_spec
        )

    def list_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinList,
            builtin_spec  = builtin_list_spec
        )

    def float_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinFloat,
            builtin_spec  = builtin_float_spec
        )

    def str_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinStr,
            builtin_spec  = builtin_str_spec
        )

    def bool_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinBool,
            builtin_spec  = builtin_bool_spec
        )

    def int_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinInt,
            builtin_spec  = builtin_int_spec
        )

    def long_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinLong,
            builtin_spec  = builtin_long_spec
        )

    def _pickLocalsForNode( self, node ):
        """ Pick a locals default for the given node. """

        provider = node.getParentVariableProvider()

        if provider.isModule():
            return Nodes.CPythonExpressionBuiltinGlobals(
                source_ref = node.getSourceReference()
            )
        else:
            return Nodes.CPythonExpressionBuiltinLocals(
                source_ref = node.getSourceReference()
            )

    def _pickGlobalsForNode( self, node ):
        """ Pick a globals default for the given node. """

        return Nodes.CPythonExpressionBuiltinGlobals(
            source_ref = node.getSourceReference()
        )

    def globals_extractor( self, node ):
        assert node.isEmptyCall()

        return self._pickGlobalsForNode( node )

    def locals_extractor( self, node ):
        assert node.isEmptyCall()

        return self._pickLocalsForNode( node )

class PrecomputeBuiltinsVisitor( OptimizationDispatchingVisitorBase ):
    """ Precompute builtins with constant arguments if possible. """
    # Many methods of this class could be functions, but we want it scoped on the class
    # level anyway. pylint: disable=R0201

    def __init__( self ):
        OptimizationDispatchingVisitorBase.__init__(
            self,
            dispatch_dict = {
#                "globals"    : self.globals_extractor,
#                "locals"     : self.locals_extractor,
#                "dir"        : self.dir_extractor,
#                "vars"       : self.vars_extractor,
                "chr"        : self.chr_extractor,
                "ord"        : self.ord_extractor,
                "type1"      : self.type1_extractor,
                "range"      : self.range_extractor,
                "len"        : self.len_extractor,
                "tuple"      : self.tuple_extractor,
                "list"       : self.list_extractor,
                "dict"       : self.dict_extractor,
                "float"      : self.float_extractor,
                "str"        : self.str_extractor,
                "bool"       : self.bool_extractor,
                "int"        : self.int_extractor,
                "long"       : self.long_extractor
            }
        )

    def getKey( self, node ):
        if node.isExpressionBuiltin():
            return node.kind.replace( "EXPRESSION_BUILTIN_", "" ).lower()

    def type1_extractor( self, node ):
        value = node.getValue()

        if value.isExpressionConstantRef():
            value = value.getConstant()

            if value is not None:
                type_name = value.__class__.__name__

                assert (type_name in _builtin_names), (type_name, _builtin_names)

                result = Nodes.CPythonExpressionVariableRef(
                    variable_name = type_name,
                    source_ref    = node.getSourceReference()
                )

                result.setVariable(
                    variable = node.getParentModule().getVariableForReference(
                        variable_name = type_name
                    )
                )

                self.signalChange(
                    "new_variable",
                    node.getSourceReference(),
                    message = "Replaced predictable type lookup with result '%s'." % type_name
                )

                return result


    def range_extractor( self, node ):
        # Quite a lot of checks to do. pylint: disable=R0912

        low  = node.getLow()
        high = node.getHigh()
        step = node.getStep()

        def isRangePredictable( node ):
            if node.isExpressionConstantRef():
                return node.isNumberConstant()
            else:
                return False

        if high is None and step is None:
            if isRangePredictable( low ):
                constant = low.getConstant()

                # Avoid warnings before Python 2.7, in Python 2.7 it's an exception.
                if type( constant ) is float and getPythonVersion() < 270:
                    constant = int( constant )

                # Negative values are empty, so don't check against 0.
                if constant <= 256:
                    return getConstantComputationReplacementNode(
                        expression = node,
                        computation = lambda : range( constant )
                    )
        elif step is None:
            if isRangePredictable( low ) and isRangePredictable( high ):
                constant1 = low.getConstant()
                constant2 = high.getConstant()

                if type( constant1 ) is float and getPythonVersion() < 270:
                    constant1 = int( constant1 )
                if type( constant2 ) is float and getPythonVersion() < 270:
                    constant2 = int( constant2 )

                if constant2 - constant1 <= 256:
                    return getConstantComputationReplacementNode(
                        expression = node,
                        computation = lambda : range( constant1, constant2 )
                    )
        else:
            if isRangePredictable( low ) and isRangePredictable( high ) and isRangePredictable( step ):
                constant1 = low.getConstant()
                constant2 = high.getConstant()
                constant3 = step.getConstant()

                if type( constant1 ) is float and getPythonVersion() < 270:
                    constant1 = int( constant1 )
                if type( constant2 ) is float and getPythonVersion() < 270:
                    constant2 = int( constant2 )
                if type( constant3 ) is float and getPythonVersion() < 270:
                    constant3 = int( constant3 )

                try:
                    if constant1 < constant2:
                        if constant3 < 0:
                            estimate = 0
                        else:
                            estimate = math.ceil( float( constant2 - constant1 ) / constant3 )
                    else:
                        if constant3 > 0:
                            estimate = 0
                        else:
                            estimate = math.ceil( float( constant2 - constant1 ) / constant3 )
                except (ValueError, TypeError, ZeroDivisionError):
                    estimate = -1

                estimate = round( estimate )

                if estimate <= 256:
                    try:
                        assert len( range( constant1, constant2, constant3 ) ) == estimate, node.getSourceReference()
                    except (ValueError, TypeError, ZeroDivisionError):
                        pass

                    return getConstantComputationReplacementNode(
                        expression = node,
                        computation = lambda : range( constant1, constant2, constant3 )
                    )


    def _extractConstantBuiltinCall( self, node, builtin_spec, given_values ):
        def isValueListConstant( values ):
            for sub_value in values:
                if sub_value.isExpressionKeyValuePair():
                    if not sub_value.getKey().isExpressionConstantRef():
                        return False
                    if not sub_value.getValue().isExpressionConstantRef():
                        return False
                elif not sub_value.isExpressionConstantRef():
                    return False

            return True

        for value in given_values:
            if value:
                if type( value ) in ( list, tuple ):
                    if not isValueListConstant( value ):
                        break
                elif not value.isExpressionConstantRef():
                    break
        else:
            return getConstantComputationReplacementNode(
                expression  = node,
                computation = lambda : builtin_spec.simulateCall( given_values )
            )

    def dict_extractor( self, node ):
        pos_arg = node.getPositionalArgument()

        if pos_arg is not None:
            pos_args = ( pos_arg, )
        else:
            pos_args = None

        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_dict_spec,
            given_values = ( pos_args, node.getNamedArgumentPairs() )
        )

    def chr_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_chr_spec,
            given_values = ( node.getValue(), )
        )

    def ord_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_ord_spec,
            given_values = ( node.getValue(), )
        )

    def len_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_len_spec,
            given_values = ( node.getValue(), )
        )

    def tuple_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_tuple_spec,
            given_values = ( node.getValue(), )
        )

    def list_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_list_spec,
            given_values = ( node.getValue(), )
        )

    def float_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_float_spec,
            given_values = ( node.getValue(), )
        )

    def str_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_str_spec,
            given_values = ( node.getValue(), )
        )


    def bool_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_bool_spec,
            given_values = ( node.getValue(), )
        )

    def int_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_int_spec,
            given_values = ( node.getValue(), node.getBase() )
        )


    def long_extractor( self, node ):
        return self._extractConstantBuiltinCall(
            node         = node,
            builtin_spec = builtin_long_spec,
            given_values = ( node.getValue(), node.getBase() )
        )
