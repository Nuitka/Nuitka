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
""" This tool is generating code variants for helper codes from Jinja templates.

"""

import nuitka.Options

nuitka.Options.is_full_compat = False

# isort:start

import os

import nuitka.specs.BuiltinBytesOperationSpecs
import nuitka.specs.BuiltinDictOperationSpecs
import nuitka.specs.BuiltinStrOperationSpecs
import nuitka.specs.BuiltinUnicodeOperationSpecs
from nuitka.code_generation.BinaryOperationHelperDefinitions import (
    getSpecializedBinaryOperations,
    parseTypesFromHelper,
)
from nuitka.code_generation.CallCodes import (
    getQuickCallCode,
    getQuickMethodCallCode,
    getQuickMethodDescriptorCallCode,
    getQuickMixedCallCode,
    getTemplateCodeDeclaredFunction,
    max_quick_call,
)
from nuitka.code_generation.ComparisonHelperDefinitions import (
    getSpecializedComparisonOperations,
)
from nuitka.code_generation.ImportCodes import getImportModuleHardCodeName
from nuitka.nodes.ImportNodes import (
    hard_modules,
    hard_modules_non_stdlib,
    hard_modules_version,
)
from nuitka.utils.Jinja2 import getTemplateC

from .Common import (
    formatArgs,
    getMethodVariations,
    python2_dict_methods,
    python2_str_methods,
    python2_unicode_methods,
    python3_bytes_methods,
    python3_dict_methods,
    python3_str_methods,
    withFileOpenedAndAutoFormatted,
    writeLine,
)
from .CTypeDescriptions import (
    bytes_desc,
    c_bool_desc,
    c_digit_desc,
    c_float_desc,
    c_long_desc,
    dict_desc,
    float_desc,
    int_desc,
    list_desc,
    long_desc,
    n_bool_desc,
    object_desc,
    set_desc,
    str_desc,
    tuple_desc,
    unicode_desc,
)


def getDoExtensionUsingTemplateC(template_name):
    return getTemplateC(
        package_name="nuitka.code_generation",
        template_subdir="templates_c",
        template_name=template_name,
        extensions=("jinja2.ext.do",),
    )


class AlternativeTypeBase(object):
    # TODO: Base class for alternative types
    pass


class AlternativeIntOrClong(AlternativeTypeBase):
    # TODO: Base class for alternative type int or clong.
    pass


types = (
    int_desc,
    str_desc,
    unicode_desc,
    float_desc,
    tuple_desc,
    list_desc,
    set_desc,
    dict_desc,
    bytes_desc,
    long_desc,
    c_long_desc,
    c_digit_desc,
    c_float_desc,
    c_bool_desc,
    n_bool_desc,
    object_desc,
)


def findTypeFromCodeName(code_name):
    for candidate in types:
        if candidate.getHelperCodeName() == code_name:
            return candidate


op_slot_codes = set()

# Reverse operation mapping.
reversed_args_compare_op_codes = {
    "LE": "GE",
    "LT": "GT",
    "EQ": "EQ",
    "NE": "NE",
    "GT": "LT",
    "GE": "LE",
}


def makeCompareSlotCode(operator, op_code, target, left, right, emit):
    # Many variations to consider, pylint: disable=too-many-branches

    key = operator, op_code, target, left, right
    if key in op_slot_codes:
        return

    int_types_family = (int_desc, c_long_desc)
    long_types_family = (int_desc, long_desc, c_long_desc, c_digit_desc)
    float_types_family = (int_desc, long_desc, float_desc, c_long_desc, c_float_desc)

    if left in int_types_family and right in int_types_family:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonInt.c.j2")
    elif left in long_types_family and right in long_types_family:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonLong.c.j2")
    elif left in float_types_family and right in float_types_family:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonFloat.c.j2")
    elif left == int_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonInt.c.j2")
    elif left == long_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonLong.c.j2")
    elif left == float_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonFloat.c.j2")
    elif left == tuple_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonTuple.c.j2")
    elif left == list_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonList.c.j2")
    # elif left == set_desc:
    #     template = env.get_template("HelperOperationComparisonSet.c.j2")
    elif left == bytes_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonBytes.c.j2")
    elif left == str_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonStr.c.j2")
    elif left == unicode_desc:
        template = getDoExtensionUsingTemplateC("HelperOperationComparisonUnicode.c.j2")
    else:
        return

    assert left is not int_desc or right is not int_desc or target is not n_bool_desc

    code = template.render(
        operand=operator,  # TODO: rename
        target=target,
        left=left,
        right=right,
        op_code=op_code,
        reversed_args_op_code=reversed_args_compare_op_codes[op_code],
        name=template.name,
        long_desc=long_desc,
        c_long_desc=c_long_desc,
        c_digit_desc=c_digit_desc,
    )

    emit(code)

    op_slot_codes.add(key)


