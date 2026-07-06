#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""This tool is generating node variants from Jinja templates."""

import ast
import hashlib
import os
import sys

from nuitka.States import states

states.is_full_compat = False

# isort:start

import textwrap
from collections import namedtuple

import nuitka.code_generation.BinaryOperationHelperDefinitions
import nuitka.code_generation.CodeGeneration
import nuitka.code_generation.ComparisonCodes
import nuitka.code_generation.Namify
import nuitka.nodes.NetworkxNodes
import nuitka.nodes.PackageMetadataNodes
import nuitka.nodes.PackageResourceNodes
import nuitka.nodes.SideEffectNodes
import nuitka.nodes.TensorflowNodes
import nuitka.specs.BuiltinBytesOperationSpecs
import nuitka.specs.BuiltinDictOperationSpecs
import nuitka.specs.BuiltinListOperationSpecs
import nuitka.specs.BuiltinStrOperationSpecs
import nuitka.specs.BuiltinTypeOperationSpecs
import nuitka.specs.HardImportSpecs
import nuitka.tree.Building
from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import OrderedSet
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
from nuitka.utils.FileOperations import getFileContents, getNormalizedPath
from nuitka.utils.Jinja2 import getTemplate

from .Common import (
    formatArgs,
    getLicenseGeneratedCode,
    getMethodVariations,
    getSpecs,
    parseOptions,
    python2_dict_methods,
    python2_list_methods,
    python2_str_methods,
    python2_type_methods,
    python3_bytes_methods,
    python3_dict_methods,
    python3_list_methods,
    python3_str_methods,
    python3_type_methods,
    withFileOpenedAndAutoFormattedWithClaim,
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

# Some methods are static, but we still do them
attribute_shape_static = {}

# Translations for node names.
node_factory_translations = {}


def _getAstStringValue(node):
    if (
        hasattr(ast, "Constant")
        and type(node) is ast.Constant
        and type(node.value) is str
    ):
        return node.value

    if hasattr(ast, "Str") and type(node) is ast.Str:
        return node.s

    return None


def _parseFormatSpec(template_value, percent_pos):
    result = None

    if percent_pos + 1 < len(template_value) and template_value[percent_pos + 1] == "(":
        end_pos = template_value.find(")", percent_pos + 2)

        if end_pos != -1:
            variable_name = template_value[percent_pos + 2 : end_pos]
            format_pos = end_pos + 1

            while format_pos < len(template_value) and template_value[format_pos] in (
                "#",
                "0",
                " ",
                "+",
                "-",
            ):
                format_pos += 1

            while (
                format_pos < len(template_value)
                and template_value[format_pos].isdigit()
            ):
                format_pos += 1

            if format_pos < len(template_value) and template_value[format_pos] == ".":
                format_pos += 1

            while (
                format_pos < len(template_value)
                and template_value[format_pos].isdigit()
            ):
                format_pos += 1

            if format_pos < len(template_value):
                conversion = template_value[format_pos]

                if conversion in ("s", "d") and format_pos == end_pos + 1:
                    result = variable_name, conversion, format_pos + 1

    return result


def _addTemplateLiteral(result, template_value, start_pos, end_pos):
    if start_pos < end_pos:
        result.append(("literal", template_value[start_pos:end_pos]))


def _parsePercentTemplate(template_value):
    if "{%" in template_value or "{{" in template_value:
        return None

    result = []
    variables = []
    pos = 0

    while True:
        percent_pos = template_value.find("%", pos)

        if percent_pos == -1:
            _addTemplateLiteral(result, template_value, pos, len(template_value))

            return result, tuple(variables)

        if percent_pos + 1 >= len(template_value):
            return None

        if template_value[percent_pos + 1] == "%":
            _addTemplateLiteral(result, template_value, pos, percent_pos)
            result.append(("literal", "%"))

            pos = percent_pos + 2
            continue

        format_spec = _parseFormatSpec(template_value, percent_pos)
        if format_spec is None:
            return None

        variable_name, conversion, next_pos = format_spec

        _addTemplateLiteral(result, template_value, pos, percent_pos)
        result.append((conversion, variable_name))
        variables.append((variable_name, conversion))

        pos = next_pos


def _getCodeTemplateValues():
    template_dir = getNormalizedPath("nuitka/code_generation/templates")

    for filename in sorted(os.listdir(template_dir)):
        if not filename.startswith("CodeTemplates") or not filename.endswith(".py"):
            continue

        if filename == "CodeTemplatesGenerated.py":
            continue

        module_name = (
            "nuitka.code_generation.templates.%s" % os.path.splitext(filename)[0]
        )
        full_path = os.path.join(template_dir, filename)

        tree = ast.parse(getFileContents(full_path, encoding="utf8"))

        for node in ast.walk(tree):
            if type(node) is not ast.Assign:
                continue

            template_value = _getAstStringValue(node.value)

            if template_value is None:
                continue

            for target in node.targets:
                if type(target) is not ast.Name:
                    continue

                if not target.id.startswith("template_"):
                    continue

                parse_result = _parsePercentTemplate(template_value)

                if parse_result is None:
                    continue

                yield module_name, target.id, template_value, parse_result


def _getTemplateHash(template_value):
    return hashlib.sha256(template_value.encode("utf8")).hexdigest()


def _getTemplateEmitFunctionName(template_name, count):
    return "_emit_%03d_%s" % (count, template_name)


class _TemplateCompactor(object):
    """Compact a template's literal parts for non-readable code generation.

    Comment and whitespace stripping must track lexer state across the whole
    template, not per fragment: a C comment or string literal can span a
    substituted value, and a literal fragment can begin in the middle of a
    line, right after a substituted value.

    Handling each fragment independently previously (1) stripped a "/*" opener
    while keeping its "*/" closer when a block comment spanned a value, and
    (2) stripped inline leading whitespace after a value, joining tokens like
    "%(file_scope)s PyObject" -> "<value>PyObject". Both produced invalid C in
    compact (non-readable) builds.
    """

    def __init__(self):
        self.in_string = None
        self.escaped = False
        self.in_block_comment = False
        self.in_line_comment = False
        self.at_line_start = True

    @property
    def _in_comment(self):
        return self.in_block_comment or self.in_line_comment

    def _compactLiteral(self, value):
        # Character-level lexer state machine, pylint: disable=too-many-branches
        result = []
        pos = 0
        length = len(value)

        while pos < length:
            char = value[pos]
            next_char = value[pos + 1] if pos + 1 < length else ""

            if self.in_block_comment:
                if char == "*" and next_char == "/":
                    self.in_block_comment = False
                    pos += 2
                    continue

                # Preserve newlines so line structure and line-start tracking
                # stay intact even after a comment is removed.
                if char in "\r\n":
                    result.append(char)
                    self.at_line_start = True

                pos += 1
            elif self.in_line_comment:
                if char in "\r\n":
                    self.in_line_comment = False
                    result.append(char)
                    self.at_line_start = True

                pos += 1
            elif self.in_string is not None:
                result.append(char)

                if self.escaped:
                    self.escaped = False
                elif char == "\\":
                    self.escaped = True
                elif char == self.in_string:
                    self.in_string = None

                self.at_line_start = char in "\r\n"
                pos += 1
            elif char in ("'", '"'):
                self.in_string = char
                result.append(char)
                self.at_line_start = False
                pos += 1
            elif char == "/" and next_char == "/":
                self.in_line_comment = True
                pos += 2
            elif char == "/" and next_char == "*":
                self.in_block_comment = True
                pos += 2
            elif self.at_line_start and char in (" ", "\t"):
                pos += 1
            else:
                result.append(char)
                self.at_line_start = char in "\r\n"
                pos += 1

        return "".join(result)

    def compact(self, parts):
        result = []

        for kind, value in parts:
            if kind == "literal":
                value = self._compactLiteral(value)

                if value:
                    result.append((kind, value))
            elif not self._in_comment:
                # A substituted value is opaque inline content (a code
                # identifier, type, number, ...). Keep it only when it is not
                # inside a comment; it never toggles string or comment state,
                # and it means the next literal is no longer at a line start.
                result.append((kind, value))
                self.at_line_start = False

        return tuple(result)


def _compactTemplateParts(parts):
    return _TemplateCompactor().compact(parts)


def _writePreparedTemplateEmitter(emit, function_name, parts):
    emit("def %s(emit, values):" % function_name)

    if parts:
        for kind, value in parts:
            if kind == "literal":
                emit("    emit(%r)" % value)
            elif kind == "s":
                emit("    emit(values[%r])" % value)
            elif kind == "d":
                emit("    emit(str(values[%r]))" % value)
            else:
                assert False, kind
    else:
        emit("    pass")

    emit()


def _writePreparedTemplateInfoTables(emit, template_infos):
    emit("template_infos = {")

    for (
        template_key,
        function_name,
        readable_function_name,
        template_hash,
        variables,
        _variables,
    ) in sorted(template_infos):
        emit(
            "    %r: (%r, %r, %s, %s),"
            % (
                template_key,
                template_hash,
                variables,
                function_name,
                readable_function_name,
            )
        )

    emit("}")
    emit()
    emit("template_variables = {")

    for (
        template_key,
        _function_name,
        _readable_function_name,
        _template_hash,
        _variables,
        variables,
    ) in sorted(template_infos):
        emit("    %r: %r," % (template_key, variables))

    emit("}")


def _makeTemplateInfo(template_desc, count):
    module_name, template_name, template_value, parse_result = template_desc
    parts, variables = parse_result

    function_name = _getTemplateEmitFunctionName(template_name, count)
    readable_function_name = function_name + "_readable"
    template_key = "%s.%s" % (module_name, template_name)

    return (
        template_key,
        function_name,
        readable_function_name,
        _getTemplateHash(template_value),
        tuple(sorted(set(variable_name for variable_name, _ in variables))),
        variables,
        _compactTemplateParts(parts),
        parts,
    )


def makeCodeTemplatesGenerated():
    filename_python = getNormalizedPath(
        "nuitka/code_generation/templates/CodeTemplatesGenerated.py"
    )

    with withFileOpenedAndAutoFormattedWithClaim(
        filename_python,
        ignore_errors=False,
        claim=getLicenseGeneratedCode(),
    ) as output_python:

        def emit(*args):
            writeLine(output_python, *args)

        emitGenerationWarning(
            emit, "Prepared code generation templates", "CodeTemplates*.py"
        )
        emit("# pylint: disable=unused-argument")
        emit()

        template_infos = []

        for count, template_desc in enumerate(_getCodeTemplateValues()):
            template_info = _makeTemplateInfo(template_desc, count)

            (
                template_key,
                function_name,
                readable_function_name,
                template_hash,
                variables,
                variable_descriptions,
                compact_parts,
                parts,
            ) = template_info

            _writePreparedTemplateEmitter(emit, function_name, compact_parts)
            _writePreparedTemplateEmitter(emit, readable_function_name, parts)

            template_infos.append(
                (
                    template_key,
                    function_name,
                    readable_function_name,
                    template_hash,
                    variables,
                    variable_descriptions,
                )
            )

        _writePreparedTemplateInfoTables(emit, template_infos)


def _getMixinForShape(shape):
    mixin_names = {
        tshape_bool: "nuitka.nodes.ExpressionShapeMixins.ExpressionBoolShapeExactMixin",
        tshape_bytes: "nuitka.nodes.ExpressionShapeMixins.ExpressionBytesShapeExactMixin",
        tshape_dict: "nuitka.nodes.ExpressionShapeMixins.ExpressionDictShapeExactMixin",
        tshape_int: "nuitka.nodes.ExpressionShapeMixins.ExpressionIntShapeExactMixin",
        tshape_list: "nuitka.nodes.ExpressionShapeMixins.ExpressionListShapeExactMixin",
        tshape_none: "nuitka.nodes.ExpressionShapeMixins.ExpressionNoneShapeExactMixin",
        tshape_str: "nuitka.nodes.ExpressionShapeMixins.ExpressionStrShapeExactMixin",
        tshape_tuple: "nuitka.nodes.ExpressionShapeMixins.ExpressionTupleShapeExactMixin",
    }

    assert shape in mixin_names, shape

    return mixin_names[shape]


def processTypeShapeAttribute(
    shape_name, spec_module, python2_methods, python3_methods, staticmethod_names=()
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
            attribute_shape_static[key] = method_name in staticmethod_names

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
            attribute_shape_static[key] = method_name in staticmethod_names

            if len(arg_counts) > 1:
                attribute_shape_variations[key] = arg_counts

            attribute_shape_node_arg_mapping[key] = arg_name_mapping


processTypeShapeAttribute(
    "tshape_dict",
    nuitka.specs.BuiltinDictOperationSpecs,
    python2_dict_methods,
    python3_dict_methods,
    ("fromkeys",),
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

processTypeShapeAttribute(
    "tshape_type",
    nuitka.specs.BuiltinTypeOperationSpecs,
    python2_type_methods,
    python3_type_methods,
)


attribute_shape_empty = {}

attribute_shape_empty["update", "tshape_dict"] = """\
lambda source_ref: wrapExpressionWithNodeSideEffects(
    new_node=makeConstantRefNode(
        constant=None,
        source_ref=source_ref
    ),
    old_node=dict_arg
)
"""

attribute_shape_empty["fromkeys", "tshape_dict"] = """
lambda source_ref: makeRaiseExceptionReplacementExpression(
    expression=dict_arg,
    exception_type="TypeError",
    exception_value=getDictFromkeysNoArgErrorMessage(),
)
"""


def emitGenerationWarning(emit, doc_string, template_name):
    generate_names = set()

    generate_names.update(attribute_information.keys())
    generate_names.update(
        attribute_name.replace("_", "") for attribute_name in attribute_information
    )

    generate_names.update(sum(attribute_shape_args.values(), ()))

    for spec_descriptions in getSpecVersions(nuitka.specs.HardImportSpecs):
        spec = spec_descriptions[0][2]
        generate_names.update(spec.getArgumentNames())

    ignores = textwrap.fill(
        " ".join(sorted(generate_names)),
        width=90,
        initial_indent="spell-checker: ignore ",
        subsequent_indent="spell-checker: ignore ",
        break_on_hyphens=False,
        break_long_words=False,
        expand_tabs=False,
        replace_whitespace=False,
    )

    emit("""
# We are not avoiding these in generated code at all
# pylint: disable=I0021,line-too-long,too-many-instance-attributes,too-many-lines
# pylint: disable=I0021,too-many-arguments,too-many-return-statements,too-many-statements
""")

    emit('''
"""%s

WARNING, this code is GENERATED. Modify the template %s instead!

%s
"""

''' % (doc_string, template_name, ignores))


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
    filename_python = getNormalizedPath("nuitka/nodes/AttributeNodesGenerated.py")

    template = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="AttributeNodeFixed.py.j2",
    )

    with withFileOpenedAndAutoFormattedWithClaim(
        filename_python,
        ignore_errors=True,
        claim=getLicenseGeneratedCode(),
    ) as output_python:

        def emit(*args):
            writeLine(output_python, *args)

        emitGenerationWarning(emit, "Specialized attribute nodes", template.name)

        emit("from .AttributeLookupNodes import ExpressionAttributeLookupFixedBase")
        emit("from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs")

        emit("from nuitka.nodes.ConstantRefNodes import makeConstantRefNode")
        emit("""\
from nuitka.nodes.NodeMakingHelpers import (
    wrapExpressionWithNodeSideEffects,
    makeRaiseExceptionReplacementExpression
)
            """)

        emit(
            "from nuitka.nodes.KeyValuePairNodes import makeKeyValuePairExpressionsFromKwArgs"
        )

        emit("from nuitka.nodes.AttributeNodes import makeExpressionAttributeLookup")

        emit("from nuitka.PythonVersions import getDictFromkeysNoArgErrorMessage")

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
                attribute_shape_static=attribute_shape_static,
                formatArgs=formatArgs,
                formatCallArgs=formatCallArgs,
                translateNodeClassName=translateNodeClassName,
                reversed=reversed,
                str=str,
                name=template.name,
            )

            emit(code)


def makeBuiltinOperationNodes():
    filename_python = getNormalizedPath(
        "nuitka/nodes/BuiltinOperationNodeBasesGenerated.py"
    )

    template = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="BuiltinOperationNodeBases.py.j2",
    )

    with withFileOpenedAndAutoFormattedWithClaim(
        filename_python,
        ignore_errors=True,
        claim=getLicenseGeneratedCode(),
    ) as output_python:

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
                attribute_shape_static=attribute_shape_static,
                attribute_shape_operations_mixin_classes=attribute_shape_operations_mixin_classes,
                formatArgs=formatArgs,
                formatCallArgs=formatCallArgs,
                addChildrenMixin=addChildrenMixin,
                reversed=reversed,
                str=str,
                repr=repr,
                name=template.name,
            )

            emit(code)


