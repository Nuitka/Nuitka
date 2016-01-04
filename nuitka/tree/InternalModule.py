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
""" Internal module

This is a container for helper functions that are shared across modules. It
may not exist, and is treated specially in code generation. This avoids to
own these functions to a random module.
"""


from nuitka.nodes.ModuleNodes import PythonInternalModule
from nuitka.SourceCodeReferences import fromFilename
from nuitka.VariableRegistry import addVariableUsage

internal_module = None

internal_source_ref = fromFilename("internal").atInternal()

# Cache result.
def once_decorator(func):
    func.cached_value = None

    def replacement():
        if func.cached_value is None:
            func.cached_value = func()

        for variable in func.cached_value.getVariables():
            addVariableUsage(variable, func.cached_value)

        return func.cached_value

    return replacement


def getInternalModule():
    # Using global here, as this is really a about the internal module as a
    # singleton, pylint: disable=W0603
    global internal_module

    if internal_module is None:
        internal_module = PythonInternalModule()

    return internal_module