mul_repeats = set()


def makeMulRepeatCode(target, left, right, emit):
    key = right, left
    if key in mul_repeats:
        return

    template = getDoExtensionUsingTemplateC("HelperOperationMulRepeatSlot.c.j2")

    code = template.render(target=target, left=left, right=right)

    emit(code)

    mul_repeats.add(key)


def _getNbSlotFromOperand(operand, op_code):
    # pylint: disable=too-many-branches,too-many-return-statements

    if operand == "+":
        return "nb_add"
    elif operand == "*":
        return "nb_multiply"
    elif operand == "-":
        return "nb_subtract"
    elif operand == "//":
        return "nb_floor_divide"
    elif operand == "/":
        if op_code == "TRUEDIV":
            return "nb_true_divide"
        else:
            return "nb_divide"
    elif operand == "%":
        return "nb_remainder"
    elif operand == "**":
        return "nb_power"
    elif operand == "<<":
        return "nb_lshift"
    elif operand == ">>":
        return "nb_rshift"
    elif operand == "|":
        return "nb_or"
    elif operand == "&":
        return "nb_and"
    elif operand == "^":
        return "nb_xor"
    elif operand == "@":
        return "nb_matrix_multiply"
    elif operand == "divmod":
        return "nb_divmod"
    else:
        assert False, operand


def _getNbInplaceSlotFromOperand(operand, op_code):
    if operand == "divmod":
        return None

    nb_slot = _getNbSlotFromOperand(operand, op_code)
    return nb_slot.replace("nb_", "nb_inplace_")


def _parseTypesFromHelper(helper_name):
    (
        target_code,
        left_code,
        right_code,
    ) = parseTypesFromHelper(helper_name)

    if target_code is not None:
        target = findTypeFromCodeName(target_code)
    else:
        target = None

    left = findTypeFromCodeName(left_code)
    right = findTypeFromCodeName(right_code)

    return target_code, target, left, right


def _parseRequirements(op_code, target, left, right, emit):
    python_requirement = set()

    # There is an obsolete Python2 operation too, making sure it's guarded in code.
    if op_code == "OLDDIV":
        python_requirement.add(int_desc.python_requirement)
    if op_code == "MATMULT":
        python_requirement.add("PYTHON_VERSION >= 0x350")
    if target is not None and target.python_requirement:
        python_requirement.add(target.python_requirement)
    if left.python_requirement:
        python_requirement.add(left.python_requirement)
    if right.python_requirement:
        python_requirement.add(right.python_requirement)

    if python_requirement:
        assert len(python_requirement) == 1, (target, left, right)
        python_requirement = python_requirement.pop()

        emit("#if %s" % python_requirement)

    return python_requirement


def makeHelperOperations(
    template, inplace, helpers_set, operator, op_code, emit_h, emit_c, emit
):
    # Complexity comes natural, pylint: disable=too-many-locals

    emit(
        '/* C helpers for type %s "%s" (%s) operations */'
        % ("in-place" if inplace else "specialized", operator, op_code)
    )
    emit()

    for helper_name in helpers_set:
        target_code, target, left, right = _parseTypesFromHelper(helper_name)

        assert target is None or not inplace, helper_name

        if target is None and not inplace:
            assert False, target_code

        python_requirement = _parseRequirements(op_code, target, left, right, emit)

        emit(
            '/* Code referring to "%s" corresponds to %s and "%s" to %s. */'
            % (
                left.getHelperCodeName(),
                left.type_desc,
                right.getHelperCodeName(),
                right.type_desc,
            )
        )

        if operator == "+":
            sq_slot = "sq_concat"
        elif operator == "*":
            sq_slot = "sq_repeat"
        else:
            sq_slot = None

        if inplace and sq_slot is not None:
            sq_inplace_slot = sq_slot.replace("sq_", "sq_inplace_")
        else:
            sq_inplace_slot = None

        code = template.render(
            target=target,
            left=left,
            right=right,
            op_code=op_code,
            operator=operator,
            nb_slot=_getNbSlotFromOperand(operator, op_code),
            nb_inplace_slot=_getNbInplaceSlotFromOperand(operator, op_code)
            if inplace
            else None,
            sq_slot=sq_slot,
            sq_inplace_slot=sq_inplace_slot,
            object_desc=object_desc,
            int_desc=int_desc,
            long_desc=long_desc,
            float_desc=float_desc,
            list_desc=list_desc,
            tuple_desc=tuple_desc,
            set_desc=set_desc,
            str_desc=str_desc,
            unicode_desc=unicode_desc,
            bytes_desc=bytes_desc,
            c_long_desc=c_long_desc,
            c_digit_desc=c_digit_desc,
        )

        emit_c(code)
        emit_h(getTemplateCodeDeclaredFunction(code))

        if python_requirement:
            emit("#endif")

        emit()


