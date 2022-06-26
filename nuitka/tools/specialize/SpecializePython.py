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

import sys
import nuitka.Options

nuitka.Options.is_full_compat = False

# isort:start

from collections import namedtuple

import nuitka.code_generation.BinaryOperationHelperDefinitions
import nuitka.code_generation.CodeGeneration
import nuitka.code_generation.ComparisonCodes
import nuitka.code_generation.Namify
import nuitka.nodes.PackageMetadataNodes
import nuitka.nodes.PackageResourceNodes
import nuitka.nodes.SideEffectNodes
import nuitka.specs.BuiltinBytesOperationSpecs
import nuitka.specs.BuiltinDictOperationSpecs
import nuitka.specs.BuiltinListOperationSpecs
import nuitka.specs.BuiltinStrOperationSpecs
import nuitka.specs.HardImportSpecs
import nuitka.tree.Building
from nuitka.nodes.ImportNodes import hard_modules_non_stdlib
from nuitka.nodes.NodeMetaClasses import NodeCheckMetaClass
from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_bytes,
    tshape_dict,
    tshape_int,
    tshape_list,
    tshape_none,
    tshape_str,
    tshape_tuple,
)
from nuitka.utils.Jinja2 import getTemplate

from .Common import (
    formatArgs,
    getMethodVariations,
    getSpecs,
    python2_dict_methods,
    python2_list_methods,
    python2_str_methods,
    python3_bytes_methods,
    python3_dict_methods,
    python3_list_methods,
    python3_str_methods,
    withFileOpenedAndAutoFormatted,
    writeLine,
)

# This defines which attribute nodes are to specialize and how
# to do that.
attribute_information = {}

# Which ones have operations implemented.
attribute_shape_operations = {}

# What result shape is known for the operation if used.
attribute_shape_operations_result_types = {}

# What mixing class should be used for the operation if used.
attribute_shape_operations_mixin_classes = {}

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

# Translations for node names.
node_factory_translations = {}


def _getMixinForShape(shape):
    # Return driven for better debugging experience, pylint: disable=too-many-return-statements

    if shape is tshape_str:
        return "nuitka.nodes.ExpressionShapeMixins.ExpressionStrShapeExactMixin"
    elif shape is tshape_list:
        return "nuitka.nodes.ExpressionShapeMixins.ExpressionListShapeExactMixin"
    elif shape is tshape_tuple:
        return "nuitka.nodes.ExpressionShapeMixins.ExpressionTupleShapeExactMixin"
    elif shape is tshape_int:
        return "nuitka.nodes.ExpressionShapeMixins.ExpressionIntShapeExactMixin"
    elif shape is tshape_bool:
        return "nuitka.nodes.ExpressionShapeMixins.ExpressionBoolShapeExactMixin"
    elif shape is tshape_none:
        return "nuitka.nodes.ExpressionShapeMixins.ExpressionNoneShapeExactMixin"
    elif shape is tshape_dict:
        return "nuitka.nodes.ExpressionShapeMixins.ExpressionDictShapeExactMixin"
    elif shape is tshape_bytes:
        return "nuitka.nodes.ExpressionShapeMixins.ExpressionBytesShapeExactMixin"
    else:
        assert False, shape


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
            result_shape,
        ) = getMethodVariations(
            spec_module=spec_module, shape_name=shape_name, method_name=method_name
        )

        attribute_shape_operations[key] = present
        attribute_shape_operations_result_types[key] = result_shape

        if result_shape is not None:
            attribute_shape_operations_mixin_classes[key] = [
                _getMixinForShape(result_shape)
            ]

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
            result_shape,
        ) = getMethodVariations(
            spec_module=spec_module, shape_name=shape_name, method_name=method_name
        )

        attribute_shape_operations[key] = present
        attribute_shape_operations_result_types[key] = result_shape

        if result_shape is not None:
            attribute_shape_operations_mixin_classes[key] = [
                _getMixinForShape(result_shape)
            ]

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

