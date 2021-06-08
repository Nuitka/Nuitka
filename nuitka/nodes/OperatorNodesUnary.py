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
""" Nodes for unary operations.

Some of these come from built-ins, e.g. abs, some from syntax, and repr from both.
"""
from nuitka import PythonOperators

from .ConstantRefNodes import makeConstantRefNode
from .ExpressionBases import ExpressionChildHavingBase
from .shapes.BuiltinTypeShapes import tshape_bool, tshape_str


class ExpressionOperationUnaryBase(ExpressionChildHavingBase):
    named_child = "operand"

    __slots__ = ("operator", "simulator")

    def __init__(self, operand, source_ref):
        ExpressionChildHavingBase.__init__(self, value=operand, source_ref=source_ref)

    def getOperator(self):
        return self.operator

    def computeExpression(self, trace_collection):
        operator = self.getOperator()
        operand = self.subnode_operand

        if operand.isCompileTimeConstant():
            operand_value = operand.getCompileTimeConstant()

            return trace_collection.getCompileTimeComputationResult(
                node=self,
                computation=lambda: self.simulator(operand_value),
                description="Operator '%s' with constant argument." % operator,
            )
        else:
            # TODO: May go down to MemoryError for compile time constant overflow
            # ones.
            trace_collection.onExceptionRaiseExit(BaseException)

            # The value of that node escapes and could change its contents.
            # TODO: The unary operations don't do much to an operator, add
            # methods, that don't do stuff on common types though.
            # trace_collection.onValueEscapeSomeUnaryOperator(operand)

            # Any code could be run, note that.
            trace_collection.onControlFlowEscape(self)

            return self, None, None

    @staticmethod
    def isExpressionOperationUnary():
        return True


class ExpressionOperationUnaryRepr(ExpressionOperationUnaryBase):
    """Python unary operator `x` and repr built-in."""

    kind = "EXPRESSION_OPERATION_UNARY_REPR"

    operator = "Repr"

    __slots__ = ("escape_desc",)

    def __init__(self, operand, source_ref):
        assert operand.isExpression(), operand

        ExpressionOperationUnaryBase.__init__(
            self, operand=operand, source_ref=source_ref
        )

        self.escape_desc = None

    def computeExpression(self, trace_collection):
        result, self.escape_desc = self.subnode_operand.computeExpressionOperationRepr(
            repr_node=self, trace_collection=trace_collection
        )

        return result

    def mayRaiseException(self, exception_type):
        # TODO: Match getExceptionExit() more precisely against exception type given
        return (
            self.escape_desc is None
            or self.escape_desc.getExceptionExit() is not None
            or self.subnode_operand.mayRaiseException(exception_type)
        )

    def mayRaiseExceptionBool(self, exception_type):
        return False

    def mayHaveSideEffects(self):
        operand = self.subnode_operand

        if operand.mayHaveSideEffects():
            return True

        return self.escape_desc is None or self.escape_desc.isControlFlowEscape()

    @staticmethod
    def getTypeShape():
        # Even unicode gets decoded in Python2
        return tshape_str


class ExpressionOperationUnarySub(ExpressionOperationUnaryBase):
    """Python unary operator -"""

    kind = "EXPRESSION_OPERATION_UNARY_SUB"

    operator = "USub"
    simulator = PythonOperators.unary_operator_functions[operator]

    def __init__(self, operand, source_ref):
        assert operand.isExpression(), operand

        ExpressionOperationUnaryBase.__init__(
            self, operand=operand, source_ref=source_ref
        )


class ExpressionOperationUnaryAdd(ExpressionOperationUnaryBase):
    """Python unary operator +"""

    kind = "EXPRESSION_OPERATION_UNARY_ADD"

    operator = "UAdd"
    simulator = PythonOperators.unary_operator_functions[operator]

    def __init__(self, operand, source_ref):
        assert operand.isExpression(), operand

        ExpressionOperationUnaryBase.__init__(
            self, operand=operand, source_ref=source_ref
        )


