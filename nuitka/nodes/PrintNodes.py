#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Print nodes.

Right now there is only the print statement, but in principle, there should
also be the print function here. These perform output, which can be combined
if possible, and could be detected to fail, which would be perfect.

Predicting the behavior of 'print' is not trivial at all, due to many special
cases.
"""

from .HardImportNodesGenerated import (
    ExpressionBuiltinsPrintBefore3CallBase,
    ExpressionBuiltinsPrintSince3Call1Base,
    ExpressionBuiltinsPrintSince3CallBase,
)
from .NodeMakingHelpers import (
    makeStatementExpressionOnlyReplacementNode,
    makeStatementsSequenceReplacementNode,
)
from .shapes.BuiltinTypeShapes import tshape_none
from .StatementBasesGenerated import (
    StatementPrintNewlineBase,
    StatementPrintValueBase,
)


class StatementPrintValue(StatementPrintValueBase):
    kind = "STATEMENT_PRINT_VALUE"

    named_children = ("dest|optional", "value|setter")
    auto_compute_handling = "operation"

    python_version_spec = "< 0x300"

    def computeStatementOperation(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        if self.subnode_dest is None and self.subnode_value.isExpressionSideEffects():
            self.setChildValue(self.subnode_value.value.subnode_expression)

            statements = [
                makeStatementExpressionOnlyReplacementNode(side_effect, self)
                for side_effect in self.subnode_value.value.subnode_side_effects
            ]

            statements.append(self)

            result = makeStatementsSequenceReplacementNode(
                statements=statements, node=self
            )

            return (
                result,
                "new_statements",
                """\
Side effects printed item promoted to statements.""",
            )

        if (
            self.subnode_value.isCompileTimeConstant()
            and not self.subnode_value.hasShapeStrOrUnicodeExact()
        ):
            # Avoid unicode encoding issues.
            new_value = self.subnode_value.getStrValue()
            assert new_value is not None, self.subnode_value

            self.setChildValue(new_value)

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        # Output may always fail due to external reasons.
        return True


class StatementPrintNewline(StatementPrintNewlineBase):
    kind = "STATEMENT_PRINT_NEWLINE"

    named_children = ("dest|optional",)
    python_version_spec = "< 0x300"
    auto_compute_handling = "operation"

    def computeStatementOperation(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        # Output may always fail due to external reasons.
        return True


class ExpressionBuiltinsPrintSince3Call1(ExpressionBuiltinsPrintSince3Call1Base):
    kind = "EXPRESSION_BUILTINS_PRINT_SINCE3_CALL1"

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    def replaceWithCompileTimeValue(self, trace_collection):
        # TODO: Implement actual optimization logic
        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None

    def getTypeShape(self):
        return tshape_none


class ExpressionBuiltinsPrintSince3Call(ExpressionBuiltinsPrintSince3CallBase):
    kind = "EXPRESSION_BUILTINS_PRINT_SINCE3_CALL"

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    def replaceWithCompileTimeValue(self, trace_collection):
        # TODO: Implement actual optimization logic
        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None

    def getTypeShape(self):
        return tshape_none


def makeExpressionBuiltinsPrintSince3Call(objects, sep, end, file, flush, source_ref):
    if sep is None and end is None and file is None and flush is None:
        return ExpressionBuiltinsPrintSince3Call1(
            objects=objects, source_ref=source_ref
        )

    return ExpressionBuiltinsPrintSince3Call(
        objects=objects,
        sep=sep,
        end=end,
        file=file,
        flush=flush,
        source_ref=source_ref,
    )


class ExpressionBuiltinsPrintBefore3Call(ExpressionBuiltinsPrintBefore3CallBase):
    kind = "EXPRESSION_BUILTINS_PRINT_BEFORE3_CALL"

    @staticmethod
    def isExpressionBuiltinCall():
        return True

    def replaceWithCompileTimeValue(self, trace_collection):
        # TODO: Implement actual optimization logic
        trace_collection.onExceptionRaiseExit(BaseException)
        return self, None, None

    def getTypeShape(self):
        return tshape_none


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