processTypeShapeAttribute(
    "tshape_list",
    nuitka.specs.BuiltinListOperationSpecs,
    python2_list_methods,
    python3_list_methods,
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
        """
# We are not avoiding these in generated code at all
# pylint: disable=I0021,too-many-lines
# pylint: disable=I0021,line-too-long
# pylint: disable=I0021,too-many-instance-attributes
# pylint: disable=I0021,too-many-return-statements
"""
    )

    emit(
        '''
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


def _getPython3OperationName(attribute_name):
    # Some attributes lead to different operations for Python3.
    if attribute_name == "items":
        return "iteritems"
    elif attribute_name == "keys":
        return "iterkeys"
    elif attribute_name == "values":
        return "itervalues"
    else:
        return None


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

            code = template.render(
                attribute_name=attribute_name,
                python3_operation_name=_getPython3OperationName(attribute_name),
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
                translateNodeClassName=translateNodeClassName,
                reversed=reversed,
                str=str,
                name=template.name,
            )

            emit(code)


def makeBuiltinOperationNodes():
    filename_python = "nuitka/nodes/BuiltinOperationNodeBasesGenerated.py"

    template = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="BuiltinOperationNodeBases.py.j2",
    )

    with withFileOpenedAndAutoFormatted(filename_python) as output_python:

        def emit(*args):
            writeLine(output_python, *args)

        emitGenerationWarning(emit, "Specialized attribute nodes", template.name)

        for attribute_name, shape_names in sorted(attribute_information.items()):
            attribute_name_class = attribute_name.replace("_", "").title()

            code = template.render(
                attribute_name=attribute_name,
                attribute_name_class=attribute_name_class,
                python3_operation_name=_getPython3OperationName(attribute_name),
                shape_names=shape_names,
                attribute_shape_versions=attribute_shape_versions,
                attribute_shape_operations=attribute_shape_operations,
                attribute_shape_variations=attribute_shape_variations,
                attribute_shape_node_arg_mapping=attribute_shape_node_arg_mapping,
                attribute_shape_args=attribute_shape_args,
                attribute_shape_arg_tests=attribute_shape_arg_tests,
                attribute_shape_empty=attribute_shape_empty,
                attribute_shape_operations_mixin_classes=attribute_shape_operations_mixin_classes,
                formatArgs=formatArgs,
                formatCallArgs=formatCallArgs,
                addChildrenMixin=addChildrenMixin,
                reversed=reversed,
                str=str,
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
        if function_name in ("resource_stream", "resource_string"):
            return "PackageResourceNodes"

        return "PackageMetadataNodes"
    if module_name in ("pkgutil", "importlib.resources"):
        return "PackageResourceNodes"
    if module_name in ("os", "sys", "os.path"):
        return "OsSysNodes"
    if module_name == "ctypes":
        return "CtypesNodes"

    assert False, (module_name, function_name)


def translateNodeClassName(node_class_name):
    return node_factory_translations.get(node_class_name, node_class_name)


def makeMixinName(
    is_expression,
    is_statement,
    named_children,
    named_children_types,
    named_children_checkers,
    auto_compute_handling,
    node_attributes,
):
    def _addType(name):
        if name in named_children_types:
            if (
                named_children_types[name] == "optional"
                and named_children_checkers.get(name) == "convertNoneConstantToNone"
            ):
                return ""

            return "_" + named_children_types[name]
        else:
            return ""

    def _addChecker(name):
        if name in named_children_checkers:
            if named_children_checkers[name] == "convertNoneConstantToNone":
                return "_auto_none"
            if named_children_checkers[name] == "convertEmptyStrConstantToNone":
                return "_auto_none_empty_str"
            if named_children_checkers[name] == "checkStatementsSequenceOrNone":
                return "_statements_or_none"
            if named_children_checkers[name] == "checkStatementsSequence":
                return "_statements"
            else:
                assert False, named_children_checkers[name]
        else:
            return ""

    mixin_name = "".join(
        makeTitleCased(named_child + _addType(named_child) + _addChecker(named_child))
        for named_child in named_children
    )

    mixin_name += "_".join(sorted(auto_compute_handling)).title().replace("_", "")

    mixin_name += "_".join(sorted(node_attributes)).title().replace("_", "")

    if len(named_children) == 0:
        mixin_name = "NoChildHaving" + mixin_name + "Mixin"
    elif len(named_children) == 1:
        mixin_name = "ChildHaving" + mixin_name + "Mixin"
    else:
        mixin_name = "ChildrenHaving" + mixin_name + "Mixin"

    if is_statement:
        mixin_name = "Statement" + mixin_name
    elif is_expression:
        pass
    else:
        mixin_name = "Module" + mixin_name

    return mixin_name


children_mixins = []

children_mixins_intentions = {}

children_mixing_setters_needed = {}


def addChildrenMixin(
    is_expression,
    is_statement,
    intended_for,
    named_children,
    named_children_types,
    named_children_checkers,
    auto_compute_handling=(),
    node_attributes=(),
):
    assert type(is_statement) is bool

    children_mixins.append(
        (
            is_expression,
            is_statement,
            named_children,
            named_children_types,
            named_children_checkers,
            auto_compute_handling,
            node_attributes,
        )
    )

    mixin_name = makeMixinName(
        is_expression,
        is_statement,
        named_children,
        named_children_types,
        named_children_checkers,
        auto_compute_handling,
        node_attributes,
    )

    if mixin_name not in children_mixins_intentions:
        children_mixins_intentions[mixin_name] = []
    if intended_for not in children_mixins_intentions[mixin_name]:
        children_mixins_intentions[mixin_name].append(intended_for)

    for named_child in named_children_types:
        assert named_child in named_children, named_child

    for named_child, named_child_checker in named_children_checkers.items():
        if named_child_checker == "convertNoneConstantToNone":
            assert named_children_types[named_child] == "optional"

    return mixin_name


def _parseNamedChildrenSpec(named_children):
    new_named_children = []

    setters_needed = set()
    named_children_types = {}
    named_children_checkers = {}

    for named_child_spec in named_children:
        if "|" in named_child_spec:
            named_child, named_child_properties = named_child_spec.split("|", 1)

            for named_child_property in named_child_properties.split("+"):
                if named_child_property == "setter":
                    setters_needed.add(named_child)
                elif named_child_property == "tuple":
                    named_children_types[named_child] = "tuple"
                elif named_child_property == "auto_none":
                    named_children_types[named_child] = "optional"
                    named_children_checkers[named_child] = "convertNoneConstantToNone"
                elif named_child_property == "auto_none_empty_str":
                    named_children_types[named_child] = "optional"
                    named_children_checkers[
                        named_child
                    ] = "convertEmptyStrConstantToNone"
                elif named_child_property == "statements_or_none":
                    named_children_types[named_child] = "optional"
                    named_children_checkers[
                        named_child
                    ] = "checkStatementsSequenceOrNone"
                elif named_child_property == "statements":
                    named_children_checkers[named_child] = "checkStatementsSequence"
                elif named_child_property == "optional":
                    named_children_types[named_child] = "optional"
                else:
                    assert False, named_child_property
        else:
            named_child = named_child_spec

        new_named_children.append(named_child)

    return (
        new_named_children,
        named_children_types,
        named_children_checkers,
        setters_needed,
    )


def _addFromNode(node_class):
    named_children = getattr(node_class, "named_children", ())
    # assert not hasattr(node_class, "named_child"), node_class

    if hasattr(node_class, "auto_compute_handling"):
        auto_compute_handling = frozenset(
            getattr(node_class, "auto_compute_handling").split(",")
        )
    else:
        auto_compute_handling = ()

    node_attributes = getattr(node_class, "node_attributes", ())

    if not named_children and not auto_compute_handling and not node_attributes:
        return

    (
        new_named_children,
        named_children_types,
        named_children_checkers,
        setters_needed,
    ) = _parseNamedChildrenSpec(named_children)

    mixin_name = makeMixinName(
        node_class.isExpression(),
        node_class.isStatement() or node_class.isStatementsSequence(),
        tuple(new_named_children),
        named_children_types,
        named_children_checkers,
        auto_compute_handling,
        node_attributes,
    )

    if mixin_name not in children_mixing_setters_needed:
        children_mixing_setters_needed[mixin_name] = set()
    children_mixing_setters_needed[mixin_name].update(setters_needed)

    for base in node_class.__mro__:
        if base.__name__ == mixin_name:
            break
    else:
        # if named_children == ("operand",):
        print("Not done", node_class.__name__, named_children, mixin_name)

    addChildrenMixin(
        node_class.isExpression(),
        node_class.isStatement() or node_class.isStatementsSequence(),
        node_class.__name__,
        tuple(new_named_children),
        named_children_types,
        named_children_checkers,
        auto_compute_handling,
        node_attributes,
    )


def addFromNodes():
    for node_class in NodeCheckMetaClass.kinds.values():
        # Find nodes with a make variant.
        if hasattr(sys.modules[node_class.__module__], "make" + node_class.__name__):
            node_factory_translations[node_class.__name__] = (
                "make" + node_class.__name__
            )

        _addFromNode(node_class)

    # Fake factories:
    node_factory_translations[
        "ExpressionImportlibMetadataMetadataCall"
    ] = "makeExpressionImportlibMetadataMetadataCall"
    node_factory_translations[
        "ExpressionImportlibMetadataBackportMetadataCall"
    ] = "makeExpressionImportlibMetadataBackportMetadataCall"


addFromNodes()


def makeChildrenHavingMixinNodes():
    # Complex stuff with many details due to 2 files and modes, pylint: disable=too-many-locals

    filename_python = "nuitka/nodes/ChildrenHavingMixins.py"
    filename_python2 = "nuitka/nodes/ExpressionBasesGenerated.py"
    filename_python3 = "nuitka/nodes/StatementBasesGenerated.py"

    template = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="ChildrenHavingMixin.py.j2",
    )

    mixins_done = set()

    with withFileOpenedAndAutoFormatted(
        filename_python
    ) as output_python, withFileOpenedAndAutoFormatted(
        filename_python2
    ) as output_python2, withFileOpenedAndAutoFormatted(
        filename_python3
    ) as output_python3:

        def emit1(*args):
            writeLine(output_python, *args)

        def emit2(*args):
            writeLine(output_python2, *args)

        def emit3(*args):
            writeLine(output_python3, *args)

        def emit(*args):
            emit1(*args)
            emit2(*args)
            emit3(*args)

        emitGenerationWarning(emit1, "Children having mixins", template.name)
        emitGenerationWarning(emit2, "Children having expression bases", template.name)
        emitGenerationWarning(emit3, "Children having statement bases", template.name)

        emit("# Loop unrolling over child names, pylint: disable=too-many-branches")

        emit1(
            """
from nuitka.nodes.Checkers import (
    checkStatementsSequenceOrNone,
    convertNoneConstantToNone,
    convertEmptyStrConstantToNone
)
"""
        )

        emit3(
            """
from nuitka.nodes.Checkers import (
    checkStatementsSequenceOrNone, \
    checkStatementsSequence,
    convertNoneConstantToNone
)
"""
        )

        for (
            is_expression,
            is_statement,
            named_children,
            named_children_types,
            named_children_checkers,
            auto_compute_handling,
            node_attributes,
        ) in sorted(
            children_mixins,
            key=lambda x: (x[0], x[1], x[2], x[3].items(), x[4].items()),
        ):
            mixin_name = makeMixinName(
                is_expression,
                is_statement,
                named_children,
                named_children_types,
                named_children_checkers,
                auto_compute_handling,
                node_attributes,
            )

            if mixin_name in mixins_done:
                continue

            intended_for = [
                value
                for value in children_mixins_intentions[mixin_name]
                if (
                    not value.endswith("Base")
                    or value.rstrip("Base")
                    not in children_mixins_intentions[mixin_name]
                )
            ]
            intended_for.sort()

            auto_compute_handling_set = set(auto_compute_handling)

            def pop(name):
                # only used inside of the loop, pylint: disable=cell-var-from-loop
                result = name in auto_compute_handling_set
                auto_compute_handling_set.discard(name)

                return result

            is_compute_final = pop("final")
            is_compute_no_raise = pop("no_raise")
            is_compute_statement = pop("operation")
            has_post_node_init = pop("post_init")

            assert not auto_compute_handling_set, auto_compute_handling_set

            code = template.render(
                name=template.name,
                is_expression=is_expression,
                is_statement=is_statement,
                mixin_name=mixin_name,
                named_children=named_children,
                named_children_types=named_children_types,
                named_children_checkers=named_children_checkers,
                children_mixing_setters_needed=sorted(
                    tuple(children_mixing_setters_needed.get(mixin_name, ()))
                ),
                intended_for=intended_for,
                is_compute_final=is_compute_final,
                is_compute_no_raise=is_compute_no_raise,
                is_compute_statement=is_compute_statement,
                has_post_node_init=has_post_node_init,
                node_attributes=node_attributes,
                len=len,
            )

            if is_statement:
                emit3(code)
            elif auto_compute_handling or node_attributes:
                emit2(code)
            else:
                emit1(code)

            mixins_done.add(mixin_name)


SpecVersion = namedtuple(
    "SpecVersion", ("spec_name", "python_criterion", "spec", "suffix")
)


def getSpecVersions(spec_module):
    result = {}

    for spec_name, spec in getSpecs(spec_module):
        for (version, str_version) in (
            (0x370, "37"),
            (0x380, "38"),
            (0x390, "39"),
            (0x3A0, "310"),
        ):
            if "since_%s" % str_version in spec_name:
                python_criterion = ">= 0x%x" % version
                suffix = "Since%s" % str_version
                break

            if "before_%s" % str_version in spec_name:
                python_criterion = "< 0x%x" % version
                suffix = "Before%s" % str_version
                break
        else:
            python_criterion = None
            suffix = ""

        assert ".entry_points" not in spec_name or python_criterion is not None

        if spec.name not in result:
            result[spec.name] = []

        result[spec.name].append(SpecVersion(spec_name, python_criterion, spec, suffix))
        result[spec.name].sort(
            key=lambda spec_version: spec_version.python_criterion or "", reverse=True
        )

    return tuple(sorted(result.values()))


def makeHardImportNodes():
    # Too many details, pylint: disable=too-many-locals

    filename_python = "nuitka/nodes/HardImportNodesGenerated.py"

    template_ref_node = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="HardImportReferenceNode.py.j2",
    )

    template_call_node = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="HardImportCallNode.py.j2",
    )

    with withFileOpenedAndAutoFormatted(filename_python) as output_python:

        def emit(*args):
            writeLine(output_python, *args)

        emitGenerationWarning(emit, "Hard import nodes", template_ref_node.name)

        emit(
            """
hard_import_node_classes = {}

"""
        )

        for spec_descriptions in getSpecVersions(nuitka.specs.HardImportSpecs):
            spec = spec_descriptions[0][2]

            named_children_checkers = {}

            module_name, function_name = spec.name.rsplit(".", 1)
            module_name_title = makeTitleCased(adaptModuleName(module_name))
            function_name_title = makeTitleCased(function_name)

            node_class_name = "Expression%s%s" % (
                module_name_title,
                function_name_title,
            )

            code = template_ref_node.render(
                name=template_ref_node.name,
                parameter_names_count=len(spec.getParameterNames()),
                function_name=function_name,
                function_name_title=function_name_title,
                function_name_code=makeCodeCased(function_name),
                module_name=module_name,
                module_name_code=makeCodeCased(adaptModuleName(module_name)),
                module_name_title=module_name_title,
                call_node_module_name=getCallModuleName(module_name, function_name),
                translateNodeClassName=translateNodeClassName,
                is_stdlib=module_name not in hard_modules_non_stdlib,
                specs=spec_descriptions,
            )

            emit(code)

            for spec_desc in spec_descriptions:
                spec = spec_desc.spec
                parameter_names = spec.getParameterNames()

                named_children_types = {}
                if spec.name == "pkg_resources.require":
                    named_children_types["requirements"] = "tuple"

                if spec.getDefaultCount():
                    for optional_name in spec.getArgumentNames()[
                        -spec.getDefaultCount() :
                    ]:
                        assert optional_name not in named_children_types
                        named_children_types[optional_name] = "optional"

                if spec.getStarDictArgumentName():
                    named_children_types[spec.getStarDictArgumentName()] = "tuple"

                if parameter_names:
                    mixin_name = addChildrenMixin(
                        True,
                        False,
                        node_class_name,
                        parameter_names,
                        named_children_types,
                        named_children_checkers,
                    )
                else:
                    mixin_name = None

                extra_mixins = []

                result_shape = spec.getTypeShape()
                if result_shape is not None:
                    extra_mixins.append(_getMixinForShape(result_shape))

                code = template_call_node.render(
                    name=template_call_node.name,
                    mixin_name=mixin_name,
                    suffix=spec_desc.suffix,
                    python_criterion=spec_desc.python_criterion,
                    extra_mixins=extra_mixins,
                    parameter_names_count=len(spec.getParameterNames()),
                    named_children=parameter_names,
                    named_children_types=named_children_types,
                    argument_names=spec.getArgumentNames(),
                    star_list_argument_name=spec.getStarListArgumentName(),
                    star_dict_argument_name=spec.getStarDictArgumentName(),
                    function_name=function_name,
                    function_name_title=function_name_title,
                    function_name_code=makeCodeCased(function_name),
                    module_name=module_name,
                    module_name_code=makeCodeCased(adaptModuleName(module_name)),
                    module_name_title=module_name_title,
                    call_node_module_name=getCallModuleName(module_name, function_name),
                    spec_name=spec_desc.spec_name,
                )

                emit(code)


def main():
    makeHardImportNodes()
    makeAttributeNodes()
    makeBuiltinOperationNodes()
    makeChildrenHavingMixinNodes()