def makeHelperComparisons(
    template, helpers_set, operator, op_code, emit_h, emit_c, emit
):
    # Details to look for, pylint: disable=too-many-locals

    emit(
        '/* C helpers for type specialized "%s" (%s) comparisons */'
        % (operator, op_code)
    )
    emit()

    for target in (object_desc, c_bool_desc):
        python_requirement = _parseRequirements(
            op_code, target, int_desc, int_desc, emit_c
        )

        makeCompareSlotCode(operator, op_code, target, int_desc, int_desc, emit_c)

        if python_requirement:
            emit_c("#endif")

    for helper_name in helpers_set:
        assert helper_name.split("_")[:2] == ["RICH", "COMPARE"], (helper_name,)

        # Filter for the operation.
        if helper_name.split("_")[2] != op_code:
            continue

        _target_code, target, left, right = _parseTypesFromHelper(helper_name)

        assert target is not None, helper_name
        assert left is not None, helper_name
        assert right is not None, helper_name

        python_requirement = _parseRequirements(op_code, target, left, right, emit)

        (
            code,
            helper_target,
            type_desc1,
            type_desc2,
            _operand1,
            _operand2,
        ) = left.getTypeComparisonSpecializationHelper(
            other=right,
            op_code=op_code,
            target=target,
            operand1="operand1",
            operand2="operand2",
        )

        if code:
            makeCompareSlotCode(
                operator, op_code, helper_target, type_desc1, type_desc2, emit_c
            )

        emit(
            '/* Code referring to "%s" corresponds to %s and "%s" to %s. */'
            % (
                left.getHelperCodeName(),
                left.type_desc,
                right.getHelperCodeName(),
                right.type_desc,
            )
        )

        if not python_requirement:
            is_py3_only = False
            is_py2_only = False
        elif python_requirement == "PYTHON_VERSION < 0x300":
            is_py3_only = False
            is_py2_only = True
        elif python_requirement == "PYTHON_VERSION >= 0x300":
            is_py3_only = True
            is_py2_only = False
        else:
            assert False, python_requirement

        code = template.render(
            target=target,
            left=left,
            right=right,
            op_code=op_code,
            reversed_args_op_code=reversed_args_compare_op_codes[op_code],
            operator=operator,
            is_py3_only=is_py3_only,
            is_py2_only=is_py2_only,
            object_desc=object_desc,
            int_desc=int_desc,
        )

        emit_c(code)
        emit_h(getTemplateCodeDeclaredFunction(code))

        if python_requirement:
            emit("#endif")

        emit()


def emitGenerationWarning(emit, template_name):
    emit(
        "/* WARNING, this code is GENERATED. Modify the template %s instead! */"
        % template_name
    )


def emitIDE(emit):
    emit(
        """
/* This file is included from another C file, help IDEs to still parse it on its own. */
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif
"""
    )


