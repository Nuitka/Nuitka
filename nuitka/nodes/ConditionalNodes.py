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

    def computeNode( self ):
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
