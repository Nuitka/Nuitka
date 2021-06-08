#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Optimize calls to built-in references to specific built-in calls.

For built-in name references, we check if it's one of the supported built-in
types, and then specialize for the ones, where it makes sense.
"""

from nuitka.__past__ import xrange  # pylint: disable=I0021,redefined-builtin
from nuitka.Errors import NuitkaAssumptionError
from nuitka.nodes.AssignNodes import (
    StatementAssignmentVariable,
    StatementDelVariable,
)
from nuitka.nodes.AttributeNodes import (
    ExpressionAttributeLookup,
    ExpressionBuiltinGetattr,
    ExpressionBuiltinHasattr,
    ExpressionBuiltinSetattr,
)
from nuitka.nodes.BuiltinAllNodes import ExpressionBuiltinAll
from nuitka.nodes.BuiltinAnyNodes import ExpressionBuiltinAny
from nuitka.nodes.BuiltinComplexNodes import (
    ExpressionBuiltinComplex1,
    ExpressionBuiltinComplex2,
)
from nuitka.nodes.BuiltinDecodingNodes import (
    ExpressionBuiltinChr,
    ExpressionBuiltinOrd,
)
from nuitka.nodes.BuiltinDecoratorNodes import (
    ExpressionBuiltinClassmethod,
    ExpressionBuiltinStaticmethod,
)
from nuitka.nodes.BuiltinDictNodes import ExpressionBuiltinDict
from nuitka.nodes.BuiltinFormatNodes import (
    ExpressionBuiltinAscii,
    ExpressionBuiltinBin,
    ExpressionBuiltinFormat,
    ExpressionBuiltinHex,
    ExpressionBuiltinId,
    ExpressionBuiltinOct,
)
from nuitka.nodes.BuiltinHashNodes import ExpressionBuiltinHash
from nuitka.nodes.BuiltinIntegerNodes import (
    ExpressionBuiltinInt1,
    ExpressionBuiltinInt2,
)
from nuitka.nodes.BuiltinIteratorNodes import (
    ExpressionBuiltinIter1,
    ExpressionBuiltinIter2,
)
from nuitka.nodes.BuiltinLenNodes import ExpressionBuiltinLen
from nuitka.nodes.BuiltinNextNodes import (
    ExpressionBuiltinNext1,
    ExpressionBuiltinNext2,
)
from nuitka.nodes.BuiltinOpenNodes import ExpressionBuiltinOpen
from nuitka.nodes.BuiltinRangeNodes import (
    ExpressionBuiltinRange1,
    ExpressionBuiltinRange2,
    ExpressionBuiltinRange3,
    ExpressionBuiltinXrange1,
    ExpressionBuiltinXrange2,
    ExpressionBuiltinXrange3,
)
from nuitka.nodes.BuiltinRefNodes import (
    ExpressionBuiltinAnonymousRef,
    makeExpressionBuiltinTypeRef,
)
from nuitka.nodes.BuiltinSumNodes import (
    ExpressionBuiltinSum1,
    ExpressionBuiltinSum2,
)
from nuitka.nodes.BuiltinTypeNodes import (
    ExpressionBuiltinBool,
    ExpressionBuiltinBytearray1,
    ExpressionBuiltinBytearray3,
    ExpressionBuiltinFloat,
    ExpressionBuiltinFrozenset,
    ExpressionBuiltinList,
    ExpressionBuiltinSet,
    ExpressionBuiltinStrP2,
    ExpressionBuiltinStrP3,
    ExpressionBuiltinTuple,
    ExpressionBuiltinUnicodeP2,
)
from nuitka.nodes.BuiltinVarsNodes import ExpressionBuiltinVars
from nuitka.nodes.CallNodes import makeExpressionCall
from nuitka.nodes.ClassNodes import ExpressionBuiltinType3
from nuitka.nodes.ComparisonNodes import ExpressionComparisonIs
from nuitka.nodes.ConditionalNodes import (
    ExpressionConditional,
    makeStatementConditional,
)
from nuitka.nodes.ConstantRefNodes import makeConstantRefNode
from nuitka.nodes.ContainerMakingNodes import makeExpressionMakeTupleOrConstant
from nuitka.nodes.ExecEvalNodes import (
    ExpressionBuiltinCompile,
    ExpressionBuiltinEval,
)
from nuitka.nodes.GlobalsLocalsNodes import (
    ExpressionBuiltinDir1,
    ExpressionBuiltinGlobals,
)
from nuitka.nodes.ImportNodes import ExpressionBuiltinImport
from nuitka.nodes.NodeMakingHelpers import (
    makeConstantReplacementNode,
    makeExpressionBuiltinLocals,
    makeRaiseExceptionReplacementExpression,
    makeRaiseExceptionReplacementExpressionFromInstance,
    wrapExpressionWithSideEffects,
)
from nuitka.nodes.OperatorNodes import ExpressionOperationBinaryDivmod
from nuitka.nodes.OperatorNodesUnary import (
    ExpressionOperationNot,
    ExpressionOperationUnaryAbs,
    ExpressionOperationUnaryRepr,
)
from nuitka.nodes.OutlineNodes import ExpressionOutlineBody
from nuitka.nodes.ReturnNodes import makeStatementReturn
from nuitka.nodes.SliceNodes import makeExpressionBuiltinSlice
from nuitka.nodes.TypeNodes import (
    ExpressionBuiltinIsinstance,
    ExpressionBuiltinIssubclass,
    ExpressionBuiltinSuper0,
    ExpressionBuiltinSuper2,
    ExpressionBuiltinType1,
)
from nuitka.nodes.VariableRefNodes import (
    ExpressionTempVariableRef,
    ExpressionVariableRef,
)
from nuitka.PythonVersions import python_version
from nuitka.specs import BuiltinParameterSpecs
from nuitka.tree.ReformulationExecStatements import wrapEvalGlobalsAndLocals
from nuitka.tree.ReformulationTryFinallyStatements import (
    makeTryFinallyStatement,
)
from nuitka.tree.TreeHelpers import (
    makeCallNode,
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
)


def dir_extractor(node):
    locals_scope = node.subnode_called.getLocalsScope()

    def buildDirEmptyCase(source_ref):
        source = makeExpressionBuiltinLocals(
            locals_scope=locals_scope, source_ref=source_ref
        )

        result = makeCallNode(
            ExpressionAttributeLookup(
                expression=source, attribute_name="keys", source_ref=source_ref
            ),
            source_ref,
        )

        # For Python3, keys doesn't really return values, but instead a handle
        # only, but we want it to be a list.
        if python_version >= 0x300:
            result = ExpressionBuiltinList(value=result, source_ref=source_ref)

        return result

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        # TODO: Needs locals_scope attached.
        builtin_class=ExpressionBuiltinDir1,
        builtin_spec=BuiltinParameterSpecs.builtin_dir_spec,
        empty_special_class=buildDirEmptyCase,
    )


def vars_extractor(node):
    locals_scope = node.subnode_called.getLocalsScope()

    def selectVarsEmptyClass(source_ref):
        return makeExpressionBuiltinLocals(
            locals_scope=locals_scope, source_ref=source_ref
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        # TODO: Needs locals_cope attached
        builtin_class=ExpressionBuiltinVars,
        builtin_spec=BuiltinParameterSpecs.builtin_vars_spec,
        empty_special_class=selectVarsEmptyClass,
    )


def import_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinImport,
        builtin_spec=BuiltinParameterSpecs.builtin_import_spec,
    )


def type_extractor(node):
    args = node.subnode_args

    if args is None:
        iter_length = 0
    else:
        iter_length = args.getIterationLength()

    if iter_length == 1:
        return BuiltinParameterSpecs.extractBuiltinArgs(
            node=node,
            builtin_class=ExpressionBuiltinType1,
            builtin_spec=BuiltinParameterSpecs.builtin_type1_spec,
        )
    elif iter_length == 3:
        return BuiltinParameterSpecs.extractBuiltinArgs(
            node=node,
            builtin_class=ExpressionBuiltinType3,
            builtin_spec=BuiltinParameterSpecs.builtin_type3_spec,
        )
    else:
        return makeRaiseExceptionReplacementExpressionFromInstance(
            expression=node, exception=TypeError("type() takes 1 or 3 arguments")
        )


def iter_extractor(node):
    def wrapIterCreation(callable_arg, sentinel, source_ref):
        if sentinel is None:
            return ExpressionBuiltinIter1(value=callable_arg, source_ref=source_ref)
        else:
            return ExpressionBuiltinIter2(
                callable_arg=callable_arg, sentinel=sentinel, source_ref=source_ref
            )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=wrapIterCreation,
        builtin_spec=BuiltinParameterSpecs.builtin_iter_spec,
    )


def next_extractor(node):
    # Split up next with and without defaults, they are not going to behave
    # really very similar.
    def selectNextBuiltinClass(iterator, default, source_ref):
        if default is None:
            return ExpressionBuiltinNext1(value=iterator, source_ref=source_ref)
        else:
            return ExpressionBuiltinNext2(
                iterator=iterator, default=default, source_ref=source_ref
            )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=selectNextBuiltinClass,
        builtin_spec=BuiltinParameterSpecs.builtin_next_spec,
    )


def sum_extractor(node):
    # Split up sumwith and without start value, one is much easier.
    def selectSumBuiltinClass(sequence, start, source_ref):
        if start is None:
            return ExpressionBuiltinSum1(sequence=sequence, source_ref=source_ref)
        else:
            return ExpressionBuiltinSum2(
                sequence=sequence, start=start, source_ref=source_ref
            )

    def makeSum0(source_ref):
        # pylint: disable=unused-argument

        return makeRaiseExceptionReplacementExpressionFromInstance(
            expression=node,
            exception=TypeError(
                "sum expected at least 1 arguments, got 0"
                if python_version < 0x380
                else "sum() takes at least 1 positional argument (0 given)"
            ),
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=selectSumBuiltinClass,
        builtin_spec=BuiltinParameterSpecs.builtin_sum_spec,
        empty_special_class=makeSum0,
    )


def dict_extractor(node):
    # The "dict" built-in is a bit strange in that it accepts a position
    # parameter, or not, but won't have a default value.
    def wrapExpressionBuiltinDictCreation(positional_args, dict_star_arg, source_ref):
        if len(positional_args) > 1:

            result = makeRaiseExceptionReplacementExpressionFromInstance(
                expression=node,
                exception=TypeError(
                    "dict expected at most 1 arguments, got %d" % (len(positional_args))
                ),
            )

            result = wrapExpressionWithSideEffects(
                side_effects=positional_args, old_node=node, new_node=result
            )

            if dict_star_arg:
                result = wrapExpressionWithSideEffects(
                    side_effects=dict_star_arg, old_node=node, new_node=result
                )

            return result

        return ExpressionBuiltinDict(
            pos_arg=positional_args[0] if positional_args else None,
            pairs=dict_star_arg,
            source_ref=source_ref,
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=wrapExpressionBuiltinDictCreation,
        builtin_spec=BuiltinParameterSpecs.builtin_dict_spec,
    )


def chr_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinChr,
        builtin_spec=BuiltinParameterSpecs.builtin_chr_spec,
    )


def ord_extractor(node):
    def makeOrd0(source_ref):
        # pylint: disable=unused-argument

        return makeRaiseExceptionReplacementExpressionFromInstance(
            expression=node,
            exception=TypeError("ord() takes exactly one argument (0 given)"),
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinOrd,
        builtin_spec=BuiltinParameterSpecs.builtin_ord_spec,
        empty_special_class=makeOrd0,
    )


def bin_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinBin,
        builtin_spec=BuiltinParameterSpecs.builtin_bin_spec,
    )


def oct_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinOct,
        builtin_spec=BuiltinParameterSpecs.builtin_oct_spec,
    )


def hex_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinHex,
        builtin_spec=BuiltinParameterSpecs.builtin_hex_spec,
    )


def id_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinId,
        builtin_spec=BuiltinParameterSpecs.builtin_id_spec,
    )


def repr_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionOperationUnaryRepr,
        builtin_spec=BuiltinParameterSpecs.builtin_repr_spec,
    )


if python_version >= 0x300:

    def ascii_extractor(node):
        return BuiltinParameterSpecs.extractBuiltinArgs(
            node=node,
            builtin_class=ExpressionBuiltinAscii,
            builtin_spec=BuiltinParameterSpecs.builtin_repr_spec,
        )


def range_extractor(node):
    def selectRangeBuiltin(low, high, step, source_ref):
        if high is None:
            return ExpressionBuiltinRange1(low=low, source_ref=source_ref)
        elif step is None:
            return ExpressionBuiltinRange2(low=low, high=high, source_ref=source_ref)
        else:
            return ExpressionBuiltinRange3(
                low=low, high=high, step=step, source_ref=source_ref
            )

    def makeRange0(source_ref):
        # pylint: disable=unused-argument
        try:
            range()
        except Exception as e:  # We want to broad here, pylint: disable=broad-except
            return makeRaiseExceptionReplacementExpressionFromInstance(
                expression=node, exception=e
            )
        else:
            raise NuitkaAssumptionError("range without argument is expected to raise")

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=selectRangeBuiltin,
        builtin_spec=BuiltinParameterSpecs.builtin_range_spec,
        empty_special_class=makeRange0,
    )


def xrange_extractor(node):
    def selectXrangeBuiltin(low, high, step, source_ref):
        if high is None:
            return ExpressionBuiltinXrange1(low=low, source_ref=source_ref)
        elif step is None:
            return ExpressionBuiltinXrange2(low=low, high=high, source_ref=source_ref)
        else:
            return ExpressionBuiltinXrange3(
                low=low, high=high, step=step, source_ref=source_ref
            )

    def makeXrange0(source_ref):
        # pylint: disable=unused-argument
        try:
            xrange()
        except Exception as e:  # We want to broad here, pylint: disable=broad-except
            return makeRaiseExceptionReplacementExpressionFromInstance(
                expression=node, exception=e
            )
        else:
            raise NuitkaAssumptionError("range without argument is expected to raise")

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=selectXrangeBuiltin,
        builtin_spec=BuiltinParameterSpecs.builtin_xrange_spec,
        empty_special_class=makeXrange0,
    )


def len_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinLen,
        builtin_spec=BuiltinParameterSpecs.builtin_len_spec,
    )


def all_extractor(node):
    # pylint: disable=unused-argument
    def makeAll0(source_ref):
        exception_message = "all() takes exactly one argument (0 given)"

        return makeRaiseExceptionReplacementExpressionFromInstance(
            expression=node, exception=TypeError(exception_message)
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinAll,
        builtin_spec=BuiltinParameterSpecs.builtin_all_spec,
        empty_special_class=makeAll0,
    )


def abs_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionOperationUnaryAbs,
        builtin_spec=BuiltinParameterSpecs.builtin_abs_spec,
    )


def any_extractor(node):
    # pylint: disable=unused-argument
    def makeAny0(source_ref):
        exception_message = "any() takes exactly one argument (0 given)"

        return makeRaiseExceptionReplacementExpressionFromInstance(
            expression=node, exception=TypeError(exception_message)
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinAny,
        builtin_spec=BuiltinParameterSpecs.builtin_any_spec,
        empty_special_class=makeAny0,
    )


def tuple_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinTuple,
        builtin_spec=BuiltinParameterSpecs.builtin_tuple_spec,
    )


def list_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinList,
        builtin_spec=BuiltinParameterSpecs.builtin_list_spec,
    )


def set_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinSet,
        builtin_spec=BuiltinParameterSpecs.builtin_set_spec,
    )


def frozenset_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinFrozenset,
        builtin_spec=BuiltinParameterSpecs.builtin_frozenset_spec,
    )


def float_extractor(node):
    def makeFloat0(source_ref):
        # pylint: disable=unused-argument

        return makeConstantReplacementNode(
            constant=float(), node=node, user_provided=False
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinFloat,
        builtin_spec=BuiltinParameterSpecs.builtin_float_spec,
        empty_special_class=makeFloat0,
    )


def complex_extractor(node):
    def makeComplex0(source_ref):
        # pylint: disable=unused-argument

        return makeConstantReplacementNode(
            constant=complex(), node=node, user_provided=False
        )

    def selectComplexBuiltin(real, imag, source_ref):
        if imag is None:
            return ExpressionBuiltinComplex1(value=real, source_ref=source_ref)
        else:
            return ExpressionBuiltinComplex2(
                real=real, imag=imag, source_ref=source_ref
            )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=selectComplexBuiltin,
        builtin_spec=BuiltinParameterSpecs.builtin_complex_spec,
        empty_special_class=makeComplex0,
    )


def str_extractor(node):
    builtin_class = ExpressionBuiltinStrP2 if str is bytes else ExpressionBuiltinStrP3

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=builtin_class,
        builtin_spec=builtin_class.builtin_spec,
    )


if python_version < 0x300:

    def unicode_extractor(node):
        return BuiltinParameterSpecs.extractBuiltinArgs(
            node=node,
            builtin_class=ExpressionBuiltinUnicodeP2,
            builtin_spec=ExpressionBuiltinUnicodeP2.builtin_spec,
        )


else:
    from nuitka.nodes.BuiltinTypeNodes import (
        ExpressionBuiltinBytes1,
        ExpressionBuiltinBytes3,
    )

    def bytes_extractor(node):
        def makeBytes0(source_ref):
            # pylint: disable=unused-argument

            return makeConstantReplacementNode(
                constant=bytes(), node=node, user_provided=False
            )

        def selectBytesBuiltin(string, encoding, errors, source_ref):
            if encoding is None and errors is None:
                return ExpressionBuiltinBytes1(value=string, source_ref=source_ref)
            else:
                return ExpressionBuiltinBytes3(
                    value=string,
                    encoding=encoding,
                    errors=errors,
                    source_ref=source_ref,
                )

        return BuiltinParameterSpecs.extractBuiltinArgs(
            node=node,
            builtin_class=selectBytesBuiltin,
            builtin_spec=BuiltinParameterSpecs.builtin_bytes_p3_spec,
            empty_special_class=makeBytes0,
        )


def bool_extractor(node):
    def makeBool0(source_ref):
        # pylint: disable=unused-argument

        return makeConstantReplacementNode(
            constant=bool(), node=node, user_provided=False
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinBool,
        builtin_spec=BuiltinParameterSpecs.builtin_bool_spec,
        empty_special_class=makeBool0,
    )


def int_extractor(node):
    def makeInt0(source_ref):
        # pylint: disable=unused-argument

        return makeConstantReplacementNode(
            constant=int(), node=node, user_provided=False
        )

    def selectIntBuiltin(value, base, source_ref):
        if base is None:
            return ExpressionBuiltinInt1(value=value, source_ref=source_ref)
        else:
            return ExpressionBuiltinInt2(value=value, base=base, source_ref=source_ref)

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=selectIntBuiltin,
        builtin_spec=BuiltinParameterSpecs.builtin_int_spec,
        empty_special_class=makeInt0,
    )


if python_version < 0x300:
    from nuitka.nodes.BuiltinIntegerNodes import (
        ExpressionBuiltinLong1,
        ExpressionBuiltinLong2,
    )

    def long_extractor(node):
        def makeLong0(source_ref):
            # pylint: disable=unused-argument

            return makeConstantReplacementNode(
                constant=int(), node=node, user_provided=False
            )

        def selectIntBuiltin(value, base, source_ref):
            if base is None:
                return ExpressionBuiltinLong1(value=value, source_ref=source_ref)
            else:
                return ExpressionBuiltinLong2(
                    value=value, base=base, source_ref=source_ref
                )

        return BuiltinParameterSpecs.extractBuiltinArgs(
            node=node,
            builtin_class=selectIntBuiltin,
            builtin_spec=BuiltinParameterSpecs.builtin_int_spec,
            empty_special_class=makeLong0,
        )


def globals_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinGlobals,
        builtin_spec=BuiltinParameterSpecs.builtin_globals_spec,
    )


def locals_extractor(node):
    locals_scope = node.subnode_called.getLocalsScope()

    def makeLocalsNode(source_ref):
        return makeExpressionBuiltinLocals(
            locals_scope=locals_scope, source_ref=source_ref
        )

    # Note: Locals on the module level is really globals.
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=makeLocalsNode,
        builtin_spec=BuiltinParameterSpecs.builtin_locals_spec,
    )


if python_version < 0x300:
    from nuitka.nodes.ExecEvalNodes import ExpressionBuiltinExecfile

    def execfile_extractor(node):
        def wrapExpressionBuiltinExecfileCreation(
            filename, globals_arg, locals_arg, source_ref
        ):
            outline_body = ExpressionOutlineBody(
                provider=node.getParentVariableProvider(),
                name="execfile_call",
                source_ref=source_ref,
            )

            globals_ref, locals_ref, tried, final = wrapEvalGlobalsAndLocals(
                provider=node.getParentVariableProvider(),
                globals_node=globals_arg,
                locals_node=locals_arg,
                temp_scope=outline_body.getOutlineTempScope(),
                source_ref=source_ref,
            )

            tried = makeStatementsSequence(
                statements=(
                    tried,
                    makeStatementReturn(
                        expression=ExpressionBuiltinExecfile(
                            source_code=makeCallNode(
                                ExpressionAttributeLookup(
                                    expression=ExpressionBuiltinOpen(
                                        filename=filename,
                                        mode=makeConstantRefNode(
                                            constant="rU", source_ref=source_ref
                                        ),
                                        buffering=None,
                                        source_ref=source_ref,
                                    ),
                                    attribute_name="read",
                                    source_ref=source_ref,
                                ),
                                source_ref,
                            ),
                            globals_arg=globals_ref,
                            locals_arg=locals_ref,
                            source_ref=source_ref,
                        ),
                        source_ref=source_ref,
                    ),
                ),
                allow_none=False,
                source_ref=source_ref,
            )

            outline_body.setChild(
                "body",
                makeStatementsSequenceFromStatement(
                    statement=makeTryFinallyStatement(
                        provider=outline_body,
                        tried=tried,
                        final=final,
                        source_ref=source_ref,
                    )
                ),
            )

            return outline_body

        return BuiltinParameterSpecs.extractBuiltinArgs(
            node=node,
            builtin_class=wrapExpressionBuiltinExecfileCreation,
            builtin_spec=BuiltinParameterSpecs.builtin_execfile_spec,
        )


def eval_extractor(node):
    def wrapEvalBuiltin(source, globals_arg, locals_arg, source_ref):
        provider = node.getParentVariableProvider()

        outline_body = ExpressionOutlineBody(
            provider=node.getParentVariableProvider(),
            name="eval_call",
            source_ref=source_ref,
        )

        globals_ref, locals_ref, tried, final = wrapEvalGlobalsAndLocals(
            provider=provider,
            globals_node=globals_arg,
            locals_node=locals_arg,
            temp_scope=outline_body.getOutlineTempScope(),
            source_ref=source_ref,
        )

        # The wrapping should not relocate to the "source_ref".
        assert (
            globals_arg is None
            or globals_ref.getSourceReference() == globals_arg.getSourceReference()
        )
        assert (
            locals_arg is None
            or locals_ref.getSourceReference() == locals_arg.getSourceReference()
        )

        source_variable = outline_body.allocateTempVariable(
            temp_scope=None, name="source"
        )

        final.setChild(
            "statements",
            final.subnode_statements
            + (
                StatementDelVariable(
                    variable=source_variable, tolerant=True, source_ref=source_ref
                ),
            ),
        )

        strip_choice = makeConstantRefNode(constant=(" \t",), source_ref=source_ref)

        if python_version >= 0x300:
            strip_choice = ExpressionConditional(
                condition=ExpressionComparisonIs(
                    left=ExpressionBuiltinType1(
                        value=ExpressionTempVariableRef(
                            variable=source_variable, source_ref=source_ref
                        ),
                        source_ref=source_ref,
                    ),
                    right=makeExpressionBuiltinTypeRef(
                        builtin_name="bytes", source_ref=source_ref
                    ),
                    source_ref=source_ref,
                ),
                expression_yes=makeConstantRefNode(
                    constant=(b" \t",), source_ref=source_ref
                ),
                expression_no=strip_choice,
                source_ref=source_ref,
            )

        # Source needs some special treatment for eval, if it's a string, it
        # must be stripped.
        string_fixup = StatementAssignmentVariable(
            variable=source_variable,
            source=makeExpressionCall(
                called=ExpressionAttributeLookup(
                    expression=ExpressionTempVariableRef(
                        variable=source_variable, source_ref=source_ref
                    ),
                    attribute_name="strip",
                    source_ref=source_ref,
                ),
                args=strip_choice,  # This is a tuple
                kw=None,
                source_ref=source_ref,
            ),
            source_ref=source_ref,
        )

        acceptable_builtin_types = [
            ExpressionBuiltinAnonymousRef(builtin_name="code", source_ref=source_ref)
        ]

        if python_version >= 0x270:
            acceptable_builtin_types.append(
                makeExpressionBuiltinTypeRef(
                    builtin_name="memoryview", source_ref=source_ref
                )
            )

        statements = (
            StatementAssignmentVariable(
                variable=source_variable, source=source, source_ref=source_ref
            ),
            makeStatementConditional(
                condition=ExpressionOperationNot(
                    operand=ExpressionBuiltinIsinstance(
                        instance=ExpressionTempVariableRef(
                            variable=source_variable, source_ref=source_ref
                        ),
                        classes=makeExpressionMakeTupleOrConstant(
                            elements=acceptable_builtin_types,
                            user_provided=True,
                            source_ref=source_ref,
                        ),
                        source_ref=source_ref,
                    ),
                    source_ref=source_ref,
                ),
                yes_branch=string_fixup,
                no_branch=None,
                source_ref=source_ref,
            ),
            makeStatementReturn(
                expression=ExpressionBuiltinEval(
                    source_code=ExpressionTempVariableRef(
                        variable=source_variable, source_ref=source_ref
                    ),
                    globals_arg=globals_ref,
                    locals_arg=locals_ref,
                    source_ref=source_ref,
                ),
                source_ref=source_ref,
            ),
        )

        tried = makeStatementsSequence(
            statements=(tried,) + statements, allow_none=False, source_ref=source_ref
        )

        outline_body.setChild(
            "body",
            makeStatementsSequenceFromStatement(
                statement=makeTryFinallyStatement(
                    provider=outline_body,
                    tried=tried,
                    final=final,
                    source_ref=source_ref,
                )
            ),
        )

        return outline_body

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=wrapEvalBuiltin,
        builtin_spec=BuiltinParameterSpecs.builtin_eval_spec,
    )


if python_version >= 0x300:
    from nuitka.nodes.ExecEvalNodes import ExpressionBuiltinExec

    def exec_extractor(node):
        def wrapExpressionBuiltinExecCreation(
            source, globals_arg, locals_arg, source_ref
        ):
            provider = node.getParentVariableProvider()

            outline_body = ExpressionOutlineBody(
                provider=provider, name="exec_call", source_ref=source_ref
            )

            globals_ref, locals_ref, tried, final = wrapEvalGlobalsAndLocals(
                provider=provider,
                globals_node=globals_arg,
                locals_node=locals_arg,
                temp_scope=outline_body.getOutlineTempScope(),
                source_ref=source_ref,
            )

            tried = makeStatementsSequence(
                statements=(
                    tried,
                    makeStatementReturn(
                        expression=ExpressionBuiltinExec(
                            source_code=source,
                            globals_arg=globals_ref,
                            locals_arg=locals_ref,
                            source_ref=source_ref,
                        ),
                        source_ref=source_ref,
                    ),
                ),
                allow_none=False,
                source_ref=source_ref,
            )

            # Hack: Allow some APIs to work already
            tried.parent = outline_body

            outline_body.setChild(
                "body",
                makeStatementsSequenceFromStatement(
                    statement=makeTryFinallyStatement(
                        provider=provider,
                        tried=tried,
                        final=final,
                        source_ref=source_ref,
                    )
                ),
            )

            return outline_body

        return BuiltinParameterSpecs.extractBuiltinArgs(
            node=node,
            builtin_class=wrapExpressionBuiltinExecCreation,
            builtin_spec=BuiltinParameterSpecs.builtin_eval_spec,
        )


def compile_extractor(node):
    def wrapExpressionBuiltinCompileCreation(
        source_code, filename, mode, flags, dont_inherit, optimize=None, source_ref=None
    ):
        return ExpressionBuiltinCompile(
            source_code=source_code,
            filename=filename,
            mode=mode,
            flags=flags,
            dont_inherit=dont_inherit,
            optimize=optimize,
            source_ref=source_ref,
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=wrapExpressionBuiltinCompileCreation,
        builtin_spec=BuiltinParameterSpecs.builtin_compile_spec,
    )


def open_extractor(node):
    def makeOpen0(source_ref):
        # pylint: disable=unused-argument
        try:
            open()
        except Exception as e:  # We want to broad here, pylint: disable=broad-except
            return makeRaiseExceptionReplacementExpressionFromInstance(
                expression=node, exception=e
            )
        else:
            raise NuitkaAssumptionError("open without argument is expected to raise")

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinOpen,
        builtin_spec=BuiltinParameterSpecs.builtin_open_spec,
        empty_special_class=makeOpen0,
    )


def super_extractor(node):
    def wrapSuperBuiltin(type_arg, object_arg, source_ref):
        if type_arg is None and python_version >= 0x300:
            if provider.isCompiledPythonModule():
                return makeRaiseExceptionReplacementExpression(
                    expression=node,
                    exception_type="RuntimeError",
                    exception_value="super(): no arguments",
                )

            class_variable = provider.getVariableForReference(variable_name="__class__")

            provider.trace_collection.getVariableCurrentTrace(class_variable).addUsage()

            type_arg = ExpressionVariableRef(
                # Ought to be already closure taken due to "super" flag in
                # tree building.
                variable=class_variable,
                source_ref=source_ref,
            )

            # If we already have this as a local variable, then use that
            # instead.
            type_arg_owner = class_variable.getOwner()
            if type_arg_owner is provider or not (
                type_arg_owner.isExpressionFunctionBody()
                or type_arg_owner.isExpressionClassBody()
            ):
                return makeRaiseExceptionReplacementExpression(
                    expression=node,
                    exception_type="SystemError"
                    if python_version < 0x331
                    else "RuntimeError",
                    exception_value="super(): __class__ cell not found",
                )

            if object_arg is None:
                if (
                    provider.isExpressionGeneratorObjectBody()
                    or provider.isExpressionCoroutineObjectBody()
                    or provider.isExpressionAsyncgenObjectBody()
                ):
                    parameter_provider = provider.getParentVariableProvider()
                else:
                    parameter_provider = provider

                if parameter_provider.getParameters().getArgumentCount() == 0:
                    return makeRaiseExceptionReplacementExpression(
                        expression=node,
                        exception_type="RuntimeError",
                        exception_value="super(): no arguments",
                    )
                else:
                    par1_name = parameter_provider.getParameters().getArgumentNames()[0]

                    object_variable = provider.getVariableForReference(
                        variable_name=par1_name
                    )

                    provider.trace_collection.getVariableCurrentTrace(
                        object_variable
                    ).addUsage()

                    object_arg = ExpressionVariableRef(
                        variable=object_variable, source_ref=source_ref
                    )

                    if not object_arg.getVariable().isParameterVariable():
                        return makeRaiseExceptionReplacementExpression(
                            expression=node,
                            exception_type="SystemError"
                            if python_version < 0x300
                            else "RuntimeError",
                            exception_value="super(): __class__ cell not found",
                        )

            return ExpressionBuiltinSuper0(
                type_arg=type_arg, object_arg=object_arg, source_ref=source_ref
            )

        return ExpressionBuiltinSuper2(
            type_arg=type_arg, object_arg=object_arg, source_ref=source_ref
        )

    provider = node.getParentVariableProvider().getEntryPoint()

    if not provider.isCompiledPythonModule():
        provider.discardFlag("has_super")

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=wrapSuperBuiltin,
        builtin_spec=BuiltinParameterSpecs.builtin_super_spec,
    )


def hasattr_extractor(node):
    # We need to have to builtin arguments, pylint: disable=redefined-builtin
    def makeExpressionBuiltinHasattr(object, name, source_ref):
        return ExpressionBuiltinHasattr(
            expression=object, name=name, source_ref=source_ref
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=makeExpressionBuiltinHasattr,
        builtin_spec=BuiltinParameterSpecs.builtin_hasattr_spec,
    )


def getattr_extractor(node):
    # We need to have to builtin arguments, pylint: disable=redefined-builtin
    def makeExpressionBuiltinGetattr(object, name, default, source_ref):
        return ExpressionBuiltinGetattr(
            expression=object, name=name, default=default, source_ref=source_ref
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=makeExpressionBuiltinGetattr,
        builtin_spec=BuiltinParameterSpecs.builtin_getattr_spec,
    )


def setattr_extractor(node):
    # We need to have to builtin arguments, pylint: disable=redefined-builtin
    def makeExpressionBuiltinSetattr(object, name, value, source_ref):
        return ExpressionBuiltinSetattr(
            expression=object, name=name, value=value, source_ref=source_ref
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=makeExpressionBuiltinSetattr,
        builtin_spec=BuiltinParameterSpecs.builtin_setattr_spec,
    )


def isinstance_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinIsinstance,
        builtin_spec=BuiltinParameterSpecs.builtin_isinstance_spec,
    )


def issubclass_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinIssubclass,
        builtin_spec=BuiltinParameterSpecs.builtin_isinstance_spec,
    )


def bytearray_extractor(node):
    def makeBytearray0(source_ref):
        return makeConstantRefNode(constant=bytearray(), source_ref=source_ref)

    def selectNextBuiltinClass(string, encoding, errors, source_ref):
        if encoding is None:
            return ExpressionBuiltinBytearray1(value=string, source_ref=source_ref)
        else:
            return ExpressionBuiltinBytearray3(
                string=string, encoding=encoding, errors=errors, source_ref=source_ref
            )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=selectNextBuiltinClass,
        builtin_spec=BuiltinParameterSpecs.builtin_bytearray_spec,
        empty_special_class=makeBytearray0,
    )


def slice_extractor(node):
    def wrapSlice(start, stop, step, source_ref):
        if start is not None and stop is None:
            # Default rules are strange. If one argument is given, it's the
            # second one then.
            stop = start
            start = None

        return makeExpressionBuiltinSlice(
            start=start, stop=stop, step=step, source_ref=source_ref
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=wrapSlice,
        builtin_spec=BuiltinParameterSpecs.builtin_slice_spec,
    )


def hash_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinHash,
        builtin_spec=BuiltinParameterSpecs.builtin_hash_spec,
    )


def format_extractor(node):
    def makeFormat0(source_ref):
        # pylint: disable=unused-argument

        return makeRaiseExceptionReplacementExpressionFromInstance(
            expression=node,
            exception=TypeError("format() takes at least 1 argument (0 given)"),
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinFormat,
        builtin_spec=BuiltinParameterSpecs.builtin_format_spec,
        empty_special_class=makeFormat0,
    )


def staticmethod_extractor(node):
    def makeStaticmethod0(source_ref):
        # pylint: disable=unused-argument

        return makeRaiseExceptionReplacementExpressionFromInstance(
            expression=node,
            exception=TypeError("staticmethod expected 1 arguments, got 0"),
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinStaticmethod,
        builtin_spec=BuiltinParameterSpecs.builtin_staticmethod_spec,
        empty_special_class=makeStaticmethod0,
    )


def classmethod_extractor(node):
    def makeStaticmethod0(source_ref):
        # pylint: disable=unused-argument

        return makeRaiseExceptionReplacementExpressionFromInstance(
            expression=node,
            exception=TypeError("classmethod expected 1 arguments, got 0"),
        )

    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionBuiltinClassmethod,
        builtin_spec=BuiltinParameterSpecs.builtin_classmethod_spec,
        empty_special_class=makeStaticmethod0,
    )


def divmod_extractor(node):
    return BuiltinParameterSpecs.extractBuiltinArgs(
        node=node,
        builtin_class=ExpressionOperationBinaryDivmod,
        builtin_spec=BuiltinParameterSpecs.builtin_divmod_spec,
    )


_dispatch_dict = {
    "compile": compile_extractor,
    "globals": globals_extractor,
    "locals": locals_extractor,
    "eval": eval_extractor,
    "dir": dir_extractor,
    "vars": vars_extractor,
    "__import__": import_extractor,
    "chr": chr_extractor,
    "ord": ord_extractor,
    "bin": bin_extractor,
    "oct": oct_extractor,
    "hex": hex_extractor,
    "id": id_extractor,
    "type": type_extractor,
    "iter": iter_extractor,
    "next": next_extractor,
    "sum": sum_extractor,
    "tuple": tuple_extractor,
    "list": list_extractor,
    "dict": dict_extractor,
    "set": set_extractor,
    "frozenset": frozenset_extractor,
    "float": float_extractor,
    "complex": complex_extractor,
    "str": str_extractor,
    "bool": bool_extractor,
    "int": int_extractor,
    "repr": repr_extractor,
    "len": len_extractor,
    "any": any_extractor,
    "abs": abs_extractor,
    "all": all_extractor,
    "super": super_extractor,
    "hasattr": hasattr_extractor,
    "getattr": getattr_extractor,
    "setattr": setattr_extractor,
    "isinstance": isinstance_extractor,
    "issubclass": issubclass_extractor,
    "bytearray": bytearray_extractor,
    "slice": slice_extractor,
    "hash": hash_extractor,
    "format": format_extractor,
    "open": open_extractor,
    "staticmethod": staticmethod_extractor,
    "classmethod": classmethod_extractor,
    "divmod": divmod_extractor,
}

if python_version < 0x300:
    # These are not in Python3
    _dispatch_dict["long"] = long_extractor
    _dispatch_dict["unicode"] = unicode_extractor
    _dispatch_dict["execfile"] = execfile_extractor
    _dispatch_dict["xrange"] = xrange_extractor

    _dispatch_dict["range"] = range_extractor
else:
    # This one is not in Python2:
    _dispatch_dict["bytes"] = bytes_extractor
    _dispatch_dict["ascii"] = ascii_extractor
    _dispatch_dict["exec"] = exec_extractor

    # The Python3 range is really an xrange, use that.
    _dispatch_dict["range"] = xrange_extractor


def check():
    from nuitka.Builtins import builtin_names

    for builtin_name in _dispatch_dict:
        assert builtin_name in builtin_names, builtin_name


check()

_builtin_ignore_list = (
    # Not supporting 'print', because it could be replaced, and is not
    # worth the effort yet.
    "print",
    # TODO: This could, and should be supported, as we could e.g. lower
    # types easily for it.
    "sorted",
    # TODO: This would be very worthwhile, as it could easily optimize
    # its iteration away.
    "zip",
    # TODO: This would be most precious due to the type hint it gives
    "enumerate",
    # TODO: Also worthwhile for known values.
    "reversed",
    # TODO: Not sure what this really is about.
    "memoryview",
)


def _describeNewNode(builtin_name, inspect_node):
    """Describe the change for better understanding."""

    # Don't mention side effects, that's not what we care about.
    if inspect_node.isExpressionSideEffects():
        inspect_node = inspect_node.subnode_expression

    if inspect_node.isExpressionBuiltinImport():
        tags = "new_import"
        message = """\
