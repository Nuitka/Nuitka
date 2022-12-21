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
import nuitka.specs.HardImportSpecs
from nuitka.utils.Jinja2 import getTemplate

from .Common import (
    formatArgs,
    getMethodVariations,
    getSpecs,
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


def emitGenerationWarning(emit, doc_string, template_name):
    attribute_code_names = set(attribute_information.keys())
    attribute_code_names = set(
        attribute_name.replace("_", "") for attribute_name in attribute_information
    )

    attribute_arg_names = set(sum(attribute_shape_args.values(), ()))

    emit(
        '''
# pylint: disable=I0021,too-many-lines
# pylint: disable=I0021,line-too-long

"""%s

WARNING, this code is GENERATED. Modify the template %s instead!

spell-checker: ignore %s
spell-checker: ignore %s
"""

'''
        % (
            doc_string,
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

        emitGenerationWarning(emit, "Specialized attribute nodes", template.name)

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


def adaptModuleName(value):
    if value == "importlib_metadata":
        return "importlib_metadata_backport"

    return value


def makeTitleCased(value):
    return "".join(s.title() for s in value.split("_")).replace(".", "")


def makeCodeCased(value):
    return value.replace(".", "_")


def getCallModuleName(module_name, function_name):
    if module_name in ("pkg_resources", "importlib.metadata", "importlib_metadata"):
        return "PackageMetadataNodes"

    assert False, (module_name, function_name)


def getCallModulePrefix(module_name, function_name):
    if module_name in ("importlib.metadata", "importlib_metadata"):
        if function_name == "metadata":
            return "make"

    return ""


def makeMixinName(named_children, named_children_types):
    def _addType(name):
        if name in named_children_types:
            return name + "_" + named_children_types[name].title()
        else:
            return name

    mixin_name = "".join(
        makeTitleCased(_addType(named_child)) for named_child in named_children
    )

    return mixin_name


children_mixins = []


def addChildrenMixin(named_children, named_children_types, named_children_checkers):
    children_mixins.append(
        (named_children, named_children_types, named_children_checkers)
    )


# tuple having container creations
addChildrenMixin(("elements",), {"elements": "tuple"}, {})
addChildrenMixin(("pairs",), {"pairs": "tuple"}, {})

# ExpressionBuiltinMakeException
addChildrenMixin(("args",), {"args": "tuple"}, {})
# ExpressionStringConcatenation
addChildrenMixin(("values",), {"values": "tuple"}, {})

# ExpressionSliceLookup
addChildrenMixin(
    ("expression", "lower", "upper"),
    {},
    {"upper": "convertNoneConstantToNone", "lower": "convertNoneConstantToNone"},
)


def makeChildrenHavingMixinNodes():
    filename_python = "nuitka/nodes/ChildrenHavingMixins.py"

    template = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="ChildrenHavingMixin.py.j2",
    )

    mixins_done = set()

    with withFileOpenedAndAutoFormatted(filename_python) as output_python:

        def emit(*args):
            writeLine(output_python, *args)

        emitGenerationWarning(emit, "Children having mixins", template.name)

        emit("""# Loop unrolling over child names, pylint: disable=too-many-branches""")

        emit(
            """
def convertNoneConstantToNone(node):
    if node is None or node.isExpressionConstantNoneRef():
        return None
    else:
        return node
"""
        )

        for named_children, named_children_types, named_children_checkers in sorted(
            children_mixins
        ):
            assert named_children
            mixin_name = makeMixinName(named_children, named_children_types)

            if mixin_name in mixins_done:
                continue

            code = template.render(
                name=template.name,
                mixin_name=mixin_name,
                named_children=named_children,
                named_children_types=named_children_types,
                named_children_checkers=named_children_checkers,
                single_child=len(named_children) == 1,
            )

            emit(code)

            mixins_done.add(mixin_name)


def makeHardImportNodes():
    filename_python = "nuitka/nodes/HardImportNodesGenerated.py"

    template = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="HardImportReferenceNode.py.j2",
    )

    with withFileOpenedAndAutoFormatted(filename_python) as output_python:

        def emit(*args):
            writeLine(output_python, *args)

        emitGenerationWarning(emit, "Hard import nodes", template.name)

        emit(
            """
hard_import_node_classes = {}

"""
        )

        for spec_name, spec in getSpecs(nuitka.specs.HardImportSpecs):
            named_children_types = {}

            if spec.name == "pkg_resources.require":
                named_children_types["requirements"] = "tuple"

            named_children_checkers = {}

            module_name, function_name = spec.name.rsplit(".", 1)
            code = template.render(
                name=template.name,
                mixin_name=makeMixinName(
                    spec.getParameterNames(), named_children_types
                ),
                parameter_names_count=len(spec.getParameterNames()),
                parameter_names=spec.getParameterNames(),
                argument_names=spec.getArgumentNames(),
                start_list_argument_name=spec.getStarListArgumentName(),
                function_name=function_name,
                function_name_title=makeTitleCased(function_name),
                function_name_code=makeCodeCased(function_name),
                module_name=module_name,
                module_name_code=makeCodeCased(adaptModuleName(module_name)),
                module_name_title=makeTitleCased(adaptModuleName(module_name)),
                call_node_module_name=getCallModuleName(module_name, function_name),
                call_node_prefix=getCallModulePrefix(module_name, function_name),
                spec_name=spec_name,
            )

            children_mixins.append(
                (
                    spec.getParameterNames(),
                    named_children_types,
                    named_children_checkers,
                )
            )

            emit(code)


def main():
    makeHardImportNodes()
    makeChildrenHavingMixinNodes()
    makeAttributeNodes()
