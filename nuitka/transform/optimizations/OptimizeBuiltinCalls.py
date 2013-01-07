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

This works via the call registry. For builtin name references, we check if it's one of the
supported builtin types.
"""

from .registry import CallRegistry

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
from nuitka.nodes.BuiltinReferenceNodes import (
    CPythonExpressionBuiltinExceptionRef,
    CPythonExpressionBuiltinRef
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
)
from nuitka.nodes.ClassNodes import CPythonExpressionBuiltinType3
from nuitka.nodes.CallNode import CPythonExpressionCall
from nuitka.nodes.AttributeNodes import CPythonExpressionAttributeLookup

from nuitka.nodes.NodeMakingHelpers import (
    makeRaiseExceptionReplacementExpressionFromInstance,
    makeRaiseExceptionReplacementExpression
)


from nuitka.transform.optimizations import BuiltinOptimization

def dir_extractor( node ):
    # Only treat the empty dir() call, leave the others alone for now.
    if node.isEmptyCall():
        return CPythonExpressionBuiltinDir0(
            source_ref = node.getSourceReference()
        )
    else:
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinDir1,
            builtin_spec  = BuiltinOptimization.builtin_dir_spec
        )

def vars_extractor( node ):
    if node.isEmptyCall():
        if node.getParentVariableProvider().isModule():
            return CPythonExpressionBuiltinGlobals(
                source_ref = node.getSourceReference()
            )
        else:
            return CPythonExpressionBuiltinLocals(
                source_ref = node.getSourceReference()
            )
    else:
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinVars,
            builtin_spec  = BuiltinOptimization.builtin_vars_spec
        )

def import_extractor( node ):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinImport,
        builtin_spec  = BuiltinOptimization.builtin_import_spec
    )

def type_extractor( node ):
    positional_args = node.getPositionalArguments()

    if len( positional_args ) == 1:
        return CPythonExpressionBuiltinType1(
            value      = positional_args[0],
            source_ref = node.getSourceReference()
        )
    elif len( positional_args ) == 3:
        return CPythonExpressionBuiltinType3(
            type_name  = positional_args[0],
            bases      = positional_args[1],
            type_dict  = positional_args[2],
            source_ref = node.getSourceReference()
        )

def iter_extractor( node ):
    positional_args = node.getPositionalArguments()

    if len( positional_args ) == 1:
        return CPythonExpressionBuiltinIter1(
            value      = positional_args[0],
            source_ref = node.getSourceReference()
        )
    elif len( positional_args ) == 2:
        return CPythonExpressionBuiltinIter2(
            call_able  = positional_args[0],
            sentinel   = positional_args[1],
            source_ref = node.getSourceReference()
        )

def next_extractor( node ):
    positional_args = node.getPositionalArguments()

    if len( positional_args ) == 1:
        return CPythonExpressionBuiltinNext1(
            value      = positional_args[0],
            source_ref = node.getSourceReference()
        )
    else:
        return CPythonExpressionBuiltinNext2(
            iterator   = positional_args[0],
            default    = positional_args[1],
            source_ref = node.getSourceReference()
        )

def dict_extractor( node ):
    # The dict is a bit strange in that it accepts a position parameter, or not, but
    # won't have a default.

    def wrapExpressionBuiltinDictCreation( positional_args, dict_star_arg, source_ref ):
        if len( positional_args ) > 1:
            return CPythonExpressionCall(
                called          = makeRaiseExceptionReplacementExpressionFromInstance(
                    expression     = node,
                    exception      = TypeError(
                        "dict expected at most 1 arguments, got %d" % len( positional_args )
                    )
                ),
                positional_args = positional_args,
                list_star_arg   = None,
                dict_star_arg   = None,
                pairs           = dict_star_arg,
                source_ref      = source_ref
            )

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
        empty_special_class = CPythonExpressionBuiltinRange0,
        builtin_spec        = BuiltinOptimization.builtin_range_spec
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
                source_code = CPythonExpressionCall(
                    called          = CPythonExpressionAttributeLookup(
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
                    positional_args = (),
                    pairs           = (),
                    list_star_arg   = None,
                    dict_star_arg   = None,
                    source_ref      = source_ref
                ),
                globals_arg = globals_arg,
                locals_arg  = locals_arg,
                source_ref = source_ref
            )

        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = wrapExpressionBuiltinExecfileCreation,
            builtin_spec  = BuiltinOptimization.builtin_execfile_spec
        )

def eval_extractor( node ):
    # TODO: Should precompute error as well: TypeError: eval() takes no keyword arguments

    positional_args = node.getPositionalArguments()

    return CPythonExpressionBuiltinEval(
        source_code  = positional_args[0],
        globals_arg  = positional_args[1] if len( positional_args ) > 1 else None,
        locals_arg   = positional_args[2] if len( positional_args ) > 2 else None,
        source_ref   = node.getSourceReference()
    )

if python_version >= 300:
    from nuitka.nodes.ExecEvalNodes import CPythonExpressionBuiltinExec

    def exec_extractor( node ):
        # TODO: Should precompute error as well: TypeError: exec() takes no keyword arguments

        positional_args = node.getPositionalArguments()

        return CPythonExpressionBuiltinExec(
            source_code  = positional_args[0],
            globals_arg  = positional_args[1] if len( positional_args ) > 1 else None,
            locals_arg   = positional_args[2] if len( positional_args ) > 2 else None,
            source_ref   = node.getSourceReference()
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
    "super"      : super_extractor
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

        tags = set( [ "new_builtin" ] )

        if new_node.isExpressionBuiltinImport():
            tags    = "new_builtin new_import"
            message = "Replaced dynamic builtin import %s with static module import." % new_node.kind
        elif new_node.isExpressionBuiltin() or new_node.isStatementExec():
            tags = "new_builtin"
            message = "Replaced call to builtin with builtin call %s." % new_node.kind
        elif new_node.isExpressionCall() or new_node.isExpressionRaiseException():
            tags = "new_raise"
            message = "Replaced call to builtin %s with exception raising call." % new_node.kind
        elif new_node.isExpressionOperationUnary():
            tags = "new_expression"
            message = "Replaced call to builtin %s with exception raising call." % new_node.kind
        else:
            assert False

        return new_node, tags, message
    else:
        # TODO: Consider giving warnings, whitelisted potentially
        return call_node, None, None

from nuitka.nodes.ExceptionNodes import CPythonExpressionBuiltinMakeException

def computeBuiltinExceptionCall( call_node, called ):
    exception_name = called.getExceptionName()

    def createBuiltinMakeException( args, source_ref ):
        return CPythonExpressionBuiltinMakeException(
            exception_name = exception_name,
            args           = args,
            source_ref     = source_ref
        )

    new_node = BuiltinOptimization.extractBuiltinArgs(
        node          = call_node,
        builtin_class = createBuiltinMakeException,
        builtin_spec  = BuiltinOptimization.BuiltinParameterSpecExceptions(
            name          = exception_name,
            default_count = 0
        )
    )

    # TODO: Don't allow this to happen.
    if new_node is None:
        return call_node, None, None

    return new_node, "new_expression", "detected builtin exception making"


def register():
    CallRegistry.registerCallHandler(
        kind    = CPythonExpressionBuiltinRef.kind,
        handler = computeBuiltinCall
    )

    CallRegistry.registerCallHandler(
        kind    = CPythonExpressionBuiltinExceptionRef.kind,
        handler = computeBuiltinExceptionCall
    )
