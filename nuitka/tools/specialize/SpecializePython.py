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
""" This tool is generating node variants from Jinja templates.

"""

import nuitka.Options

nuitka.Options.is_fullcompat = False

# isort:start

import nuitka.codegen.ComparisonCodes
import nuitka.codegen.HelperDefinitions
import nuitka.codegen.Namify
import nuitka.specs.BuiltinDictOperationSpecs
from nuitka.utils.Jinja2 import getTemplate

from .Common import withFileOpenedAndAutoformatted, writeline

# This defines which attribute nodes are to specialize and how
# to do that.
attribute_information = {}

# Which ones have operations implemented.
attribute_shape_operations = {}

# Version specific tests for attributes.
attribute_shape_versions = {}

# Argument count specific operation nodes if used.
attribute_shape_variations = {}

# Argument names of an operation.
attribute_shape_args = {}

# Python2 dict methods:
python2_dict_methods = (
    "clear",  # has full dict coverage
    "copy",  # has full dict coverage
    "fromkeys",
    "get",  # has full dict coverage
    "has_key",
    "items",  # has full dict coverage
    "iteritems",  # has full dict coverage
    "iterkeys",
    "itervalues",
    "keys",
    "pop",
    "popitem",
    "setdefault",
    "update",
    "values",
    "viewitems",
    "viewkeys",
    "viewvalues",
)
python3_dict_methods = (
    "clear",
    "copy",
    "fromkeys",
    "get",
    "items",
    "keys",
    "pop",
    "popitem",
    "setdefault",
    "update",
    "values",
)

for method_name in python2_dict_methods:
    attribute_information.setdefault(method_name, []).append("tshape_dict")

    key = method_name, "tshape_dict"
    if hasattr(nuitka.specs.BuiltinDictOperationSpecs, "dict_%s_spec" % method_name):
        attribute_shape_operations[key] = True
    else:
        attribute_shape_operations[key] = False

    if method_name not in python3_dict_methods:
        attribute_shape_versions[key] = "str is bytes"

    spec = getattr(
        nuitka.specs.BuiltinDictOperationSpecs, "dict_%s_spec" % method_name, None
    )

    if spec is not None:
        if spec.getDefaultCount():
            required = spec.getArgumentCount() - spec.getDefaultCount()

            attribute_shape_variations[key] = tuple(
                range(required, spec.getArgumentCount() + 1)
            )

        attribute_shape_args[key] = spec.getArgumentNames()


# Python3 dict methods must be present already.
for method_name in python3_dict_methods:
    assert "tshape_dict" in attribute_information.get(method_name, [])


def emitGenerationWarning(emit, template_name):
    emit(
        '''"""Specialized attribute nodes

WARNING, this code is GENERATED. Modify the template %s instead!
"""
'''
        % template_name
    )


def formatArgs(args, starting=True):
    result = []
    for arg in args:
        result.append(arg)

        if arg is not args[-1] or starting:
            result.append(",")

    return "".join(result)


def formatCallArgs(args):
    return ",".join("%s=%s" % (arg, arg) for arg in args)


def makeAttributeNodes():
    filename_python = "nuitka/nodes/AttributeNodesGenerated.py"

    template = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="AttributeNodeFixed.py.j2",
    )

    with withFileOpenedAndAutoformatted(filename_python) as output_python:

        def emit(*args):
            writeline(output_python, *args)

        emitGenerationWarning(emit, template.name)

        emit("from .AttributeLookupNodes import ExpressionAttributeLookupFixedBase")
        emit("from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs")

        # TODO: Maybe generate its effect instead of using a base class.
        emit("from .NodeBases import SideEffectsFromChildrenMixin")

        emit("attribute_classes = {}")
        emit("attribute_typed_classes = {}")

        for attribute_name, shape_names in sorted(attribute_information.items()):
            # Some attributes lead to different operations for Python3.
            if attribute_name == "items":
                python3_operation_name = "iteritems"
            elif attribute_name == "keys":
                python3_operation_name = "viewkeys"
            else:
                python3_operation_name = None

            code = template.render(
                attribute_name=attribute_name,
                python3_operation_name=python3_operation_name,
                shape_names=shape_names,
                attribute_shape_versions=attribute_shape_versions,
                attribute_shape_operations=attribute_shape_operations,
                attribute_shape_variations=attribute_shape_variations,
                attribute_shape_args=attribute_shape_args,
                formatArgs=formatArgs,
                formatCallArgs=formatCallArgs,
                reversed=reversed,
                name=template.name,
            )

            emit(code)


def main():
    makeAttributeNodes()
