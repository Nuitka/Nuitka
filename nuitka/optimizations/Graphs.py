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
""" Graph optimization states.

These are not the graphs you might be thinking of. This is for rending the
progress of optimization into images.
"""

from logging import warning

from nuitka import Options
from nuitka.Tracing import printLine

graph = None
computation_counters = {}


def onModuleOptimizationStep(module):
    # Update the graph if active.
    if graph is not None:
        computation_counters[module] = computation_counters.get(module, 0) + 1
        module_graph = module.asGraph(computation_counters[module])

        graph.subgraph(module_graph)


def startGraph():
    # We maintain this globally to make it accessible, pylint: disable=W0603
    global graph

    if Options.shouldCreateGraph():
        try:
            from graphviz import Digraph # pylint: disable=F0401,I0021
            graph = Digraph('G')
        except ImportError:
            warning("Cannot import graphviz module, no graphing capability.")


def endGraph():
    if graph is not None:
        graph.engine = "dot"
        graph.graph_attr["rankdir"] = "TB"
        graph.render("something.dot")

        printLine(graph.source)