Replaced dynamic "__import__" call with static built-in call."""
    elif inspect_node.isExpressionBuiltin() or inspect_node.isStatementExec():
        tags = "new_builtin"
        message = "Replaced call to built-in '%s' with built-in call '%s'." % (
            builtin_name,
            inspect_node.kind,
        )
    elif inspect_node.isExpressionRaiseException():
        tags = "new_raise"
        message = """\
Replaced call to built-in '%s' with exception raise.""" % (
            builtin_name,
        )
    elif inspect_node.isExpressionOperationBinary():
        tags = "new_expression"
        message = """\
Replaced call to built-in '%s' with binary operation '%s'.""" % (
            builtin_name,
            inspect_node.getOperator(),
        )
    elif inspect_node.isExpressionOperationUnary():
        tags = "new_expression"
        message = """\
Replaced call to built-in '%s' with unary operation '%s'.""" % (
            builtin_name,
            inspect_node.getOperator(),
        )
    elif inspect_node.isExpressionCall():
        tags = "new_expression"
        message = """\
Replaced call to built-in '%s' with call.""" % (
            builtin_name,
        )
    elif inspect_node.isExpressionOutlineBody():
        tags = "new_expression"
        message = (
            """\
Replaced call to built-in '%s' with outlined call."""
            % builtin_name
        )
    elif inspect_node.isExpressionConstantRef():
        tags = "new_expression"
        message = (
            """\
Replaced call to built-in '%s' with constant value."""
            % builtin_name
        )
    else:
        assert False, (builtin_name, "->", inspect_node)

    return tags, message


def computeBuiltinCall(builtin_name, call_node):
    # There is some dispatching for how to output various types of changes,
    # with lots of cases.
    if builtin_name in _dispatch_dict:
        new_node = _dispatch_dict[builtin_name](call_node)

        assert new_node is not call_node, builtin_name
        assert new_node is not None, builtin_name

        # For traces, we are going to ignore side effects, and output traces
        # only based on the basis of it.
        tags, message = _describeNewNode(builtin_name, new_node)

        return new_node, tags, message
    else:
        # TODO: Achieve coverage of all built-ins in at least the ignore list.
        # if False and builtin_name not in _builtin_ignore_list:
        #     optimization_logger.warning(
        #         "Not handling built-in %r, consider support." % builtin_name
        #     )

        return call_node, None, None