class ExpressionOperationUnaryInvert(ExpressionOperationUnaryBase):
    """Python unary operator ~"""

    kind = "EXPRESSION_OPERATION_UNARY_INVERT"

    operator = "Invert"
    simulator = PythonOperators.unary_operator_functions[operator]

    def __init__(self, operand, source_ref):
        assert operand.isExpression(), operand

        ExpressionOperationUnaryBase.__init__(
            self, operand=operand, source_ref=source_ref
        )


class ExpressionOperationNot(ExpressionOperationUnaryBase):
    kind = "EXPRESSION_OPERATION_NOT"

    operator = "Not"
    simulator = PythonOperators.unary_operator_functions[operator]

    def __init__(self, operand, source_ref):
        ExpressionOperationUnaryBase.__init__(
            self, operand=operand, source_ref=source_ref
        )

    @staticmethod
    def getTypeShape():
        return tshape_bool

    def computeExpression(self, trace_collection):
        return self.subnode_operand.computeExpressionOperationNot(
            not_node=self, trace_collection=trace_collection
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_operand.mayRaiseException(
            exception_type
        ) or self.subnode_operand.mayRaiseExceptionBool(exception_type)

    def mayRaiseExceptionBool(self, exception_type):
        return self.subnode_operand.mayRaiseExceptionBool(exception_type)

    def getTruthValue(self):
        result = self.subnode_operand.getTruthValue()

        # Need to invert the truth value of operand of course here.
        return None if result is None else not result

    def mayHaveSideEffects(self):
        operand = self.subnode_operand

        if operand.mayHaveSideEffects():
            return True

        return operand.mayHaveSideEffectsBool()

    def mayHaveSideEffectsBool(self):
        return self.subnode_operand.mayHaveSideEffectsBool()

    def extractSideEffects(self):
        operand = self.subnode_operand

        # TODO: Find the common ground of these, and make it an expression
        # method.
        if operand.isExpressionMakeSequence():
            return operand.extractSideEffects()

        if operand.isExpressionMakeDict():
            return operand.extractSideEffects()

        return (self,)


class ExpressionOperationUnaryAbs(ExpressionOperationUnaryBase):
    kind = "EXPRESSION_OPERATION_UNARY_ABS"

    operator = "Abs"
    simulator = PythonOperators.unary_operator_functions[operator]

    def __init__(self, operand, source_ref):
        ExpressionOperationUnaryBase.__init__(
            self, operand=operand, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        return self.subnode_operand.computeExpressionAbs(
            abs_node=self, trace_collection=trace_collection
        )

    def mayRaiseException(self, exception_type):
        operand = self.subnode_operand

        if operand.mayRaiseException(exception_type):
            return True

        return operand.mayRaiseExceptionAbs(exception_type)

    def mayHaveSideEffects(self):
        operand = self.subnode_operand

        if operand.mayHaveSideEffects():
            return True

        return operand.mayHaveSideEffectsAbs()


def makeExpressionOperationUnary(operator, operand, source_ref):
    if operator == "Repr":
        unary_class = ExpressionOperationUnaryRepr
    elif operator == "USub":
        unary_class = ExpressionOperationUnarySub
    elif operator == "UAdd":
        unary_class = ExpressionOperationUnaryAdd
    elif operator == "Invert":
        unary_class = ExpressionOperationUnaryInvert
    else:
        assert False, operand

    # Shortcut these unary operations, avoiding "-1", etc. to ever become one.
    if operand.isCompileTimeConstant():
        try:
            constant = unary_class.simulator(operand.getCompileTimeConstant())
        except Exception:  # Catch all the things, pylint: disable=broad-except
            # Compile time detectable error, postpone these, so they get traced.
            pass
        else:
            return makeConstantRefNode(
                constant=constant,
                source_ref=source_ref,
                user_provided=getattr(operand, "user_provided", False),
            )

    return unary_class(operand=operand, source_ref=source_ref)
