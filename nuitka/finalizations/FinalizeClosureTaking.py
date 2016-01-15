#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Finalize the closure.

If a taker wants a variable, make sure that the closure taker in between all do
forward it for this use or else it will not be available. We do this late so it
is easier to remove closure variables and keep track of references, by not
having it spoiled with these transitive only references.

"""

from nuitka.optimizations.Optimization import areEmptyTraces

from .FinalizeBase import FinalizationVisitorBase


class FinalizeClosureTaking(FinalizationVisitorBase):
    def onEnterNode(self, node):
        # print node, node.provider

        for variable in node.getClosureVariables():
            assert not variable.isModuleVariable()

            current = node

            while current is not variable.getOwner():
                if current.isParentVariableProvider():
                    if variable not in current.getClosureVariables():
                        current.addClosureVariable(variable)

                # Detect loops in the provider relationship
                assert current.getParentVariableProvider() is not current

                current = current.getParentVariableProvider()

                # Not found?!
                assert current is not None, variable


class FinalizeClassClosure(FinalizationVisitorBase):
    def onEnterNode(self, function_body):
        for closure_variable in function_body.getClosureVariables():
            if closure_variable.getName() not in ("__class__", "self"):
                continue

            variable_traces = function_body.constraint_collection.getVariableTraces(
                variable = closure_variable
            )

            empty = areEmptyTraces(variable_traces)
            if empty:
                function_body.removeClosureVariable(closure_variable)
