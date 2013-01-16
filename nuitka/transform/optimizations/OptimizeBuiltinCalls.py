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
""" Optimize calls to builtins reference builtin nodes.

For builtin name references, we check if it's one of the supported builtin types.
"""

from nuitka.Utils import python_version

from nuitka.nodes.BuiltinIteratorNodes import (
    CPythonExpressionBuiltinNext1,
    CPythonExpressionBuiltinNext2,
    CPythonExpressionBuiltinIter1,
    CPythonExpressionBuiltinIter2,
    CPythonExpressionBuiltinLen
)
from nuitka.nodes.BuiltinTypeNodes import (
    CPythonExpressionBuiltinFloat,
    CPythonExpressionBuiltinTuple,
    CPythonExpressionBuiltinList,
    CPythonExpressionBuiltinBool,
    CPythonExpressionBuiltinInt,
    CPythonExpressionBuiltinStr,
)
from nuitka.nodes.BuiltinFormatNodes import (
    CPythonExpressionBuiltinBin,
    CPythonExpressionBuiltinOct,
    CPythonExpressionBuiltinHex,
)
from nuitka.nodes.BuiltinDecodingNodes import (
    CPythonExpressionBuiltinChr,
    CPythonExpressionBuiltinOrd,
    CPythonExpressionBuiltinOrd0
)
from nuitka.nodes.ExecEvalNodes import (
    CPythonExpressionBuiltinEval,
    CPythonStatementExec
)

from nuitka.nodes.VariableRefNode import CPythonExpressionVariableRef

from nuitka.nodes.GlobalsLocalsNodes import (
    CPythonExpressionBuiltinGlobals,
    CPythonExpressionBuiltinLocals,
    CPythonExpressionBuiltinDir0,
    CPythonExpressionBuiltinDir1
)
from nuitka.nodes.OperatorNodes import CPythonExpressionOperationUnary
from nuitka.nodes.ConstantRefNode import CPythonExpressionConstantRef
from nuitka.nodes.BuiltinDictNode import CPythonExpressionBuiltinDict
from nuitka.nodes.BuiltinOpenNode import CPythonExpressionBuiltinOpen
from nuitka.nodes.BuiltinRangeNode import (
    CPythonExpressionBuiltinRange0,
    CPythonExpressionBuiltinRange1,
    CPythonExpressionBuiltinRange2,
    CPythonExpressionBuiltinRange3
)

from nuitka.nodes.BuiltinVarsNode import CPythonExpressionBuiltinVars
from nuitka.nodes.ImportNodes import CPythonExpressionBuiltinImport
from nuitka.nodes.TypeNode import (
    CPythonExpressionBuiltinSuper,
    CPythonExpressionBuiltinType1,
    CPythonExpressionBuiltinIsinstance
)
from nuitka.nodes.ClassNodes import CPythonExpressionBuiltinType3
from nuitka.nodes.CallNode import CPythonExpressionCallEmpty
from nuitka.nodes.AttributeNodes import (
    CPythonExpressionAttributeLookup,
    CPythonExpressionBuiltinGetattr,
    CPythonExpressionBuiltinSetattr,
    CPythonExpressionBuiltinHasattr
)

from nuitka.transform.optimizations import BuiltinOptimization

def dir_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node                = node,
        builtin_class       = CPythonExpressionBuiltinDir1,
        builtin_spec        = BuiltinOptimization.builtin_dir_spec,
        empty_special_class = CPythonExpressionBuiltinDir0
    )

def vars_extractor( node ):
    def selectVarsEmptyClass( source_ref ):
        if node.getParentVariableProvider().isModule():
            return CPythonExpressionBuiltinGlobals(
                source_ref = node.getSourceReference()
            )
        else:
            return CPythonExpressionBuiltinLocals(
                source_ref = node.getSourceReference()
            )
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class       = CPythonExpressionBuiltinVars,
        builtin_spec        = BuiltinOptimization.builtin_vars_spec,
        empty_special_class = selectVarsEmptyClass
    )

def import_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinImport,
        builtin_spec  = BuiltinOptimization.builtin_import_spec
    )

def type_extractor( node ):
    args = node.getCallArgs()
    length = args.getIterationLength( None )

    if length == 1:
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinType1,
            builtin_spec  = BuiltinOptimization.builtin_type1_spec
        )

    else:
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinType3,
            builtin_spec  = BuiltinOptimization.builtin_type3_spec
        )

