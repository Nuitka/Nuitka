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
""" Finalize the variable visibility.

In order to declare variables with minimum scope in the generated code, we need
to find the common ancestor statement and attach it to the variable for
declaration.
"""


from .FinalizeBase import FinalizationVisitorBase

class FinalizeVariableVisibility( FinalizationVisitorBase ):
    def onEnterNode( self, node ):
        collection = node.collection

        assert collection is not None, node

        # TODO: This could easily be expanded to all variables.
        for variable in node.getTempVariables():
            variable_traces = collection.getVariableTraces( variable )

            uses = set()

            for variable_trace in variable_traces:
                # Safe to ignore this likely, although the merge point may be
                # important, but it should come up as potential use.
                if variable_trace.isMergeTrace():
                    continue

                for use in variable_trace.getPotentialUsages():
                    if use.__class__.__name__.startswith( "VariableMerge" ):
                        continue

                    uses.add( use )

                if variable_trace.isAssignTrace():
                    uses.add( variable_trace.getAssignNode() )

                for use in variable_trace.getReleases():
                    uses.add( use )

            best = None
            for use in uses:
                other = use.getParents()

                if best is None:
                    best = other
                else:
                    merge = []

                    l = None

                    for b, o in zip( best, other ):
                        if b is not o:
                            break

                        merge.append( b )
                        l = b

                    while True:
                        if merge[-1].isStatement():
                            break
                        elif merge[-1].isStatementsSequence():
                            statements = merge[-1].getStatements()

                            # print use, best, other

                            c1 = best[ len( merge ) ]
                            c2 = other[ len( merge ) ]

                            if statements.index( c1 ) < statements.index( c2 ):
                                merge.append( c1 )
                            else:
                                merge.append( c2 )

                            break
                        elif merge[-1].isExpression():
                            while merge[-1].isExpression():
                                del merge[-1]
                        else:
                            assert False, merge[-1]

                    best = merge
                    assert None not in merge

            if best is not None and best[-1].isStatementAssignmentVariable():
                best[-1].getTargetVariableRef().getVariable().getReferenced().markAsNeedsLateDeclaration()
