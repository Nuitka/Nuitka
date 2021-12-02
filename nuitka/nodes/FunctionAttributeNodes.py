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
""" Function attribute nodes

The represent special values of the modules. The "__qualname__" value node
is intended and to be resolved later. And the function output for error
messages, is also dynamic.

These nodes are intended to allow for as much compile time optimization as
possible, despite this difficulty. In some modes these node become constants
quickly, in others they will present boundaries for optimization.

"""

from .ExpressionBases import (
    CompileTimeConstantExpressionBase,
    ExpressionChildHavingBase,
)
from .NodeBases import SideEffectsFromChildrenMixin
from .NodeMakingHelpers import makeConstantReplacementNode


class ExpressionFunctionQualnameRef(CompileTimeConstantExpressionBase):
    """Node for value __qualname__ of function or class.

    Notes:
        This is for Python 3.4 and higher only, where classes calculate the __qualname__
        value at runtime, then it's determined dynamically, while 3.3 set it more
        statically, and Python2 didn't have this feature at all.
    """

    kind = "EXPRESSION_FUNCTION_QUALNAME_REF"

    __slots__ = ("function_body",)

    def __init__(self, function_body, source_ref):
        CompileTimeConstantExpressionBase.__init__(self, source_ref=source_ref)

        self.function_body = function_body

    def finalize(self):
        del self.parent
        del self.function_body

    def computeExpressionRaw(self, trace_collection):
        result = makeConstantReplacementNode(
            node=self,
            constant=self.function_body.getFunctionQualname(),
            user_provided=True,
        )

        return (
            result,
            "new_constant",
            "Executed '__qualname__' resolution to '%s'."
            % self.function_body.getFunctionQualname(),
        )

    def getCompileTimeConstant(self):
        return self.function_body.getFunctionQualname()


class ExpressionFunctionErrorStr(
    SideEffectsFromChildrenMixin, ExpressionChildHavingBase
):
    """Node for value "_PyObject_FunctionStr" C-API of function or callable in general.

    Notes:
        This is for Python 3.9 and higher only, where functions have their module
        added to the "__qualname__" value at runtime.
    """

    kind = "EXPRESSION_FUNCTION_ERROR_STR"

    named_child = "value"

    def __init__(self, value, source_ref):
        ExpressionChildHavingBase.__init__(self, value, source_ref=source_ref)

    def mayRaiseException(self, exception_type):
        return self.subnode_value.mayRaiseException(exception_type)

    def computeExpression(self, trace_collection):
        # TODO: Could compile time compute these for concrete functions.
        return self, None, None