def iter_extractor( node ):
    # Note: Iter in fact names its first argument if the default applies "collection", but
    # it won't matter much, fixed up in a wrapper.
    def wrapIterCreation( callable, sentinel, source_ref ):
        if sentinel is None:
            return CPythonExpressionBuiltinIter1(
                value      = callable,
                source_ref = source_ref
            )
        else:
            return CPythonExpressionBuiltinIter2(
                callable   = callable,
                sentinel   = sentinel,
                source_ref = source_ref
            )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = wrapIterCreation,
        builtin_spec  = BuiltinOptimization.builtin_iter_spec
    )


def next_extractor( node ):

    # Split up next with and without defaults, they are not going to behave really very
    # similar.
    def selectNextBuiltinClass( iterator, default, source_ref ):
        if default is None:
            return CPythonExpressionBuiltinNext1(
                value      = iterator,
                source_ref = node.getSourceReference()
            )
        else:
            return CPythonExpressionBuiltinNext2(
                iterator   = iterator,
                default    = default,
                source_ref = node.getSourceReference()
            )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = selectNextBuiltinClass,
        builtin_spec  = BuiltinOptimization.builtin_iter_spec
    )


def dict_extractor( node ):
    # The dict is a bit strange in that it accepts a position parameter, or not, but
    # won't have a default.

    def wrapExpressionBuiltinDictCreation( positional_args, dict_star_arg, source_ref ):
        if len( positional_args ) > 1:
            from nuitka.nodes.NodeMakingHelpers import (
                makeRaiseExceptionReplacementExpressionFromInstance,
                wrapExpressionWithSideEffects
            )

            result = makeRaiseExceptionReplacementExpressionFromInstance(
                expression     = node,
                exception      = TypeError(
                    "dict expected at most 1 arguments, got %d" % len( positional_args )
                )
            )

            result = wrapExpressionWithSideEffects(
                side_effects = positional_args,
                old_node     = node,
                new_node     = result
            )

            if dict_star_arg:
                result = wrapExpressionWithSideEffects(
                    side_effects = dict_star_arg,
                    old_node     = node,
                    new_node     = result
                )

            return result

        return CPythonExpressionBuiltinDict(
            pos_arg    = positional_args[0] if positional_args else None,
            pairs      = dict_star_arg,
            source_ref = node.getSourceReference()
        )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = wrapExpressionBuiltinDictCreation,
        builtin_spec  = BuiltinOptimization.builtin_dict_spec
    )

def chr_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinChr,
        builtin_spec  = BuiltinOptimization.builtin_chr_spec
    )

def ord_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node                = node,
        builtin_class       = CPythonExpressionBuiltinOrd,
        builtin_spec        = BuiltinOptimization.builtin_ord_spec,
        empty_special_class = CPythonExpressionBuiltinOrd0
    )

def bin_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinBin,
        builtin_spec  = BuiltinOptimization.builtin_bin_spec
    )

def oct_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinOct,
        builtin_spec  = BuiltinOptimization.builtin_oct_spec
    )

def hex_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinHex,
        builtin_spec  = BuiltinOptimization.builtin_hex_spec
    )

def repr_extractor( node ):
    def makeReprOperator( operand, source_ref ):
        return CPythonExpressionOperationUnary(
            operator   = "Repr",
            operand    = operand,
            source_ref = source_ref
        )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = makeReprOperator,
        builtin_spec  = BuiltinOptimization.builtin_repr_spec
    )

def range_extractor( node ):
    def selectRangeBuiltin( low, high, step, source_ref ):
        if high is None:
            return CPythonExpressionBuiltinRange1( low, source_ref )
        elif step is None:
            return CPythonExpressionBuiltinRange2( low, high, source_ref )
        else:
            return CPythonExpressionBuiltinRange3( low, high, step, source_ref )

    return BuiltinOptimization.extractBuiltinArgs(
        node                = node,
        builtin_class       = selectRangeBuiltin,
        builtin_spec        = BuiltinOptimization.builtin_range_spec,
        empty_special_class = CPythonExpressionBuiltinRange0
    )

def len_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinLen,
        builtin_spec  = BuiltinOptimization.builtin_len_spec
    )

