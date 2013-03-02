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
""" Loop nodes.

There are for and loop nodes, and the break/continue statements for it. Loops are a very
difficult topic, and it might be that the two forms need to be reduced to one common form,
which is more general, the 'Forever' loop, with breaks

"""

from .NodeBases import (
    StatementChildrenHavingBase,
    NodeBase
)


class StatementLoop( StatementChildrenHavingBase ):
    kind = "STATEMENT_LOOP"

    named_children = ( "frame", )

    def __init__( self, body, source_ref ):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "frame" : body
            },
            source_ref = source_ref
        )

        self.break_exception = False
        self.continue_exception = False

    getLoopBody = StatementChildrenHavingBase.childGetter( "frame" )

    def markAsExceptionContinue( self ):
        self.continue_exception = True

    def markAsExceptionBreak( self ):
        self.break_exception = True

    def needsExceptionContinue( self ):
        return self.continue_exception

    def needsExceptionBreak( self ):
        return self.break_exception

    def computeStatement( self, constraint_collection ):
        from nuitka.optimizations.ConstraintCollections import ConstraintCollectionLoopOther

        other_loop_run = ConstraintCollectionLoopOther( constraint_collection )
        other_loop_run.process( self )

        constraint_collection.mergeBranch(
            other_loop_run
        )

        return self, None, None


class StatementContinueLoop( NodeBase ):
    kind = "STATEMENT_CONTINUE_LOOP"

    def __init__( self, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

        self.exception_driven = False

    def isStatementAborting( self ):
        return True

    def markAsExceptionDriven( self ):
        self.exception_driven = True

    def isExceptionDriven( self ):
        return self.exception_driven

    def computeStatement( self, constraint_collection ):
        # This statement being aborting, will already tell everything. TODO: The fine
        # difference that this jumps to loop start for sure, should be represented somehow
        # one day.
        return self, None, None


class StatementBreakLoop( NodeBase ):
    kind = "STATEMENT_BREAK_LOOP"

    def __init__( self, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )

        self.exception_driven = False

    def isStatementAborting( self ):
        return True

    def markAsExceptionDriven( self ):
        self.exception_driven = True

    def isExceptionDriven( self ):
        return self.exception_driven

    def computeStatement( self, constraint_collection ):
        # This statement being aborting, will already tell everything. TODO: The fine
        # difference that this exits the loop for sure, should be represented somehow one
        # day.
        return self, None, None
