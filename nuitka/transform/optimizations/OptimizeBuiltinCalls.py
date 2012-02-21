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
""" Optimize calls to builtins reference builtin nodes.

This works via the call registry. For builtin name references, we check if it's one of the
supported builtin types.
"""

from .registry import CallRegistry

from nuitka.nodes.BuiltinIteratorNodes import (
    CPythonExpressionBuiltinNext1,
    CPythonExpressionBuiltinNext2,
    CPythonExpressionBuiltinIter1,
    CPythonExpressionBuiltinIter2,
    CPythonExpressionBuiltinLen
)
from nuitka.nodes.BuiltinTypeNodes import (
#    CPythonExpressionBuiltinUnicode, TODO: Missing from here actually
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
    CPythonExpressionBuiltinOrd
)
from nuitka.nodes.ExecEvalNodes import (
    CPythonExpressionBuiltinEval,
    CPythonExpressionBuiltinExec,
    CPythonExpressionBuiltinExecfile,
    CPythonStatementExec
)
from nuitka.nodes.GlobalsLocalsNodes import (
    CPythonExpressionBuiltinGlobals,
    CPythonExpressionBuiltinLocals,
    CPythonExpressionBuiltinDir0
)
from nuitka.nodes.BuiltinReferenceNodes import (
    CPythonExpressionBuiltinExceptionRef,
    CPythonExpressionBuiltinRef
)
from nuitka.nodes.OperatorNodes import CPythonExpressionOperationUnary
from nuitka.nodes.ConstantRefNode import CPythonExpressionConstantRef
from nuitka.nodes.BuiltinDictNode import CPythonExpressionBuiltinDict
from nuitka.nodes.BuiltinOpenNode import CPythonExpressionBuiltinOpen
from nuitka.nodes.BuiltinRangeNode import CPythonExpressionBuiltinRange
from nuitka.nodes.BuiltinVarsNode import CPythonExpressionBuiltinVars
from nuitka.nodes.ImportNodes import CPythonExpressionBuiltinImport
from nuitka.nodes.TypeNode import CPythonExpressionBuiltinType1
from nuitka.nodes.ClassNodes import CPythonExpressionBuiltinType3
from nuitka.nodes.CallNode import CPythonExpressionFunctionCall
from nuitka.nodes.AttributeNode import CPythonExpressionAttributeLookup

from nuitka.nodes.NodeMakingHelpers import (
    makeRaiseExceptionReplacementExpressionFromInstance,
)


from nuitka.transform.optimizations import BuiltinOptimization

from nuitka.Utils import getPythonVersion

def dir_extractor( node ):
    # Only treat the empty dir() call, leave the others alone for now.
    if not node.isEmptyCall():
        return None

    return CPythonExpressionBuiltinDir0(
        source_ref = node.getSourceReference()
    )

def vars_extractor( node ):
    positional_args = node.getPositionalArguments()

    if len( positional_args ) == 0:
        if node.getParentVariableProvider().isModule():
            return CPythonExpressionBuiltinGlobals(
                source_ref = node.getSourceReference()
            )
        else:
            return CPythonExpressionBuiltinLocals(
                source_ref = node.getSourceReference()
            )
    elif len( positional_args ) == 1:
        return CPythonExpressionBuiltinVars(
            source     = positional_args[ 0 ],
            source_ref = node.getSourceReference()
        )
    else:
        assert False

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

    def wrapExpressionBuiltinDictCreation( positional_args, pairs, source_ref ):
        if len( positional_args ) > 1:
            return CPythonExpressionFunctionCall(
                called_expression = makeRaiseExceptionReplacementExpressionFromInstance(
                    expression     = node,
                    exception      = TypeError(
                        "dict expected at most 1 arguments, got %d" % len( positional_args )
                    )
                ),
                positional_args   = positional_args,
                list_star_arg     = None,
                dict_star_arg     = None,
                pairs             = pairs,
                source_ref        = source_ref
            )

        return CPythonExpressionBuiltinDict(
            pos_arg    = positional_args[0] if positional_args else None,
            pairs      = pairs,
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
        node          = node,
        builtin_class = CPythonExpressionBuiltinOrd,
        builtin_spec  = BuiltinOptimization.builtin_ord_spec
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
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = CPythonExpressionBuiltinRange,
        builtin_spec  = BuiltinOptimization.builtin_range_spec
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

if getPythonVersion() < 300:
    from nuitka.nodes.BuiltinTypeNodes import CPythonExpressionBuiltinLong

    def long_extractor( node ):
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = CPythonExpressionBuiltinLong,
            builtin_spec  = BuiltinOptimization.builtin_long_spec
        )

def globals_extractor( node ):
    assert node.isEmptyCall()

    return CPythonExpressionBuiltinGlobals(
        source_ref = node.getSourceReference()
    )

def locals_extractor( node ):
    assert node.isEmptyCall()

    # Note: Locals on the module level is really globals.
    provider = node.getParentVariableProvider()

    if provider.isModule():
        return CPythonExpressionBuiltinGlobals(
            source_ref = node.getSourceReference()
        )
    else:
        return CPythonExpressionBuiltinLocals(
            source_ref = node.getSourceReference()
        )


def execfile_extractor( node ):
    def wrapExpressionBuiltinExecfileCreation( filename, globals_arg, locals_arg, source_ref ):

        if node.getParentVariableProvider().isExpressionClassBody():
            # In a case, the copy-back must be done and will only be done correctly by
            # the code for exec statements.

            use_call = CPythonStatementExec
        else:
            use_call = CPythonExpressionBuiltinExecfile

        return use_call(
            source_code = CPythonExpressionFunctionCall(
                called_expression = CPythonExpressionAttributeLookup(
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
                positional_args  = (),
                pairs            = (),
                list_star_arg    = None,
                dict_star_arg    = None,
                source_ref       = source_ref
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

_dispatch_dict = {
    "globals"    : globals_extractor,
    "locals"     : locals_extractor,
    "eval"       : eval_extractor,
    "exec"       : exec_extractor,
    "execfile"   : execfile_extractor,
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
    "open"       : open_extractor
}

if getPythonVersion() < 300:
    _dispatch_dict[ "long" ] = long_extractor


def computeBuiltinCall( call_node, called ):
    builtin_name = called.getBuiltinName()

    if builtin_name in _dispatch_dict:
        new_node = _dispatch_dict[ builtin_name ]( call_node )

        if new_node is None:
            return call_node, None, None

            # TODO: Actually returning None should not be allowed at this point.
            raise AssertionError( "None is not allowed to return", _dispatch_dict[ builtin_name ] )

        return new_node, "new_builtin", "Detected builtin call %s" % builtin_name
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