def tuple_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinTuple,
        builtin_spec  = BuiltinOptimization.builtin_tuple_spec
    )

def list_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinList,
        builtin_spec  = BuiltinOptimization.builtin_list_spec
    )

def float_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinFloat,
        builtin_spec  = BuiltinOptimization.builtin_float_spec
    )

def str_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinStr,
        builtin_spec  = BuiltinOptimization.builtin_str_spec
    )

if python_version < 300:
    from nuitka.nodes.BuiltinTypeNodes import CPythonExpressionBuiltinUnicode

    def unicode_extractor( node ):
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinUnicode,
            builtin_spec  = BuiltinOptimization.builtin_unicode_spec
        )


def bool_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinBool,
        builtin_spec  = BuiltinOptimization.builtin_bool_spec
    )

def int_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinInt,
        builtin_spec  = BuiltinOptimization.builtin_int_spec
    )

if python_version < 300:
    from nuitka.nodes.BuiltinTypeNodes import CPythonExpressionBuiltinLong

    def long_extractor( node ):
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinLong,
            builtin_spec  = BuiltinOptimization.builtin_long_spec
        )

def globals_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinGlobals,
        builtin_spec  = BuiltinOptimization.builtin_globals_spec
    )

def locals_extractor( node ):
    # Note: Locals on the module level is really globals.
    provider = node.getParentVariableProvider()

    if provider.isModule():
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinGlobals,
            builtin_spec  = BuiltinOptimization.builtin_locals_spec
        )
    else:
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinLocals,
            builtin_spec  = BuiltinOptimization.builtin_locals_spec
        )

if python_version < 300:
    from nuitka.nodes.ExecEvalNodes import CPythonExpressionBuiltinExecfile

    def execfile_extractor( node ):
        def wrapExpressionBuiltinExecfileCreation( filename, globals_arg, locals_arg, source_ref ):

            provider = node.getParentVariableProvider()

            if provider.isExpressionFunctionBody() and provider.isClassDictCreation():
                # In a case, the copy-back must be done and will only be done correctly by
                # the code for exec statements.

                use_call = CPythonStatementExec
            else:
                use_call = CPythonExpressionBuiltinExecfile

            if provider.isExpressionFunctionBody():
                provider.markAsExecContaining()

            return use_call(
                source_code = CPythonExpressionCallEmpty(
                    called     = CPythonExpressionAttributeLookup(
                        expression     = CPythonExpressionBuiltinOpen(
                            filename   = filename,
                            mode       = CPythonExpressionConstantRef(
                                constant   = "rU",
                                source_ref = source_ref
                            ),
                            buffering  = None,
                            source_ref = source_ref
                        ),
                        attribute_name = "read",
                        source_ref     = source_ref
                    ),
                    source_ref = source_ref
                ),
                globals_arg = globals_arg,
                locals_arg  = locals_arg,
                source_ref  = source_ref
            )

        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = wrapExpressionBuiltinExecfileCreation,
            builtin_spec  = BuiltinOptimization.builtin_execfile_spec
        )

def eval_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinEval,
        builtin_spec  = BuiltinOptimization.builtin_eval_spec
    )


if python_version >= 300:
    from nuitka.nodes.ExecEvalNodes import CPythonExpressionBuiltinExec

    def exec_extractor( node ):
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinExec,
            builtin_spec  = BuiltinOptimization.builtin_eval_spec
        )

def open_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinOpen,
        builtin_spec  = BuiltinOptimization.builtin_open_spec
    )

