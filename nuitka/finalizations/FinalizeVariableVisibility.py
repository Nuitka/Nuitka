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
""" Finalize the variable visibility.

In order to declare variables with minimum scope in the generated code, we need
to find the common ancestor statement and attach it to the variable for
declaration.
"""


from .FinalizeBase import FinalizationVisitorBase

def selectStatement(one, two, mode):
    merge = []

    for c1, c2 in zip( one, two ):
        if c1 is not c2:
            break

        merge.append( c1 )

    # print( "M", merge )
    # If it's both in an expression, go up until it's a statement.
    if merge[-1].isExpression():
        while merge[-1].isExpression():
            del merge[-1]
    elif merge[-1].isStatementsSequence():
        if len( one ) > len( merge ):
            c1 = one[ len( merge )  ]
            c2 = two[ len( merge )  ]

            statements = merge[-1].getStatements()
            if statements.index( c1 ) < statements.index( c2 ):
                merge.append( c1 if mode else c2 )
            else:
                merge.append( c2 if mode else c1 )

    assert None not in merge

    return merge

class FinalizeVariableVisibility(FinalizationVisitorBase):
    def onEnterNode(self, node):
        collection = node.collection

        assert collection is not None, node

        # TODO: This could easily be expanded to all variables.
        for variable in node.getTempVariables():
            variable_traces = collection.getVariableTraces( variable )

            uses = set()

            # Will remain "None" only if no assignments are done, which is
            # probably an error for at least temporary variables.
            needs_free = None

            for variable_trace in variable_traces:
                # Safe to ignore this likely, although the merge point may be
                # important, but it should come up as potential use.
                if variable_trace.isMergeTrace():
                    continue

                for use in variable_trace.getPotentialUsages():
                    if use.__class__.__name__.startswith("VariableMerge"):
                        continue

                    uses.add( use )

                if variable_trace.isAssignTrace():
                    assign_node = variable_trace.getAssignNode()

                    uses.add( assign_node.getTargetVariableRef() )

                    # In preparation for code generation, we are here checking
                    # if it's required to hold a reference in this variable,
                    # because if it is not, we can create faster code.
                    if assign_node.getAssignSource().mayProvideReference():
                        needs_free = True
                    elif needs_free is None:
                        needs_free = False

                for use in variable_trace.getReleases():
                    uses.add( use )

            # For temporary variables, we can expect to know that as it should
            # have been removed, if it's without assignments or if it has
            # references left-over, these would be bogus and should be converted
            # to some form of raise or assertion previously.
            assert needs_free is not None or not uses, variable
            assert variable.getNeedsFree() is None
            variable.setNeedsFree( needs_free )

            # Determine the first and last useing statements for a variable,
            # which means for scopes that late initialisation might be used, or
            # RAII style release.
            first = None
            last = None

            for use in uses:
                other = use.getParents()

                if first is None:
                    first = other
                else:
                    first = selectStatement( first, other, True )

                if last is None:
                    last = other
                else:
                    last = selectStatement( last, other, False )

            if first is not None and first[-1].isStatementAssignmentVariable():
                assigned_to = first[-1].getTargetVariableRef().getVariable()

                if assigned_to.isReference():
                    assigned_to = assigned_to.getReferenced()

                assert assigned_to is variable, ( variable, assigned_to )

                if not variable.isShared():
                    variable.markAsNeedsLateDeclaration()

                    assert last is not None

                    if last[-1].isStatementDelVariable():
                        variable.markAsDeleteScope( last[-1] )
