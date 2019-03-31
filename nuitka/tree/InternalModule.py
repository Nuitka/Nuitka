#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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


from nuitka.nodes.FunctionNodes import ExpressionFunctionBody
from nuitka.nodes.ModuleNodes import PythonInternalModule
from nuitka.SourceCodeReferences import fromFilename

internal_source_ref = fromFilename("internal").atInternal()


def once_decorator(func):
    """ Cache result of a function call without arguments.

    Used for all internal function accesses to become a singleton.

    Note: This doesn't much specific anymore, but we are not having
    this often enough to warrant re-use or generalization.

    """

    func.cached_value = None

    def replacement():
        if func.cached_value is None:
            func.cached_value = func()

        return func.cached_value

    return replacement


@once_decorator
def getInternalModule():
    """ Get the singleton internal module.

    """

    return PythonInternalModule()


def makeInternalHelperFunctionBody(name, parameters):
    return ExpressionFunctionBody(
        provider=getInternalModule(),
        name=name,
        code_object=None,
        doc=None,
        parameters=parameters,
        flags=set(),
        source_ref=internal_source_ref,
    )
