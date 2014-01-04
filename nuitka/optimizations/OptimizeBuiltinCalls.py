#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

For builtin name references, we check if it's one of the supported builtin
types.
"""

from nuitka.Utils import python_version
from nuitka.Options import isDebug, shallMakeModule

from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionBuiltinNext1,
    ExpressionBuiltinNext2,
    ExpressionBuiltinIter1,
    ExpressionBuiltinIter2,
    ExpressionBuiltinLen
)
from nuitka.nodes.BuiltinTypeNodes import (
    ExpressionBuiltinFloat,
    ExpressionBuiltinTuple,
    ExpressionBuiltinList,
    ExpressionBuiltinBool,
    ExpressionBuiltinInt,
    ExpressionBuiltinStr,
    ExpressionBuiltinSet
)
from nuitka.nodes.BuiltinFormatNodes import (
    ExpressionBuiltinBin,
    ExpressionBuiltinOct,
    ExpressionBuiltinHex,
)
from nuitka.nodes.BuiltinDecodingNodes import (
    ExpressionBuiltinChr,
    ExpressionBuiltinOrd,
    ExpressionBuiltinOrd0
)
from nuitka.nodes.ExecEvalNodes import ExpressionBuiltinEval
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableRef
)
from nuitka.nodes.GlobalsLocalsNodes import (
    ExpressionBuiltinGlobals,
    ExpressionBuiltinLocals,
    ExpressionBuiltinDir0,
    ExpressionBuiltinDir1
)
from nuitka.nodes.OperatorNodes import ExpressionOperationUnary
from nuitka.nodes.ConstantRefNodes import ExpressionConstantRef
from nuitka.nodes.BuiltinDictNodes import ExpressionBuiltinDict
from nuitka.nodes.BuiltinOpenNodes import ExpressionBuiltinOpen
from nuitka.nodes.BuiltinRangeNodes import (
    ExpressionBuiltinRange0,
    ExpressionBuiltinRange1,
    ExpressionBuiltinRange2,
    ExpressionBuiltinRange3
)

from nuitka.nodes.BuiltinVarsNodes import ExpressionBuiltinVars
from nuitka.nodes.ImportNodes import ExpressionBuiltinImport
from nuitka.nodes.TypeNodes import (
    ExpressionBuiltinSuper,
    ExpressionBuiltinType1,
    ExpressionBuiltinIsinstance
)
from nuitka.nodes.ClassNodes import ExpressionBuiltinType3
from nuitka.nodes.CallNodes import ExpressionCallEmpty
from nuitka.nodes.AttributeNodes import (
    ExpressionAttributeLookup,
    ExpressionBuiltinGetattr,
    ExpressionBuiltinSetattr,
    ExpressionBuiltinHasattr
)
from nuitka.nodes.ConditionalNodes import ExpressionConditional
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs

from nuitka.tree.ReformulationExecStatements import wrapEvalGlobalsAndLocals

from . import BuiltinOptimization

def dir_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node                = node,
        builtin_class       = ExpressionBuiltinDir1,
        builtin_spec        = BuiltinOptimization.builtin_dir_spec,
        empty_special_class = ExpressionBuiltinDir0
    )

def vars_extractor(node):
    def selectVarsEmptyClass(source_ref):
        if node.getParentVariableProvider().isPythonModule():
            return ExpressionBuiltinGlobals(
                source_ref = source_ref
            )
        else:
            return ExpressionBuiltinLocals(
                source_ref = source_ref
            )
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class       = ExpressionBuiltinVars,
        builtin_spec        = BuiltinOptimization.builtin_vars_spec,
        empty_special_class = selectVarsEmptyClass
    )

def import_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinImport,
        builtin_spec  = BuiltinOptimization.builtin_import_spec
    )

def type_extractor(node):
    args = node.getCallArgs()
    length = args.getIterationLength()

    if length == 1:
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = ExpressionBuiltinType1,
            builtin_spec  = BuiltinOptimization.builtin_type1_spec
        )

    else:
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = ExpressionBuiltinType3,
            builtin_spec  = BuiltinOptimization.builtin_type3_spec
        )

def iter_extractor(node):
    # Note: Iter in fact names its first argument if the default applies
    # "collection", but it won't matter much, fixed up in a wrapper.  The
    # "callable" is part of the API, pylint: disable=W0622

    def wrapIterCreation(callable, sentinel, source_ref):
        if sentinel is None:
            return ExpressionBuiltinIter1(
                value      = callable,
                source_ref = source_ref
            )
        else:
            return ExpressionBuiltinIter2(
                callable   = callable,
                sentinel   = sentinel,
                source_ref = source_ref
            )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = wrapIterCreation,
        builtin_spec  = BuiltinOptimization.builtin_iter_spec
    )


def next_extractor(node):

    # Split up next with and without defaults, they are not going to behave
    # really very similar.
    def selectNextBuiltinClass(iterator, default, source_ref):
        if default is None:
            return ExpressionBuiltinNext1(
                value      = iterator,
                source_ref = source_ref
            )
        else:
            return ExpressionBuiltinNext2(
                iterator   = iterator,
                default    = default,
                source_ref = source_ref
            )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = selectNextBuiltinClass,
        builtin_spec  = BuiltinOptimization.builtin_iter_spec
    )


def dict_extractor(node):
    # The dict is a bit strange in that it accepts a position parameter, or not,
    # but won't have a default.

    def wrapExpressionBuiltinDictCreation( positional_args, dict_star_arg,
                                           source_ref ):
        if len( positional_args ) > 1:
            from nuitka.nodes.NodeMakingHelpers import (
                makeRaiseExceptionReplacementExpressionFromInstance,
                wrapExpressionWithSideEffects
            )

            result = makeRaiseExceptionReplacementExpressionFromInstance(
                expression     = node,
                exception      = TypeError(
                    "dict expected at most 1 arguments, got %d" % (
                        len( positional_args )
                    )
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

        return ExpressionBuiltinDict(
            pos_arg    = positional_args[0] if positional_args else None,
            pairs      = dict_star_arg,
            source_ref = source_ref
        )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = wrapExpressionBuiltinDictCreation,
        builtin_spec  = BuiltinOptimization.builtin_dict_spec
    )

def chr_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinChr,
        builtin_spec  = BuiltinOptimization.builtin_chr_spec
    )

def ord_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node                = node,
        builtin_class       = ExpressionBuiltinOrd,
        builtin_spec        = BuiltinOptimization.builtin_ord_spec,
        empty_special_class = ExpressionBuiltinOrd0
    )

def bin_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinBin,
        builtin_spec  = BuiltinOptimization.builtin_bin_spec
    )

def oct_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinOct,
        builtin_spec  = BuiltinOptimization.builtin_oct_spec
    )

def hex_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinHex,
        builtin_spec  = BuiltinOptimization.builtin_hex_spec
    )

def repr_extractor(node):
    def makeReprOperator(operand, source_ref):
        return ExpressionOperationUnary(
            operator   = "Repr",
            operand    = operand,
            source_ref = source_ref
        )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = makeReprOperator,
        builtin_spec  = BuiltinOptimization.builtin_repr_spec
    )

def range_extractor(node):
    def selectRangeBuiltin(low, high, step, source_ref):
        if high is None:
            return ExpressionBuiltinRange1( low, source_ref )
        elif step is None:
            return ExpressionBuiltinRange2( low, high, source_ref )
        else:
            return ExpressionBuiltinRange3( low, high, step, source_ref )

    return BuiltinOptimization.extractBuiltinArgs(
        node                = node,
        builtin_class       = selectRangeBuiltin,
        builtin_spec        = BuiltinOptimization.builtin_range_spec,
        empty_special_class = ExpressionBuiltinRange0
    )

if python_version < 300:
    from nuitka.nodes.BuiltinRangeNodes import ExpressionBuiltinXrange

    def xrange_extractor(node):
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = ExpressionBuiltinXrange,
            builtin_spec  = BuiltinOptimization.builtin_xrange_spec
    )


def len_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinLen,
        builtin_spec  = BuiltinOptimization.builtin_len_spec
    )

def tuple_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinTuple,
        builtin_spec  = BuiltinOptimization.builtin_tuple_spec
    )

def list_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinList,
        builtin_spec  = BuiltinOptimization.builtin_list_spec
    )

def set_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinSet,
        builtin_spec  = BuiltinOptimization.builtin_set_spec
    )

def float_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinFloat,
        builtin_spec  = BuiltinOptimization.builtin_float_spec
    )

def str_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinStr,
        builtin_spec  = BuiltinOptimization.builtin_str_spec
    )

if python_version < 300:
    from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinUnicode

    def unicode_extractor(node):
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = ExpressionBuiltinUnicode,
            builtin_spec  = BuiltinOptimization.builtin_unicode_spec
        )


def bool_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinBool,
        builtin_spec  = BuiltinOptimization.builtin_bool_spec
    )

def int_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinInt,
        builtin_spec  = BuiltinOptimization.builtin_int_spec
    )

if python_version < 300:
    from nuitka.nodes.BuiltinTypeNodes import ExpressionBuiltinLong

    def long_extractor(node):
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = ExpressionBuiltinLong,
            builtin_spec  = BuiltinOptimization.builtin_long_spec
        )

def globals_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinGlobals,
        builtin_spec  = BuiltinOptimization.builtin_globals_spec
    )

def locals_extractor(node):
    # Note: Locals on the module level is really globals.
    provider = node.getParentVariableProvider()

    if provider.isPythonModule():
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = ExpressionBuiltinGlobals,
            builtin_spec  = BuiltinOptimization.builtin_locals_spec
        )
    else:
        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = ExpressionBuiltinLocals,
            builtin_spec  = BuiltinOptimization.builtin_locals_spec
        )

if python_version < 300:
    from nuitka.nodes.ExecEvalNodes import ExpressionBuiltinExecfile

    def execfile_extractor(node):
        # Need to accept globals and local keyword argument, that is just the
        # API of execfile, pylint: disable=W0622

        def wrapExpressionBuiltinExecfileCreation( filename, globals, locals,
                                                   source_ref ):
            provider = node.getParentVariableProvider()

            # TODO: Can't really be true, can it?
            if provider.isExpressionFunctionBody():
                provider.markAsExecContaining()

                if provider.isClassDictCreation():
                    provider.markAsUnqualifiedExecContaining( source_ref )

            globals_wrap, locals_wrap = wrapEvalGlobalsAndLocals(
                provider     = provider,
                globals_node = globals,
                locals_node  = locals,
                exec_mode    = False,
                source_ref   = source_ref
            )

            return ExpressionBuiltinExecfile(
                source_code = ExpressionCallEmpty(
                    called     = ExpressionAttributeLookup(
                        expression     = ExpressionBuiltinOpen(
                            filename   = filename,
                            mode       = ExpressionConstantRef(
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
                globals_arg = globals_wrap,
                locals_arg  = locals_wrap,
                source_ref  = source_ref
            )

        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = wrapExpressionBuiltinExecfileCreation,
            builtin_spec  = BuiltinOptimization.builtin_execfile_spec
        )

def eval_extractor(node):
    # Need to accept globals and local keyword argument, that is just the API of
    # eval, pylint: disable=W0622

    def wrapEvalBuiltin(source, globals, locals, source_ref):
        globals_wrap, locals_wrap = wrapEvalGlobalsAndLocals(
            provider     = node.getParentVariableProvider(),
            globals_node = globals,
            locals_node  = locals,
            exec_mode    = False,
            source_ref   = source_ref
        )

        return ExpressionBuiltinEval(
            source_code = source,
            globals_arg = globals_wrap,
            locals_arg  = locals_wrap,
            source_ref  = source_ref
        )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = wrapEvalBuiltin,
        builtin_spec  = BuiltinOptimization.builtin_eval_spec
    )


if python_version >= 300:
    from nuitka.nodes.ExecEvalNodes import ExpressionBuiltinExec

    def exec_extractor(node):
        # Need to accept globals and local keyword argument, that is just the
        # API of exec, pylint: disable=W0622

        def wrapExpressionBuiltinExecCreation( source, globals, locals,
                                               source_ref ):
            provider = node.getParentVariableProvider()

            # TODO: Can't really be true, can it?
            if provider.isExpressionFunctionBody():
                provider.markAsExecContaining()

                if provider.isClassDictCreation():
                    provider.markAsUnqualifiedExecContaining( source_ref )

            globals_wrap, locals_wrap = wrapEvalGlobalsAndLocals(
                provider     = provider,
                globals_node = globals,
                locals_node  = locals,
                exec_mode    = False,
                source_ref   = source_ref
            )

            return ExpressionBuiltinExec(
                source_code = source,
                globals_arg = globals_wrap,
                locals_arg  = locals_wrap,
                source_ref  = source_ref
            )

        return BuiltinOptimization.extractBuiltinArgs(
            node          = node,
            builtin_class = wrapExpressionBuiltinExecCreation,
            builtin_spec  = BuiltinOptimization.builtin_eval_spec
        )

def open_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinOpen,
        builtin_spec  = BuiltinOptimization.builtin_open_spec
    )

def super_extractor(node):
    # Need to accept type and object as keyword argument, that is just the API
    # of super, pylint: disable=W0622
    def wrapSuperBuiltin(type, object, source_ref):
        if type is None and python_version >= 300:
            provider = node.getParentVariableProvider()

            if python_version < 340:
                type = ExpressionVariableRef(
                    variable_name = "__class__",
                    source_ref    = source_ref
                )

                # Ought to be already closure taken.
                type.setVariable(
                    provider.getVariableForClosure(
                        variable_name = "__class__"
                    )
                )

                if not type.getVariable().isClosureReference():
                    type = None
            else:
                parent_provider = provider.getParentVariableProvider()

                class_var = parent_provider.getTempVariable(
                    temp_scope = None,
                    name       = "__class__"
                )

                type = ExpressionTempVariableRef(
                    variable      = class_var.makeReference( parent_provider ).makeReference(provider),
                    source_ref    = source_ref
                )


            from nuitka.nodes.NodeMakingHelpers import \
                makeRaiseExceptionReplacementExpression

            if type is None:
                return makeRaiseExceptionReplacementExpression(
                    expression      = node,
                    exception_type  = "SystemError"
                                        if python_version < 331 else
                                      "RuntimeError",
                    exception_value = "super(): __class__ cell not found",
                )

            if object is None:
                if provider.getParameters().getArgumentCount() > 0:
                    par1_name = provider.getParameters().getArgumentNames()[0]
                    # TODO: Nested first argument would kill us here, need a
                    # test for that.

                    object = ExpressionVariableRef(
                        variable_name = par1_name,
                        source_ref    = source_ref
                    )

                    object.setVariable(
                        provider.getVariableForReference(
                            variable_name = par1_name
                        )
                    )

                    if not object.getVariable().isParameterVariable():
                        return makeRaiseExceptionReplacementExpression(
                            expression      = node,
                            exception_type  = "SystemError"
                                                if python_version < 330 else
                                              "RuntimeError",
                            exception_value = "super(): __class__ cell not found",
                        )
                else:
                    return makeRaiseExceptionReplacementExpression(
                        expression      = node,
                        exception_type  = "RuntimeError",
                        exception_value = "super(): no arguments"
                    )

        return ExpressionBuiltinSuper(
            super_type   = type,
            super_object = object,
            source_ref   = source_ref
        )

    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = wrapSuperBuiltin,
        builtin_spec  = BuiltinOptimization.builtin_super_spec
    )

def hasattr_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinHasattr,
        builtin_spec  = BuiltinOptimization.builtin_hasattr_spec
    )

def getattr_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinGetattr,
        builtin_spec  = BuiltinOptimization.builtin_getattr_spec
    )

def setattr_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinSetattr,
        builtin_spec  = BuiltinOptimization.builtin_setattr_spec
    )

def isinstance_extractor(node):
    return BuiltinOptimization.extractBuiltinArgs(
        node          = node,
        builtin_class = ExpressionBuiltinIsinstance,
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
    "set"        : set_extractor,
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

def computeBuiltinCall(call_node, called):
    builtin_name = called.getBuiltinName()

    if builtin_name in _dispatch_dict:
        new_node = _dispatch_dict[builtin_name](call_node)

        # Lets just have this contract to return "None" when no change is meant
        # to be done.
        assert new_node is not call_node
        if new_node is None:
            return call_node, None, None

        # For traces, we are going to ignore side effects, and output traces
        # only based on the basis of it.
        inspect_node = new_node
        if inspect_node.isExpressionSideEffects():
            inspect_node = inspect_node.getExpression()

        if inspect_node.isExpressionBuiltinImport():
            tags    = "new_import"
            message = """\