def super_extractor( node ):
    # Need to accept type and object as keyword argument, that is just the API of super,
    # pylint: disable=W0622
    def wrapSuperBuiltin( type, object, source_ref ):
        if type is None and python_version >= 300:
            provider = node.getParentVariableProvider()

            type = CPythonExpressionVariableRef(
                variable_name = "__class__",
                source_ref    = source_ref
            )

            # Ought to be already closure taken.
            type.setVariable(
                provider.getVariableForReference(
                    variable_name = "__class__"
                )
            )

            from nuitka.nodes.NodeMakingHelpers import makeRaiseExceptionReplacementExpression

            if not type.getVariable().isClosureReference():
                return makeRaiseExceptionReplacementExpression(
                    expression      = node,
                    exception_type  = "SystemError",
                    exception_value = "super(): __class__ cell not found",
                )

            if object is None and provider.getParameters().getArgumentCount() > 0:
                par1_name = provider.getParameters().getArgumentNames()[0]
                # TODO: Nested first argument would kill us here, need a test for that.

                object = CPythonExpressionVariableRef(
                    variable_name = par1_name,
                    source_ref    = source_ref
                )

                object.setVariable(
                    node.getParentVariableProvider().getVariableForReference(
                        variable_name = par1_name
                    )
                )

                if not object.getVariable().isParameterVariable():
                    return makeRaiseExceptionReplacementExpression(
                        expression      = node,
                        exception_type  = "SystemError",
                        exception_value = "super(): __class__ cell not found",
                    )


        return CPythonExpressionBuiltinSuper(
            super_type   = type,
            super_object = object,
            source_ref   = source_ref
        )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = wrapSuperBuiltin,
        builtin_spec  = BuiltinOptimization.builtin_super_spec
    )

def hasattr_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinHasattr,
        builtin_spec  = BuiltinOptimization.builtin_hasattr_spec
    )

def getattr_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinGetattr,
        builtin_spec  = BuiltinOptimization.builtin_getattr_spec
    )

def setattr_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinSetattr,
        builtin_spec  = BuiltinOptimization.builtin_setattr_spec
    )

def isinstance_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinIsinstance,
        builtin_spec  = BuiltinOptimization.builtin_isinstance_spec
    )

_dispatch_dict = {
    "globals"    : globals_extractor,
    "locals"     : locals_extractor,
    "eval"       : eval_extractor,
    "dir"        : dir_extractor,
    "vars"       : vars_extractor,
    "__import__" : import_extractor,
    "chr"        : chr_extractor,
    "ord"        : ord_extractor,
    "bin"        : bin_extractor,
    "oct"        : oct_extractor,
    "hex"        : hex_extractor,
    "type"       : type_extractor,
    "iter"       : iter_extractor,
    "next"       : next_extractor,
    "range"      : range_extractor,
    "tuple"      : tuple_extractor,
    "list"       : list_extractor,
    "dict"       : dict_extractor,
    "float"      : float_extractor,
    "str"        : str_extractor,
    "bool"       : bool_extractor,
    "int"        : int_extractor,
    "repr"       : repr_extractor,
    "len"        : len_extractor,
    "super"      : super_extractor,
    "hasattr"    : hasattr_extractor,
    "getattr"    : getattr_extractor,
    "setattr"    : setattr_extractor,
    "isinstance" : isinstance_extractor
}

if python_version < 300:
    _dispatch_dict[ "long" ] = long_extractor
    _dispatch_dict[ "unicode" ] = unicode_extractor
    _dispatch_dict[ "execfile" ] = execfile_extractor

    # The handling of 'open' built-in for Python3 is not yet correct.
    _dispatch_dict[ "open" ] = open_extractor
else:
    _dispatch_dict[ "exec" ] = exec_extractor

def check():
    from nuitka.Builtins import builtin_names

    for builtin_name in _dispatch_dict:
        assert builtin_name in builtin_names, builtin_name

check()

def computeBuiltinCall( call_node, called ):
    builtin_name = called.getBuiltinName()

    if builtin_name in _dispatch_dict:
        new_node = _dispatch_dict[ builtin_name ]( call_node )

        if new_node is None:
            return call_node, None, None

        inspect_node = new_node

        if inspect_node.isExpressionSideEffects():
            inspect_node = inspect_node.getExpression()

        if inspect_node.isExpressionBuiltinImport():
            tags    = "new_builtin new_import"
            message = "Replaced dynamic builtin import %s with static module import." % inspect_node.kind
        elif inspect_node.isExpressionBuiltin() or inspect_node.isStatementExec():
            tags = "new_builtin"
            message = "Replaced call to builtin with builtin call %s." % inspect_node.kind
        elif inspect_node.isExpressionRaiseException():
            tags = "new_raise"
            message = "Replaced call to builtin %s with exception raising call." % inspect_node.kind
        elif inspect_node.isExpressionOperationUnary():
            tags = "new_expression"
            message = "Replaced call to builtin %s with exception raising call." % inspect_node.kind
        else:
            assert False, ( builtin_name, "->", inspect_node )

        return new_node, tags, message
    else:
        # TODO: Consider giving warnings, whitelisted potentially
        return call_node, None, None
