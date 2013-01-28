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
""" Conditional nodes.

These is the conditional expression '(a if b else c)' and the conditional statement, that
would be 'if a: ... else: ...' and there is no 'elif', because that is expressed via
nesting of conditional statements.
"""

from .NodeBases import CPythonExpressionChildrenHavingBase


class CPythonExpressionConditional( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_CONDITIONAL"

    named_children = ( "condition", "expression_yes", "expression_no" )

    def __init__( self, condition, yes_expression, no_expression, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "condition"      : condition,
                "expression_yes" : yes_expression,
                "expression_no"  : no_expression
            },
            source_ref = source_ref
        )

    def getBranches( self ):
        return ( self.getExpressionYes(), self.getExpressionNo() )

    getExpressionYes = CPythonExpressionChildrenHavingBase.childGetter( "expression_yes" )
    getExpressionNo = CPythonExpressionChildrenHavingBase.childGetter( "expression_no" )
    getCondition = CPythonExpressionChildrenHavingBase.childGetter( "condition" )

    def computeNode( self, constraint_collection ):
        condition = self.getCondition()

        # TODO: Actually really want to check the truth value only, not constant ness.
        if condition.isCompileTimeConstant():
            if condition.getCompileTimeConstant():
                return (
                    self.getExpressionYes(),
                    "new_expression",
                    "Conditional expression predicted to yes case"
                )
            else:
                return (
                    self.getExpressionNo(),
                    "new_expression",
                    "Conditional expression predicted to no case"
                )
        else:
            return self, None, None

    def mayHaveSideEffectsBool( self, constraint_collection ):
        if condition.mayHaveSideEffectsBool( constraint_collection ):
            return True

        if self.getExpressionYes().mayHaveSideEffectsBool( constraint_collection ):
            return True

        if self.getExpressionNo().mayHaveSideEffectsBool( constraint_collection ):
            return True

        return False

    def mayProvideReference( self ):
        return self.getExpressionYes().mayProvideReference() or self.getExpressionNo().mayProvideReference()


class CPythonStatementConditional( CPythonExpressionChildrenHavingBase ):
    kind = "STATEMENT_CONDITIONAL"

    named_children = ( "condition", "yes_branch", "no_branch" )

    def __init__( self, condition, yes_branch, no_branch, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "condition"  : condition,
                "yes_branch" : yes_branch,
                "no_branch"  : no_branch
            },
            source_ref = source_ref
        )

    getCondition = CPythonExpressionChildrenHavingBase.childGetter( "condition" )
    getBranchYes = CPythonExpressionChildrenHavingBase.childGetter( "yes_branch" )
    setBranchYes = CPythonExpressionChildrenHavingBase.childSetter( "yes_branch" )
    getBranchNo = CPythonExpressionChildrenHavingBase.childGetter( "no_branch" )
    setBranchNo = CPythonExpressionChildrenHavingBase.childSetter( "no_branch" )

    def isStatementAbortative( self ):
        yes_branch = self.getBranchYes()

        if yes_branch is not None and not yes_branch.isStatementAbortative():
            return False

        no_branch = self.getBranchNo()

        if no_branch is not None and not no_branch.isStatementAbortative():
            return False

        assert yes_branch is not None or no_branch is not None

        return yes_branch is not None and no_branch is not None