Replaced dynamic __import__ %s with static module import.""" % (
                inspect_node.kind,
            )
        elif inspect_node.isExpressionBuiltin() or \
             inspect_node.isStatementExec():
            tags = "new_builtin"
            message = "Replaced call to builtin %s with builtin call %s." % (
                builtin_name,
                inspect_node.kind,
            )
        elif inspect_node.isExpressionRaiseException():
            tags = "new_raise"
            message = """\
Replaced call to builtin %s with exception raising call.""" % (
                inspect_node.kind,
            )
        elif inspect_node.isExpressionOperationUnary():
            tags = "new_expression"
            message = """\
Replaced call to builtin %s with unary operation %s.""" % (
                inspect_node.kind,
                inspect_node.getOperator()
            )
        else:
            assert False, ( builtin_name, "->", inspect_node )

        # TODO: One day, this should be enabled by default and call either the
        # original built-in or the optimized above one. That should be done,
        # once we can eliminate the condition for most cases.
        if False and isDebug() and not shallMakeModule() and builtin_name:
            from nuitka.nodes.BuiltinRefNodes import (
                ExpressionBuiltinOriginalRef,
                ExpressionBuiltinRef,
            )
            from nuitka.nodes.NodeMakingHelpers import \
              makeRaiseExceptionReplacementExpression

            source_ref = called.getSourceReference()

            new_node = ExpressionConditional(
                condition      = ExpressionComparisonIs(
                    left  = ExpressionBuiltinRef(
                        builtin_name = builtin_name,
                        source_ref   = source_ref
                    ),
                    right = ExpressionBuiltinOriginalRef(
                        builtin_name = builtin_name,
                        source_ref   = source_ref
                    ),
                    source_ref   = source_ref
                ),
                yes_expression = new_node,
                no_expression  = makeRaiseExceptionReplacementExpression(
                    exception_type  = "RuntimeError",
                    exception_value = "Builtin '%s' was overloaded'" % (
                        builtin_name
                    ),
                    expression      = call_node
                ),
                source_ref     = source_ref
            )

        assert tags != ""

        return new_node, tags, message
    else:
        # TODO: Consider giving warnings, whitelisted potentially
        return call_node, None, None