def adaptModuleName(value):
    if value == "importlib_metadata":
        return "importlib_metadata_backport"

    if value == "importlib_resources":
        return "importlib_resources_backport"

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

    module_names = {
        "builtins": {"open": "BuiltinOpenNodes"},
        "ctypes": "CtypesNodes",
        "importlib.resources": "PackageResourceNodes",
        "importlib_resources": "PackageResourceNodes",
        "os": "OsSysNodes",
        "os.path": "OsSysNodes",
        "pkgutil": "PackageResourceNodes",
        "sys": "OsSysNodes",
        "tensorflow": "TensorflowNodes",
    }

    if module_name.startswith("networkx"):
        result = "NetworkxNodes"
    else:
        result = module_names.get(module_name)

        if type(result) is dict:
            result = result.get(function_name)

    assert result is not None, (module_name, function_name)

    return result


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

    mixin_name += (
        "_".join(sorted(auto_compute_handling))
        .title()
        .replace("_", "")
        .replace(":", "")
    )

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
                    named_children_checkers[named_child] = (
                        "convertEmptyStrConstantToNone"
                    )
                elif named_child_property == "statements_or_none":
                    named_children_types[named_child] = "optional"
                    named_children_checkers[named_child] = (
                        "checkStatementsSequenceOrNone"
                    )
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
        # TODO: Subject to dying, we now make this up on the fly.
        node_class.kind.startswith("EXPRESSION"),
        node_class.kind.startswith("STATEMENT"),
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
        if base.__name__ in (mixin_name, "_" + mixin_name):
            break
    else:
        # if named_children == ("operand",):
        print("Not done", node_class.__name__, named_children, mixin_name)

    addChildrenMixin(
        # TODO: Subject to dying, we now make this up on the fly.
        node_class.kind.startswith("EXPRESSION"),
        node_class.kind.startswith("STATEMENT"),
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
    node_factory_translations["ExpressionImportlibMetadataMetadataCall"] = (
        "makeExpressionImportlibMetadataMetadataCall"
    )
    node_factory_translations["ExpressionImportlibMetadataBackportMetadataCall"] = (
        "makeExpressionImportlibMetadataBackportMetadataCall"
    )
    node_factory_translations["ExpressionBuiltinsOpenCall"] = (
        "makeExpressionBuiltinsOpenCall"
    )
    node_factory_translations["ExpressionSysExitCall"] = "makeExpressionSysExitCall"


addFromNodes()


def makeChildrenHavingMixinNodes():  # pylint: disable=too-many-locals,too-many-statements
    # Complex stuff with many details due to 2 files and modes,

    filename_python = getNormalizedPath("nuitka/nodes/ChildrenHavingMixins.py")
    filename_python2 = getNormalizedPath("nuitka/nodes/ExpressionBasesGenerated.py")
    filename_python3 = getNormalizedPath("nuitka/nodes/StatementBasesGenerated.py")

    template = getTemplate(
        package_name=__package__,
        template_subdir="templates_python",
        template_name="ChildrenHavingMixin.py.j2",
    )

    mixins_done = set()

    with withFileOpenedAndAutoFormattedWithClaim(
        filename_python,
        ignore_errors=False,
        claim=getLicenseGeneratedCode(),
    ) as output_python, withFileOpenedAndAutoFormattedWithClaim(
        filename_python2,
        ignore_errors=False,
        claim=getLicenseGeneratedCode(),
    ) as output_python2, withFileOpenedAndAutoFormattedWithClaim(
        filename_python3,
        ignore_errors=False,
        claim=getLicenseGeneratedCode(),
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

        emit1("""
from .Checkers import (
    checkStatementsSequenceOrNone,
    convertNoneConstantToNone,
    convertEmptyStrConstantToNone
)
""")

        emit3("""
from .Checkers import (
    checkStatementsSequenceOrNone, \
    checkStatementsSequence,
    convertNoneConstantToNone
)
""")

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

            is_compute_final_children = pop("final_children")

            is_compute_no_raise = pop("no_raise")
            is_compute_raise = pop("raise")
            is_compute_raise_operation = pop("raise_operation")
            assert (
                is_compute_no_raise + is_compute_raise + is_compute_raise_operation < 2
            )

            if is_compute_raise:
                raise_mode = "raise"
            elif is_compute_no_raise:
                raise_mode = "no_raise"
            elif is_compute_raise_operation:
                raise_mode = "raise_operation"
            else:
                raise_mode = None

            is_compute_statement = pop("operation")
            has_post_node_init = pop("post_init")

            awaited_constant_attributes = OrderedSet(
                value.split(":", 1)[1]
                for value in auto_compute_handling_set
                if value.startswith("wait_constant:")
            )

            auto_compute_handling_set -= {
                "wait_constant:%s" % value for value in awaited_constant_attributes
            }

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
                is_compute_final_children=is_compute_final_children,
                raise_mode=raise_mode,
                is_compute_statement=is_compute_statement,
                awaited_constant_attributes=awaited_constant_attributes,
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
        for version, str_version in (
            (0x370, "37"),
            (0x380, "38"),
            (0x390, "39"),
            (0x3A0, "310"),
            (0x3B0, "311"),
            (0x3C0, "312"),
            (0x3D0, "313"),
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


def makeHardImportNodes():  # pylint: disable=too-many-locals
    filename_python = getNormalizedPath("nuitka/nodes/HardImportNodesGenerated.py")

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

    with withFileOpenedAndAutoFormattedWithClaim(
        filename_python,
        ignore_errors=True,
        claim=getLicenseGeneratedCode(),
    ) as output_python:

        def emit(*args):
            writeLine(output_python, *args)

        emitGenerationWarning(emit, "Hard import nodes", template_ref_node.name)

        emit("""
hard_import_node_classes = {}

""")

        for spec_descriptions in getSpecVersions(nuitka.specs.HardImportSpecs):
            spec = spec_descriptions[0][2]

            named_children_checkers = OrderedDict()

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
                parameter_names = spec.getParameterNames2()

                named_children_types = {}
                if spec.name == "pkg_resources.require":
                    named_children_types["requirements"] = "tuple"

                if spec.getDefaultCount():
                    for optional_name in spec.getArgumentNames()[
                        -spec.getDefaultCount() :
                    ]:
                        assert optional_name not in named_children_types
                        named_children_types[optional_name] = "optional"

                if spec.getStarListArgumentName():
                    named_children_types[spec.getStarListArgumentName()] = "tuple"

                if spec.getStarDictArgumentName():
                    named_children_types[spec.getStarDictArgumentName()] = "tuple"

                for kw_only_name in spec.getKwOnlyParameterNames():
                    assert kw_only_name not in named_children_types
                    named_children_types[kw_only_name] = "optional"

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
                    is_stdlib_module=module_name
                    in (
                        "builtins",
                        "os",
                        "os.path",
                        "pkgutil",
                        "ctypes",
                        "importlib.metadata",
                        "importlib.resources",
                    ),
                    module_name_code=makeCodeCased(adaptModuleName(module_name)),
                    module_name_title=module_name_title,
                    call_node_module_name=getCallModuleName(module_name, function_name),
                    spec_name=spec_desc.spec_name,
                )

                emit(code)


def main():
    parseOptions()

    makeCodeTemplatesGenerated()
    makeHardImportNodes()
    makeAttributeNodes()
    makeBuiltinOperationNodes()
    makeChildrenHavingMixinNodes()


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
