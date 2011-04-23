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

import math

_builtin_names = [ str( x ) for x in __builtins__.keys() ]
assert "int" in _builtin_names, __builtins__.keys()

from nuitka.nodes.ParameterSpec import ParameterSpec, TooManyArguments

class BuiltinParameterSpec( ParameterSpec ):
    def __init__( self, name, arg_names, default_count ):
        self.name = name

        ParameterSpec.__init__(
            self,
            normal_args    = arg_names,
            list_star_arg  = None,
            dict_star_arg  = None,
            default_count  = default_count
        )

    def getName( self ):
        return self.name

builtin_int_spec = BuiltinParameterSpec( "int", ( "x", "base" ), 2 )
builtin_long_spec = BuiltinParameterSpec( "long", ( "x", "base" ), 2 )

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

    def globals_extractor( self, node ):
        assert node.isEmptyCall()

        return self._pickGlobalsForNode( node )

    def locals_extractor( self, node ):
        assert node.isEmptyCall()

        return self._pickLocalsForNode( node )

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
                expression = Nodes.CPythonExpressionBuiltinOpen(
                    filename   = positional_args[0],
                    mode       = Nodes.makeConstantReplacementNode(
                        constant = "rU",
                        node     = node
                    ),
                    buffering  = None,
                    source_ref = source_ref
                ),
                attribute = "read",
                source_ref = source_ref
            ),
            positional_args = (),
            named_args = (),
            list_star_arg = None,
            dict_star_arg = None,
            source_ref    = source_ref
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

    def chr_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinChr(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
            )


    def ord_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinOrd(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
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

    def range_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) >= 1 and len( positional_args ) <= 3:
            low = positional_args[0]
            high = positional_args[1] if len( positional_args ) > 1 else None
            step = positional_args[2] if len( positional_args ) > 2 else None

            return Nodes.CPythonExpressionBuiltinRange(
                low        = low,
                high       = high,
                step       = step,
                source_ref = node.getSourceReference()
            )

    def len_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        if len( positional_args ) == 1:
            return Nodes.CPythonExpressionBuiltinLen(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
            )

    def tuple_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        positional_args_count = len( positional_args )

        if positional_args_count == 1:
            return Nodes.CPythonExpressionBuiltinTuple(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
            )
        elif positional_args_count == 0:
            return Nodes.makeConstantReplacementNode(
                node     = node,
                constant = ()
            )

    def list_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        positional_args_count = len( positional_args )

        if positional_args_count == 1:
            return Nodes.CPythonExpressionBuiltinList(
                value      = positional_args[0],
                source_ref = node.getSourceReference()
            )
        elif positional_args_count == 0:
            return Nodes.makeConstantReplacementNode(
                node     = node,
                constant = []
            )

    def dict_extractor( self, node ):
        positional_args = node.getPositionalArguments()

        # TODO: These could be handled too.
        if node.getStarListArg() is not None or node.getStarDictArg() is not None:
            return

        if len( positional_args ) <= 1:
            if positional_args:
                return Nodes.CPythonExpressionBuiltinDict(
                    pos_arg    = positional_args[0],
                    named_args = node.getNamedArguments(),
                    source_ref = node.getSourceReference()
                )
            else:
                named_args = node.getNamedArguments()

                if named_args:
                    return Nodes.CPythonExpressionBuiltinDict(
                        pos_arg    = None,
                        named_args = named_args,
                        source_ref = node.getSourceReference()
                    )
                else:
                    return Nodes.makeConstantReplacementNode(
                        node     = node,
                        constant = {}
                    )

    def _extractSingleArgBuiltin( self, node, arg_name, builtin_class, default ):
        positional_args = node.getPositionalArguments()

        # TODO: These could be handled too.
        if node.getStarListArg() is not None or node.getStarDictArg() is not None:
            return

        # TODO: These could be handled too
        arg_names = node.getNamedArgumentNames()

        if len( arg_names ) > 1 or ( len( arg_names ) == 1 and arg_names[0] != arg_name ):
            return

        named_arguments = node.getNamedArguments()

        if len( positional_args ) == 0:
            if not named_arguments:
                return Nodes.makeConstantReplacementNode(
                    node     = node,
                    constant = default
                )
            else:
                return builtin_class(
                    value      = named_arguments[0][1],
                    source_ref = node.getSourceReference()
                )
        elif len( positional_args ) == 1:
            if not named_arguments:
                return builtin_class(
                    value      = positional_args[0],
                    source_ref = node.getSourceReference()
                )

    def _extractBuiltinArgs( self, node, builtin_spec, builtin_class, default ):
        # TODO: These could be handled too.
        if node.getStarListArg() is not None or node.getStarDictArg() is not None:
            return

        try:
            args = builtin_spec.matchCallSpec( builtin_spec.getName(), node.getCallSpec() )

            if not args:
                return Nodes.makeConstantReplacementNode(
                    node     = node,
                    constant = default
                )
            else:
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
                named_args        = node.getNamedArguments(),
                source_ref        = node.getSourceReference()
            )


    def float_extractor( self, node ):
        return self._extractSingleArgBuiltin(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinFloat,
            arg_name      = "x",
            default       = 0.0
        )

    def str_extractor( self, node ):
        return self._extractSingleArgBuiltin(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinStr,
            arg_name      = "object",
            default       = ""
        )

    def bool_extractor( self, node ):
        return self._extractSingleArgBuiltin(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinBool,
            arg_name      = "x",
            default       = False
        )

    def int_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinInt,
            builtin_spec  = builtin_int_spec,
            default       = False
        )

    def long_extractor( self, node ):
        return self._extractBuiltinArgs(
            node          = node,
            builtin_class = Nodes.CPythonExpressionBuiltinLong,
            builtin_spec  = builtin_long_spec,
            default       = False
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

    def chr_extractor( self, node ):
        value = node.getValue()

        if value.isExpressionConstantRef():
            value = value.getConstant()

            return getConstantComputationReplacementNode(
                expression  = node,
                computation = lambda : chr( value )
            )

    def ord_extractor( self, node ):
        value = node.getValue()

        if value.isExpressionConstantRef():
            value = value.getConstant()

            return getConstantComputationReplacementNode(
                expression  = node,
                computation = lambda : ord( value )
            )

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

    def len_extractor( self, node ):
        value = node.getValue()

        if value.isExpressionConstantRef():
            return getConstantComputationReplacementNode(
                expression  = node,
                computation = lambda : len( value.getConstant() )
            )

    def tuple_extractor( self, node ):
        value = node.getValue()

        if value.isExpressionConstantRef():
            return getConstantComputationReplacementNode(
                expression  = node,
                computation = lambda : tuple( value.getConstant() )
            )

    def list_extractor( self, node ):
        value = node.getValue()

        if value.isExpressionConstantRef():
            return getConstantComputationReplacementNode(
                expression  = node,
                computation = lambda : list( value.getConstant() )
            )


    def dict_extractor( self, node ):
        pos_arg = node.getPositionalArgument()

        if pos_arg is None or pos_arg.isExpressionConstantRef():
            named_arguments = node.getNamedArguments()

            named_argument_names = []
            named_argument_values = []

            for named_argument_name, named_argument_value in named_arguments:
                if not named_argument_value.isExpressionConstantRef():
                    break

                named_argument_names.append( named_argument_name )
                named_argument_values.append( named_argument_value.getConstant() )
            else:
                arg_dict = dict.fromkeys( named_argument_names )

                for named_argument_name, named_argument_value in zip( named_argument_names, named_argument_values ):
                    arg_dict[ named_argument_name ] = named_argument_value

                if pos_arg is None:
                    return getConstantComputationReplacementNode(
                        expression  = node,
                        computation = lambda : dict( **arg_dict )
                    )
                else:
                    return getConstantComputationReplacementNode(
                        expression  = node,
                        computation = lambda : dict( pos_arg.getConstant(), **arg_dict )
                    )

    def float_extractor( self, node ):
        value = node.getValue()

        if value.isExpressionConstantRef():
            return getConstantComputationReplacementNode(
                expression  = node,
                computation = lambda : float( value.getConstant() )
            )

    def str_extractor( self, node ):
        value = node.getValue()

        if value.isExpressionConstantRef():
            return getConstantComputationReplacementNode(
                expression  = node,
                computation = lambda : str( value.getConstant() )
            )

    def bool_extractor( self, node ):
        value = node.getValue()

        if value.isExpressionConstantRef():
            return getConstantComputationReplacementNode(
                expression  = node,
                computation = lambda : bool( value.getConstant() )
            )


    def int_extractor( self, node ):
        value = node.getValue()

        if value is None or value.isExpressionConstantRef():
            base = node.getBase()

            if base is None:
                if value is None:
                    return Nodes.makeConstantReplacementNode(
                        node     = node,
                        constant = 0
                    )
                else:
                    return getConstantComputationReplacementNode(
                        expression  = node,
                        computation = lambda : int( value.getConstant() )
                    )
            elif base.isExpressionConstantRef():
                if value is None:
                    return getConstantComputationReplacementNode(
                        expression  = node,
                        computation = lambda : int( base = base.getConstant() )
                    )
                else:
                    return getConstantComputationReplacementNode(
                        expression  = node,
                        computation = lambda : int( value.getConstant(), base.getConstant() )
                    )

    def long_extractor( self, node ):
        value = node.getValue()

        if value is None or value.isExpressionConstantRef():
            base = node.getBase()

            if base is None:
                if value is None:
                    return Nodes.makeConstantReplacementNode(
                        node     = node,
                        constant = 0
                    )
                else:
                    return getConstantComputationReplacementNode(
                        expression  = node,
                        computation = lambda : long( value.getConstant() )
                    )
            elif base.isExpressionConstantRef():
                if value is None:
                    return getConstantComputationReplacementNode(
                        expression  = node,
                        computation = lambda : long( base = base.getConstant() )
                    )
                else:
                    return getConstantComputationReplacementNode(
                        expression  = node,
                        computation = lambda : long( value.getConstant(), base.getConstant() )
                    )
