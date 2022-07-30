#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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

nuitka.Options.is_full_compat = False

# isort:start

import nuitka.code_generation.BinaryOperationHelperDefinitions
import nuitka.code_generation.ComparisonCodes
import nuitka.code_generation.Namify
import nuitka.specs.BuiltinBytesOperationSpecs
import nuitka.specs.BuiltinDictOperationSpecs
import nuitka.specs.BuiltinStrOperationSpecs
from nuitka.utils.Jinja2 import getTemplate

from .Common import (
    formatArgs,
    getMethodVariations,
    python2_dict_methods,
    python2_str_methods,
    python3_bytes_methods,
    python3_dict_methods,
    python3_str_methods,
    withFileOpenedAndAutoFormatted,
    writeLine,
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

# How to test for argument name presence
attribute_shape_arg_tests = {}


def processTypeShapeAttribute(
    shape_name, spec_module, python2_methods, python3_methods
):
    for method_name in python2_methods:
        attribute_information.setdefault(method_name, set()).add(shape_name)
        key = method_name, shape_name

        if method_name not in python3_methods:
            attribute_shape_versions[key] = "str is bytes"

        (
            present,
            arg_names,
            arg_tests,
            arg_name_mapping,
            arg_counts,
        ) = getMethodVariations(
            spec_module=spec_module, shape_name=shape_name, method_name=method_name
        )

        attribute_shape_operations[key] = present

        if present:
            attribute_shape_args[key] = tuple(arg_names)
            attribute_shape_arg_tests[key] = arg_tests

            if len(arg_counts) > 1:
                attribute_shape_variations[key] = arg_counts

            attribute_shape_node_arg_mapping[key] = arg_name_mapping

    for method_name in python3_methods:
        attribute_information.setdefault(method_name, set()).add(shape_name)
        key = method_name, shape_name

        if method_name not in python2_methods:
            attribute_shape_versions[key] = "str is not bytes"

        (
            present,
            arg_names,
            arg_tests,
            arg_name_mapping,
            arg_counts,
        ) = getMethodVariations(
            spec_module=spec_module, shape_name=shape_name, method_name=method_name
        )

        attribute_shape_operations[key] = present

        if present:
            attribute_shape_args[key] = tuple(arg_names)
            attribute_shape_arg_tests[key] = arg_tests

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

processTypeShapeAttribute(
    "tshape_bytes",
    nuitka.specs.BuiltinBytesOperationSpecs,
    (),
    python3_bytes_methods,
)

attribute_shape_empty = {}

attribute_shape_empty[
    "update", "tshape_dict"
] = """\
lambda source_ref: wrapExpressionWithNodeSideEffects(
    new_node=makeConstantRefNode(
        constant=None,
        source_ref=source_ref
    ),
    old_node=dict_arg
)
"""


def emitGenerationWarning(emit, template_name):
    attribute_code_names = set(attribute_information.keys())
    attribute_code_names = set(
        attribute_name.replace("_", "") for attribute_name in attribute_information
    )

    attribute_arg_names = set(sum(attribute_shape_args.values(), ()))

    emit(
        '''
# pylint: disable=too-many-lines
# pylint: disable=line-too-long

"""Specialized attribute nodes

WARNING, this code is GENERATED. Modify the template %s instead!

spell-checker: ignore %s
spell-checker: ignore %s
"""

'''
        % (
            template_name,
            " ".join(sorted(attribute_code_names)),
            " ".join(sorted(attribute_arg_names)),
        )
    )


def formatCallArgs(operation_node_arg_mapping, args, starting=True):
    def mapName(arg):
        if not operation_node_arg_mapping:
            return arg
        else:
            return operation_node_arg_mapping.get(arg, arg)

    def mapValue(arg):
        if arg == "pairs":
            return "makeKeyValuePairExpressionsFromKwArgs(pairs)"
        else:
            return arg

    if args is None:
        result = ""
    else:
        result = ",".join("%s=%s" % (mapName(arg), mapValue(arg)) for arg in args)

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

    with withFileOpenedAndAutoFormatted(filename_python) as output_python:

        def emit(*args):
            writeLine(output_python, *args)

        emitGenerationWarning(emit, template.name)

        emit("from .AttributeLookupNodes import ExpressionAttributeLookupFixedBase")
        emit("from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs")

        emit("from nuitka.nodes.ConstantRefNodes import makeConstantRefNode")
        emit(
            "from nuitka.nodes.NodeMakingHelpers import wrapExpressionWithNodeSideEffects"
        )

        emit(
            "from nuitka.nodes.KeyValuePairNodes import makeKeyValuePairExpressionsFromKwArgs"
        )

        emit("from nuitka.nodes.AttributeNodes import makeExpressionAttributeLookup")

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
                attribute_shape_arg_tests=attribute_shape_arg_tests,
                attribute_shape_empty=attribute_shape_empty,
                formatArgs=formatArgs,
                formatCallArgs=formatCallArgs,
                reversed=reversed,
                name=template.name,
            )

            emit(code)


def main():
    makeAttributeNodes()
