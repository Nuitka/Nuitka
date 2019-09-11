#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
#                     Batakrishna Sahu, mailto:batakrishna.sahu@suiit.ac.in
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
""" Node for the calls to the 'zip' built-in.
"""

from nuitka.specs import BuiltinParameterSpecs
from nuitka.tree.ReformulationTryExceptStatements import makeTryExceptSingleHandlerNode
from nuitka.tree.TreeHelpers import (
    makeStatementsSequence,
    makeStatementsSequenceFromStatement,
)

from .AssignNodes import StatementAssignmentVariable, StatementReleaseVariable
from .BuiltinIteratorNodes import ExpressionBuiltinIter1
from .BuiltinNextNodes import ExpressionBuiltinNext1
from .BuiltinRefNodes import ExpressionBuiltinExceptionRef
from .ConstantRefNodes import makeConstantRefNode
from .ContainerMakingNodes import ExpressionMakeTuple
from .ExceptionNodes import StatementRaiseException
from .ExpressionBases import ExpressionChildHavingBase
from .FunctionNodes import ExpressionFunctionRef
from .GeneratorNodes import (
    ExpressionGeneratorObjectBody,
    ExpressionMakeGeneratorObject,
    StatementGeneratorReturnNone,
)
from .LoopNodes import StatementLoop, StatementLoopBreak
from .NodeMakingHelpers import (
    makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue,
)
from .OutlineNodes import ExpressionOutlineBody
from .ReturnNodes import StatementReturn
from .StatementNodes import StatementExpressionOnly
from .VariableRefNodes import ExpressionTempVariableRef
from .YieldNodes import ExpressionYield


# TODO: Add support for generator outlines and
# remove this node entirely.
class ExpressionBuiltinZip(ExpressionChildHavingBase):
    kind = "EXPRESSION_BUILTIN_ZIP"

    named_child = "values"

    builtin_spec = BuiltinParameterSpecs.builtin_zip_spec

    getValues = ExpressionChildHavingBase.childGetter("values")

    def computeExpression(self, trace_collection):
        values = self.getValues()

        if values:
            for count, value in enumerate(values):
                if not value.hasShapeSlotIter():
                    return makeRaiseTypeErrorExceptionReplacementFromTemplateAndValue(
                        template="zip argument #%d must support iteration"
                        % (count + 1),
                        operation="zip",
                        original_node=value,
                        value_node=value,
                    )

            # TODO: How can we do the same as computeExpressionIter1
            # even for exceptions.
            # zip arguments could be lowered, not done now.
            # [1,2,3] -> (1,2,3)

        return self, None, None

    # TODO: We should have an iteration handle.
    # Length and values might be possible to predict
    # if every argument iteration handle is capable of it.

    def computeExpressionIter1(self, iter_node, trace_collection):
        values = self.getValues()

        # TODO: Put re-formulation, ideally shared with Python2
        # zip here, with yield instead of appending to a list
        # needs no list temporary variable of course.

        provider = self.getParentVariableProvider()

        outline_body = ExpressionOutlineBody(
            provider=provider, name="zip_reformulation", source_ref=self.source_ref
        )

        zip_arg_variables = [
            outline_body.allocateTempVariable(
                temp_scope=None, name="zip_arg_%d" % (i + 1)
            )
            for i in range(len(values))
        ]

        statements = [
            StatementAssignmentVariable(
                variable=zip_arg_variable, source=call_arg, source_ref=self.source_ref
            )
            for call_arg, zip_arg_variable in zip(values, zip_arg_variables)
        ]

        # while provider.isExpressionOutlineBody() or provider.isExpressionOutlineFunction():
        #     provider = provider.getParentVariableProvider()

        generator_body = ExpressionGeneratorObjectBody(
            provider=provider,
            name="builtin_zip",
            code_object=None,  # provider.getCodeObject(),
            flags=set(),
            source_ref=self.source_ref,
        )

        # Take closure of arg variable to use them in generator
        for variable in zip_arg_variables:
            generator_body.addClosureVariable(variable)

        statements.append(
            StatementReturn(
                expression=ExpressionMakeGeneratorObject(
                    generator_ref=ExpressionFunctionRef(
                        function_body=generator_body, source_ref=self.source_ref
                    ),
                    source_ref=self.source_ref,
                ),
                source_ref=self.source_ref,
            )
        )

        outline_body.setBody(
            makeStatementsSequence(
                statements=statements, allow_none=False, source_ref=self.source_ref
            )
        )

        statements = []

        zip_iter_variables = [
            generator_body.allocateTempVariable(
                temp_scope=None, name="zip_iter_%d" % (i + 1)
            )
            for i in range(len(values))
        ]

        statements += [
            makeTryExceptSingleHandlerNode(
                tried=makeStatementsSequenceFromStatement(
                    StatementAssignmentVariable(
                        variable=zip_iter_variable,
                        source=ExpressionBuiltinIter1(
                            value=ExpressionTempVariableRef(
                                variable=zip_arg_variable, source_ref=self.source_ref
                            ),
                            source_ref=self.source_ref,
                        ),
                        source_ref=self.source_ref,
                    )
                ),
                exception_name="TypeError",
                handler_body=StatementRaiseException(
                    exception_type=ExpressionBuiltinExceptionRef(
                        exception_name="TypeError", source_ref=self.source_ref
                    ),
                    exception_value=makeConstantRefNode(
                        constant="zip argument #%d must support iteration" % (i + 1),
                        source_ref=self.source_ref,
                    ),
                    exception_trace=None,
                    exception_cause=None,
                    source_ref=self.source_ref,
                ),
                source_ref=self.source_ref,
            )
            for i, zip_iter_variable, zip_arg_variable in zip(
                range(len(values)), zip_iter_variables, zip_arg_variables
            )
        ]

        yield_statement = StatementExpressionOnly(
            expression=ExpressionYield(
                expression=ExpressionMakeTuple(
                    elements=[
                        ExpressionBuiltinNext1(
                            value=ExpressionTempVariableRef(
                                variable=zip_iter_variable, source_ref=self.source_ref
                            ),
                            source_ref=self.source_ref,
                        )
                        for zip_iter_variable in zip_iter_variables
                    ],
                    source_ref=self.source_ref,
                ),
                source_ref=self.source_ref,
            ),
            source_ref=self.source_ref,
        )

        loop_body = StatementLoop(
            body=makeStatementsSequenceFromStatement(
                statement=makeTryExceptSingleHandlerNode(
                    tried=yield_statement,
                    exception_name="StopIteration",
                    handler_body=StatementLoopBreak(source_ref=self.source_ref),
                    source_ref=self.source_ref,
                )
            ),
            source_ref=self.source_ref,
        )

        statements.append(loop_body)

        # Code generation expects this to be there.
        statements.append(StatementGeneratorReturnNone(source_ref=self.source_ref))

        generator_body.setBody(
            makeStatementsSequence(
                statements=statements, allow_none=False, source_ref=self.source_ref
            )
        )

        return outline_body, "new_expression", "Lowered zip built-in to generator."
