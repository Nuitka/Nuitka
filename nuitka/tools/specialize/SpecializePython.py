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
import nuitka.specs.BuiltinStrOperationSpecs
from nuitka.utils.Jinja2 import getTemplate

from .Common import (
    formatArgs,
    getMethodVariations,
    python2_dict_methods,
    python2_str_methods,
    python3_dict_methods,
    python3_str_methods,
    withFileOpenedAndAutoformatted,
    writeline,
)

# This defines which attribute nodes are to specialize and how
# to do that.
attribute_information = {}

# Which ones have operations implemented.
attribute_shape_operations = {}

# Version specific tests for attributes.
attribute_shape_versions = {}

# Argument count specific operation nodes if used.
attribute_shape_variations = {}

# Arguments names differences in spec vs. node
attribute_shape_node_arg_mapping = {}

# Argument names of an operation.
attribute_shape_args = {}


def processTypeShapeAttribute(
    shape_name, spec_module, python2_methods, python3_methods
):
    for method_name in python2_methods:
        attribute_information.setdefault(method_name, set()).add(shape_name)
        key = method_name, shape_name

        if method_name not in python3_methods:
            attribute_shape_versions[key] = "str is bytes"

        present, arg_names, arg_name_mapping, arg_counts = getMethodVariations(
            spec_module=spec_module, shape_name=shape_name, method_name=method_name
        )

        attribute_shape_operations[key] = present

        if present:
            attribute_shape_args[key] = arg_names

            if len(arg_counts) > 1:
                attribute_shape_variations[key] = arg_counts

            attribute_shape_node_arg_mapping[key] = arg_name_mapping

    for method_name in python3_methods:
        attribute_information.setdefault(method_name, set()).add(shape_name)
        key = method_name, shape_name

        if method_name not in python2_methods:
            attribute_shape_versions[key] = "str is not bytes"

        present, arg_names, arg_name_mapping, arg_counts = getMethodVariations(
            spec_module=spec_module, shape_name=shape_name, method_name=method_name
        )

        attribute_shape_operations[key] = present

        if present:
            attribute_shape_args[key] = arg_names

            if len(arg_counts) > 1:
                attribute_shape_variations[key] = arg_counts

            attribute_shape_node_arg_mapping[key] = arg_name_mapping


processTypeShapeAttribute(
    "tshape_dict",
    nuitka.specs.BuiltinDictOperationSpecs,
    python2_dict_methods,
    python3_dict_methods,
)


processTypeShapeAttribute(
    "tshape_str",
    nuitka.specs.BuiltinStrOperationSpecs,
    python2_str_methods,
    python3_str_methods,
)


def emitGenerationWarning(emit, template_name):
    emit(
        '''"""Specialized attribute nodes

WARNING, this code is GENERATED. Modify the template %s instead!
"""
'''
        % template_name
    )


def formatCallArgs(operation_node_arg_mapping, args, starting=True):
    def mapName(arg):
        if not operation_node_arg_mapping:
            return arg
        else:
            return operation_node_arg_mapping.get(arg, arg)

    if args is None:
        result = ""
    else:
        result = ",".join("%s=%s" % (mapName(arg), arg) for arg in args)

    if not starting and result:
        result = "," + result

    # print("args", args, "->", result)

    return result


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
        emit("attribute_typed_classes = set()")

        for attribute_name, shape_names in sorted(attribute_information.items()):
            # Some attributes lead to different operations for Python3.
            if attribute_name == "items":
                python3_operation_name = "iteritems"
            elif attribute_name == "keys":
                python3_operation_name = "iterkeys"
            elif attribute_name == "values":
                python3_operation_name = "itervalues"
            else:
                python3_operation_name = None

            code = template.render(
                attribute_name=attribute_name,
                python3_operation_name=python3_operation_name,
                shape_names=shape_names,
                attribute_shape_versions=attribute_shape_versions,
                attribute_shape_operations=attribute_shape_operations,
                attribute_shape_variations=attribute_shape_variations,
                attribute_shape_node_arg_mapping=attribute_shape_node_arg_mapping,
                attribute_shape_args=attribute_shape_args,
                formatArgs=formatArgs,
                formatCallArgs=formatCallArgs,
                reversed=reversed,
                name=template.name,
            )

            emit(code)


def main():
    makeAttributeNodes()
