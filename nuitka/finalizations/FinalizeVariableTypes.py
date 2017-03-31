#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Determine types of variables for code generation. """

from nuitka.__past__ import iterItems

from .FinalizeBase import FinalizationVisitorBase


class FinalizeVariableTypes(FinalizationVisitorBase):
    def onEnterNode(self, provider):
        all_traces = provider.trace_collection.getVariableTracesAll()

        # We can have a C union for all versions of a variable, each one
        # indicating a type. Not every version needs its own type, e.g.
        # those without references do not. But initially they will get
        # one, since frame building, etc. do not properly count as any
        # reference.
        # We will use "None" for versions with no value, "void" C.

        variable_types = {}

        for (variable, version), variable_trace in iterItems(all_traces):
            if variable_trace.isUninitTrace():
                # No contribution from there. TODO: In fact we have too
                # many of those around.
                variable_types[variable, version] = None
            elif variable_trace.isInitTrace():
                variable_types[variable, version] = "PyObject *"
            elif variable_trace.isUnknownTrace():
                variable_types[variable, version] = "PyObject *"
            elif variable_trace.isMergeTrace():
                variable_types[variable, version] = "PyObject *"
            else:
                type_shape = variable_trace.getAssignNode().getAssignSource().getTypeShape()

                variable_types[variable, version] = type_shape.getCType()