def makeHelpersComparisonOperation(operand, op_code):
    specialized_cmp_helpers_set = getSpecializedComparisonOperations()

    template = getDoExtensionUsingTemplateC("HelperOperationComparison.c.j2")

    filename_c = "nuitka/build/static_src/HelpersComparison%s.c" % op_code.capitalize()
    filename_h = "nuitka/build/include/nuitka/helper/comparisons_%s.h" % op_code.lower()

    with withFileOpenedAndAutoFormatted(filename_c) as output_c:
        with withFileOpenedAndAutoFormatted(filename_h) as output_h:

            def emit_h(*args):
                writeLine(output_h, *args)

            def emit_c(*args):
                writeLine(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

            filename_utils = filename_c[:-2] + "Utils.c"

            if os.path.exists(filename_utils):
                emit_c('#include "%s"' % os.path.basename(filename_utils))

            makeHelperComparisons(
                template,
                specialized_cmp_helpers_set,
                operand,
                op_code,
                emit_h,
                emit_c,
                emit,
            )


def makeHelpersBinaryOperation(operand, op_code):
    specialized_op_helpers_set = getSpecializedBinaryOperations(op_code)

    template = getDoExtensionUsingTemplateC("HelperOperationBinary.c.j2")

    filename_c = (
        "nuitka/build/static_src/HelpersOperationBinary%s.c" % op_code.capitalize()
    )
    filename_h = (
        "nuitka/build/include/nuitka/helper/operations_binary_%s.h" % op_code.lower()
    )

    with withFileOpenedAndAutoFormatted(filename_c) as output_c:
        with withFileOpenedAndAutoFormatted(filename_h) as output_h:

            def emit_h(*args):
                writeLine(output_h, *args)

            def emit_c(*args):
                writeLine(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

            filename_utils = filename_c[:-2] + "Utils.c"

            if os.path.exists(filename_utils):
                emit_c('#include "%s"' % os.path.basename(filename_utils))

            makeHelperOperations(
                template,
                False,
                specialized_op_helpers_set,
                operand,
                op_code,
                emit_h,
                emit_c,
                emit,
            )


def makeHelpersInplaceOperation(operand, op_code):
    specialized_op_helpers_set = getSpecializedBinaryOperations("I" + op_code)

    template = getDoExtensionUsingTemplateC("HelperOperationInplace.c.j2")

    filename_c = (
        "nuitka/build/static_src/HelpersOperationInplace%s.c" % op_code.capitalize()
    )
    filename_h = (
        "nuitka/build/include/nuitka/helper/operations_inplace_%s.h" % op_code.lower()
    )

    with withFileOpenedAndAutoFormatted(filename_c) as output_c:
        with withFileOpenedAndAutoFormatted(filename_h) as output_h:

            def emit_h(*args):
                writeLine(output_h, *args)

            def emit_c(*args):
                writeLine(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

            filename_utils = filename_c[:-2] + "Utils.c"

            if os.path.exists(filename_utils):
                emit_c('#include "%s"' % os.path.basename(filename_utils))

            makeHelperOperations(
                template,
                True,
                specialized_op_helpers_set,
                operand,
                op_code,
                emit_h,
                emit_c,
                emit,
            )


def makeHelpersImportHard():
    filename_c = "nuitka/build/static_src/HelpersImportHard.c"
    filename_h = "nuitka/build/include/nuitka/helper/import_hard.h"

    template = getDoExtensionUsingTemplateC("HelperImportHard.c.j2")

    with withFileOpenedAndAutoFormatted(filename_c) as output_c:
        with withFileOpenedAndAutoFormatted(filename_h) as output_h:

            def emit_h(*args):
                writeLine(output_h, *args)

            def emit_c(*args):
                writeLine(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

            for module_name in sorted(hard_modules):
                makeHelperImportModuleHard(
                    template,
                    module_name,
                    emit_h,
                    emit_c,
                    emit,
                )


def makeHelperImportModuleHard(template, module_name, emit_h, emit_c, emit):
    emit('/* C helper for hard import of module "%s" import. */' % module_name)

    python_min_max_version = hard_modules_version.get(module_name)

    if python_min_max_version is not None:
        python_min_version, python_max_version = python_min_max_version

        parts = []

        if python_min_version is not None:
            parts.append("PYTHON_VERSION >= %s" % hex(python_min_version))
        if python_max_version is not None:
            parts.append("PYTHON_VERSION < %s" % hex(python_max_version))

        python_requirement = " && ".join(parts)

    else:
        python_requirement = None

    if python_requirement:
        emit("#if %s" % python_requirement)

    code = template.render(
        module_name=module_name,
        module_code_name=getImportModuleHardCodeName(module_name),
        name=template.name,
        target=object_desc,
        is_stdlib=module_name not in hard_modules_non_stdlib,
    )

    emit_c(code)
    emit_h(getTemplateCodeDeclaredFunction(code))

    if python_requirement:
        emit("#endif")

    emit()


def makeHelperCalls():
    filename_c = "nuitka/build/static_src/HelpersCalling2.c"
    filename_h = "nuitka/build/include/nuitka/helper/calling2.h"

    with withFileOpenedAndAutoFormatted(filename_c) as output_c:
        with withFileOpenedAndAutoFormatted(filename_h) as output_h:

            def emit_h(*args):
                assert args[0] != "extern "
                writeLine(output_h, *args)

            def emit_c(*args):
                writeLine(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            template = getTemplateC(
                "nuitka.code_generation", "CodeTemplateCallsPositional.c.j2"
            )

            emitGenerationWarning(emit, template.name)

            emitIDE(emit)

            for args_count in range(max_quick_call + 1):
                code = getQuickCallCode(args_count=args_count, has_tuple_arg=False)

                emit_c(code)
                emit_h(getTemplateCodeDeclaredFunction(code))

                if args_count >= 1:
                    code = getQuickCallCode(args_count=args_count, has_tuple_arg=True)

                    emit_c(code)
                    emit_h(getTemplateCodeDeclaredFunction(code))

            template = getTemplateC(
                "nuitka.code_generation", "CodeTemplateCallsMixed.c.j2"
            )

            # Only keywords, but not positional arguments, via split args.
            code = getQuickMixedCallCode(
                args_count=0,
                has_tuple_arg=False,
                has_dict_values=True,
            )

            emit_c(code)
            emit_h(getTemplateCodeDeclaredFunction(code))

            for args_count in range(1, max_quick_call + 1):
                for has_tuple_arg in (False, True):
                    for has_dict_values in (False, True):
                        # We do not do that.
                        if not has_dict_values and has_tuple_arg:
                            continue

                        code = getQuickMixedCallCode(
                            args_count=args_count,
                            has_tuple_arg=has_tuple_arg,
                            has_dict_values=has_dict_values,
                        )

                        emit_c(code)
                        emit_h(getTemplateCodeDeclaredFunction(code))

            for args_count in range(1, 5):
                code = getQuickMethodDescriptorCallCode(args_count=args_count)

                emit_c(code)
                emit_h(getTemplateCodeDeclaredFunction(code))

            for args_count in range(max_quick_call + 1):
                code = getQuickMethodCallCode(args_count=args_count)

                emit_c(code)
                emit_h(getTemplateCodeDeclaredFunction(code))


def _makeHelperBuiltinTypeAttributes(
    type_prefix, type_name, python2_methods, python3_methods, emit_c, emit_h
):
    # many cases to deal with, pylint: disable=too-many-branches

    def getVarName(method_name):
        return "%s_builtin_%s" % (type_prefix, method_name)

    for method_name in sorted(set(python2_methods + python3_methods)):
        is_public = method_name in ("format",)

        if method_name in python2_methods and method_name not in python3_methods:
            emit_c("#if PYTHON_VERSION < 0x300")
            if is_public:
                emit_h("#if PYTHON_VERSION < 0x300")
            needs_endif = True
        elif method_name not in python2_methods and method_name in python3_methods:
            emit_c("#if PYTHON_VERSION >= 0x300")
            if is_public:
                emit_h("#if PYTHON_VERSION >= 0x300")
            needs_endif = True
        else:
            needs_endif = False

        if not is_public:
            emit_c("static")

        emit_c("PyObject *%s = NULL;" % getVarName(method_name))

        if is_public:
            emit_h("extern PyObject *%s;" % getVarName(method_name))

        if needs_endif:
            emit_c("#endif")

            if is_public:
                emit_h("#endif")

    if not python3_methods:
        emit_c("#if PYTHON_VERSION < 0x300")
    if not python2_methods:
        emit_c("#if PYTHON_VERSION >= 0x300")

    emit_c("static void _init%sBuiltinMethods(void) {" % type_prefix.capitalize())
    for method_name in sorted(set(python2_methods + python3_methods)):
        if (
            method_name in python2_methods
            and method_name not in python3_methods
            and python3_methods
        ):
            emit_c("#if PYTHON_VERSION < 0x300")
            needs_endif = True
        elif (
            method_name not in python2_methods
            and method_name in python3_methods
            and python2_methods
        ):
            emit_c("#if PYTHON_VERSION >= 0x300")
            needs_endif = True
        else:
            needs_endif = False

        emit_c(
            '%s = PyObject_GetAttrString((PyObject *)&%s, "%s");'
            % (getVarName(method_name), type_name, method_name)
        )

        if needs_endif:
            emit_c("#endif")

    emit_c("}")

    if not python2_methods or not python3_methods:
        emit_c("#endif")


generate_builtin_type_operations = [
    # TODO: For these, we would need an implementation for adding/deleting dictionary values. That
    # has turned out to be too hard so far and these are very good friends, not doing hashing
    # multiple times when reading and writing, so can't do it unless we add something for the
    # Nuitka-Python eventually.
    (
        "tshape_dict",
        dict_desc,
        nuitka.specs.BuiltinDictOperationSpecs,
        ("pop", "popitem", "setdefault"),
    ),
    # TODO: These are very complex things using "string lib" code in CPython,
    # that we do not have easy access to, but we might one day for Nuitka-Python
    # expose it for the static linking of it and then we could in fact call
    # these directly.
    (
        "tshape_str",
        str_desc,
        nuitka.specs.BuiltinStrOperationSpecs,
        (
            "strip",
            "rstrip",
            "lstrip",
            "partition",
            "rpartition",
            "find",
            "rfind",
            "index",
            "rindex",
            "capitalize",
            "upper",
            "lower",
            "swapcase",
            "title",
            "isalnum",
            "isalpha",
            "isdigit",
            "islower",
            "isupper",
            "isspace",
            "istitle",
            "split",
            "rsplit",
            "startswith",
            "endswith",
            "replace",
            "encode",
            "decode",
            "count",
            "expandtabs",
            "translate",
            "ljust",
            "rjust",
            "center",
            "zfill",
            "splitlines",
        ),
    ),
    # TODO: This is using Python2 spec module for Python3 strings, that will be a problem down the
    # road, when version specifics come in.
    (
        "tshape_unicode",
        unicode_desc,
        nuitka.specs.BuiltinUnicodeOperationSpecs,
        (
            "strip",
            "rstrip",
            "lstrip",
            "find",
            "rfind",
            "index",
            "rindex",
            "capitalize",
            "upper",
            "lower",
            "swapcase",
            "title",
            "isalnum",
            "isalpha",
            "isdigit",
            "islower",
            "isupper",
            "isspace",
            "istitle",
            "split",
            "rsplit",
            "startswith",
            "endswith",
            "replace",
            "encode",
            "count",
            "expandtabs",
            "translate",
            "ljust",
            "rjust",
            "center",
            "zfill",
            "splitlines",
        ),
    ),
    (
        "tshape_bytes",
        bytes_desc,
        nuitka.specs.BuiltinBytesOperationSpecs,
        ("decode",),
    ),
]


def makeHelperBuiltinTypeMethods():
    # Many details, pylint: disable=too-many-locals
    filename_c = "nuitka/build/static_src/HelpersBuiltinTypeMethods.c"
    filename_h = "nuitka/build/include/nuitka/helper/operations_builtin_types.h"
    with withFileOpenedAndAutoFormatted(filename_c) as output_c:
        with withFileOpenedAndAutoFormatted(filename_h) as output_h:

            def emit_h(*args):
                writeLine(output_h, *args)

            def emit_c(*args):
                writeLine(output_c, *args)

            def emit(*args):
                emit_h(*args)
                emit_c(*args)

            emitIDE(emit)

            _makeHelperBuiltinTypeAttributes(
                "str", "PyString_Type", python2_str_methods, (), emit_c, emit_h
            )
            _makeHelperBuiltinTypeAttributes(
                "bytes", "PyBytes_Type", (), python3_bytes_methods, emit_c, emit_h
            )
            _makeHelperBuiltinTypeAttributes(
                "unicode",
                "PyUnicode_Type",
                python2_unicode_methods,
                python3_str_methods,
                emit_c,
                emit_h,
            )
            _makeHelperBuiltinTypeAttributes(
                "dict",
                "PyDict_Type",
                python2_dict_methods,
                python3_dict_methods,
                emit_c,
                emit_h,
            )

            template = getDoExtensionUsingTemplateC("HelperBuiltinMethodOperation.c.j2")

            for (
                shape_name,
                type_desc,
                spec_module,
                method_names,
            ) in generate_builtin_type_operations:
                if type_desc.python_requirement:
                    emit("#if %s" % type_desc.python_requirement)

                for method_name in sorted(method_names):
                    (
                        present,
                        arg_names,
                        _arg_tests,
                        arg_name_mapping,
                        arg_counts,
                    ) = getMethodVariations(
                        spec_module=spec_module,
                        shape_name=shape_name,
                        method_name=method_name,
                        must_exist=True,
                    )

                    assert present, method_name

                    def formatArgumentDeclaration(arg_types, arg_names, starting):
                        return formatArgs(
                            [
                                arg_type.getVariableDecl(arg_name)
                                for arg_type, arg_name in zip(arg_types, arg_names)
                            ],
                            starting=starting,
                        )

                    # Function is used immediately in same loop, pylint: disable=cell-var-from-loop
                    def replaceArgNameForC(arg_name):
                        if arg_name in arg_name_mapping:
                            arg_name = arg_name_mapping[arg_name]

                        if arg_name in ("default", "new"):
                            return arg_name + "_value"
                        else:
                            return arg_name

                    for arg_count in arg_counts:
                        variant_args = [
                            replaceArgNameForC(arg_name)
                            for arg_name in arg_names[:arg_count]
                        ]

                        code = template.render(
                            object_desc=object_desc,
                            builtin_type=type_desc,
                            builtin_arg_name=type_desc.type_name,
                            method_name=method_name,
                            api_suffix=str(arg_count + 1)
                            if len(arg_counts) > 1
                            else "",
                            arg_names=variant_args,
                            arg_types=[object_desc] * len(variant_args),
                            formatArgumentDeclaration=formatArgumentDeclaration,
                            zip=zip,
                            len=len,
                            name=template.name,
                        )

                        emit_c(code)
                        emit_h(getTemplateCodeDeclaredFunction(code))
                if type_desc.python_requirement:
                    emit("#endif")


def main():

    # Cover many things once first, then cover all for quicker turnaround during development.
    makeHelperBuiltinTypeMethods()
    makeHelpersComparisonOperation("==", "EQ")
    makeHelpersBinaryOperation("+", "ADD")
    makeHelpersInplaceOperation("+", "ADD")

    makeHelpersImportHard()

    makeHelperCalls()

    makeHelpersBinaryOperation("-", "SUB")
    makeHelpersBinaryOperation("*", "MULT")
    makeHelpersBinaryOperation("%", "MOD")
    makeHelpersBinaryOperation("|", "BITOR")
    makeHelpersBinaryOperation("&", "BITAND")
    makeHelpersBinaryOperation("^", "BITXOR")
    makeHelpersBinaryOperation("<<", "LSHIFT")
    makeHelpersBinaryOperation(">>", "RSHIFT")
    makeHelpersBinaryOperation("//", "FLOORDIV")
    makeHelpersBinaryOperation("/", "TRUEDIV")
    makeHelpersBinaryOperation("/", "OLDDIV")
    makeHelpersBinaryOperation("divmod", "DIVMOD")
    makeHelpersBinaryOperation("**", "POW")
    makeHelpersBinaryOperation("@", "MATMULT")

    makeHelpersInplaceOperation("-", "SUB")
    makeHelpersInplaceOperation("*", "MULT")
    makeHelpersInplaceOperation("%", "MOD")
    makeHelpersInplaceOperation("|", "BITOR")
    makeHelpersInplaceOperation("&", "BITAND")
    makeHelpersInplaceOperation("^", "BITXOR")
    makeHelpersInplaceOperation("<<", "LSHIFT")
    makeHelpersInplaceOperation(">>", "RSHIFT")
    makeHelpersInplaceOperation("//", "FLOORDIV")
    makeHelpersInplaceOperation("/", "TRUEDIV")
    makeHelpersInplaceOperation("/", "OLDDIV")
    makeHelpersInplaceOperation("**", "POW")
    makeHelpersInplaceOperation("@", "MATMULT")

    makeHelpersComparisonOperation("!=", "NE")
    makeHelpersComparisonOperation("<=", "LE")
    makeHelpersComparisonOperation(">=", "GE")
    makeHelpersComparisonOperation(">", "GT")
    makeHelpersComparisonOperation("<", "LT")
