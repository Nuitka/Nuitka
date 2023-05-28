#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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

from nuitka import Options
from nuitka.ModuleRegistry import getDoneModules
from nuitka.Tracing import general

graph = None
computation_counters = {}

progressive = False


def _addModuleGraph(module, desc):
    module_graph = module.asGraph(graph, desc)

    return module_graph


def onModuleOptimizationStep(module):
    # Update the graph if active.
    if graph is not None:
        computation_counters[module] = computation_counters.get(module, 0) + 1

        if progressive:
            _addModuleGraph(module, computation_counters[module])


def startGraph():
    # We maintain this globally to make it accessible, pylint: disable=global-statement
    global graph

    if Options.shallCreateGraph():
        try:
            from pygraphviz import AGraph  # pylint: disable=I0021,import-error

            graph = AGraph(name="Optimization", directed=True)
            graph.layout()
        except ImportError:
            general.sysexit("Cannot import pygraphviz module, no graphing capability.")


def endGraph(output_filename):
    if graph is not None:
        for module in getDoneModules():
            _addModuleGraph(module, "final")

        graph.draw(output_filename + ".dot", prog="dot")
