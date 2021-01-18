#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

TODO: Clarify by renaming that the top module is now used, and these are
merely helpers to do it.
"""


from nuitka.ModuleRegistry import getRootTopModule
from nuitka.nodes.FunctionNodes import (
    ExpressionFunctionBody,
    ExpressionFunctionPureBody,
)
from nuitka.SourceCodeReferences import fromFilename

internal_source_ref = fromFilename("internal").atInternal()


def once_decorator(func):
    """Cache result of a function call without arguments.

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
    """Get the singleton internal module."""

    return getRootTopModule()


def makeInternalHelperFunctionBody(name, parameters, inline_const_args=False):
    if inline_const_args:
        node_class = ExpressionFunctionPureBody
    else:
        node_class = ExpressionFunctionBody

    result = node_class(
        provider=getInternalModule(),
        name=name,
        code_object=None,
        doc=None,
        parameters=parameters,
        flags=None,
        auto_release=None,
        source_ref=internal_source_ref,
    )

    for variable in parameters.getAllVariables():
        result.removeVariableReleases(variable)

    return result
