#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Python operator tables

These are mostly used to resolve the operator in the module operator and to know the list
of operations allowed.

"""

import operator
import re

from nuitka.PythonVersions import python_version

binary_operator_functions = {
    "Add": operator.add,
    "Sub": operator.sub,
    "Pow": operator.pow,
    "Mult": operator.mul,
    "FloorDiv": operator.floordiv,
    "TrueDiv": operator.truediv,
    "Mod": operator.mod,
    "LShift": operator.lshift,
    "RShift": operator.rshift,
    "BitAnd": operator.and_,
    "BitOr": operator.or_,
    "BitXor": operator.xor,
    "Divmod": divmod,
    "IAdd": operator.iadd,
    "ISub": operator.isub,
    "IPow": operator.ipow,
    "IMult": operator.imul,
    "IFloorDiv": operator.ifloordiv,
    "ITrueDiv": operator.itruediv,
    "IMod": operator.imod,
    "ILShift": operator.ilshift,
    "IRShift": operator.irshift,
    "IBitAnd": operator.iand,
    "IBitOr": operator.ior,
    "IBitXor": operator.ixor,
}

# Python 2 only operator
if python_version < 0x300:
    binary_operator_functions["OldDiv"] = operator.div
    binary_operator_functions["IOldDiv"] = operator.idiv  # spell-checker: ignore idiv

# Python 3.5 only operator
if python_version >= 0x350:
    binary_operator_functions["MatMult"] = operator.matmul
    binary_operator_functions["IMatMult"] = operator.imatmul

unary_operator_functions = {
    "UAdd": operator.pos,
    "USub": operator.neg,
    "Invert": operator.invert,
    "Repr": repr,
    # Boolean not is treated an unary operator.
    "Not": operator.not_,
    "Abs": operator.abs,
}


rich_comparison_functions = {
    "Lt": operator.lt,
    "LtE": operator.le,
    "Eq": operator.eq,
    "NotEq": operator.ne,
    "Gt": operator.gt,
    "GtE": operator.ge,
}

other_comparison_functions = {
    "Is": operator.is_,
    "IsNot": operator.is_not,
    "In": lambda value1, value2: value1 in value2,
    "NotIn": lambda value1, value2: value1 not in value2,
}

comparison_inversions = {
    "Is": "IsNot",
    "IsNot": "Is",
    "In": "NotIn",
    "NotIn": "In",
    "Lt": "GtE",
    "GtE": "Lt",
    "Eq": "NotEq",
    "NotEq": "Eq",
    "Gt": "LtE",
    "LtE": "Gt",
    "exception_match": "exception_mismatch",
    "exception_mismatch": "exception_match",
}

# Comparator change when swapping arguments of comparisons.
rich_comparison_arg_swaps = {
    "Lt": "Gt",
    "GtE": "LtE",
    "Eq": "Eq",
    "NotEq": "NotEq",
    "Gt": "Lt",
    "LtE": "GtE",
}


all_comparison_functions = dict(rich_comparison_functions)
all_comparison_functions.update(other_comparison_functions)


def matchException(left, right):
    # This doesn't yet work, make it error exit and silence PyLint for now.
    # pylint: disable=unused-argument

    if python_version >= 0x300:
        if type(right) is tuple:
            for element in right:
                if not isinstance(BaseException, element):
                    raise TypeError(
                        "catching classes that do not inherit from BaseException is not allowed"
                    )
        elif not isinstance(BaseException, right):
            raise TypeError(
                "catching classes that do not inherit from BaseException is not allowed"
            )

    import os

    os._exit(16)


all_comparison_functions["exception_match"] = matchException


# Regex to parse format specifiers.
#
# spell-checker: disable
# Matches:
# %                     - format identifier spec
# (?:\(([^)]*)\))?      - mapping key (optional)
# ([#0\- +]*)           - flags
# (\*|\d+)?             - width
# (?:\.(\*|\d+))?       - precision (optional)
# [hlL]?                - length modifier (optional, ignored)
# ([diouxXeEfFgGcrs%a]) - conversion type
_format_spec_re = re.compile(
    r"%"
    r"(?:\(([^)]*)\))?"
    r"([#0\- +]*)"
    r"(\*|\d+)?"
    r"(?:\.(\*|\d+))?"
    r"[hlL]?"
    r"([diouxXeEfFgGcrs%a])"
)
# spell-checker: enable


def _getFormatSpecSize(match, args, arg_idx, mapping_mode):
    """Calculate the size of a single format specifier match.

    Returns:
        tuple: (item_len, args_consumed)
            item_len (int or None): The estimated size of the formatted item, or None if optimization should be skipped.
            args_consumed (int or None): The number of arguments consumed by this specifier.
    """
    # Result size or None for checks that say to not optimize.
    # pylint: disable=too-many-branches,too-many-locals,too-many-return-statements,too-many-statements

    mapping_key, _flags, width, precision, type_char = match.groups()

    if type_char == "%":
        return 1, 0

    current_arg = None
    target_width = 0
    target_precision = None

    if mapping_key is not None:
        if not mapping_mode or mapping_key not in args:
            return None, None

        current_arg = args[mapping_key]

        # Mapping does not support * width/prec. # spell-checker: disable-line
        if width == "*" or precision == "*":
            return None, None
    else:
        if mapping_mode:
            return None, None

        args_consumed = 0

        if width == "*":
            if arg_idx + args_consumed >= len(args):
                return None, None
            target_width = args[arg_idx + args_consumed]
            args_consumed += 1
        elif width:
            target_width = int(width)

        if precision == "*":
            if arg_idx + args_consumed >= len(args):
                return None, None
            target_precision = args[arg_idx + args_consumed]
            args_consumed += 1
        elif precision:
            target_precision = int(precision)

        if current_arg is None:
            if arg_idx + args_consumed >= len(args):
                return None, None
            current_arg = args[arg_idx + args_consumed]
            args_consumed += 1

    arg_len = 0

    # Calculate the size of the argument.
    if type_char == "s":
        s_val = str(current_arg)
        if target_precision is not None and target_precision >= 0:
            s_val = s_val[:target_precision]
        arg_len = len(s_val)

    elif type_char in "diouxX":  # spell-checker: disable-line
        arg_len = len(str(current_arg))
        if target_precision is not None:
            arg_len = max(arg_len, target_precision)

    elif type_char in "eEfFgG":
        precision = target_precision if target_precision is not None else 6
        # Heuristic for float formatting.
        try:
            val_str = "{:.{p}f}".format(current_arg, p=precision)
        except ValueError:
            return None, None
        else:
            arg_len = len(val_str)

    elif type_char == "c":
        arg_len = 1
    elif type_char == "r":
        arg_len = len(repr(current_arg))

    if mapping_key is not None:
        return max(target_width, arg_len), 0
    else:
        return max(target_width, arg_len), args_consumed


def predictStringFormatSizeRange(format_string, args):
    """Predict the size range of the formatted string.

    Args:
        format_string (str): The format string.
        args: The right-hand side operand (can be dict, tuple, or single value).

    Returns:
        tuple or None: (min_size, max_size) or None if unpredictable.
    """
    # Check for mapping being involved.
    mapping_mode = False
    if type(args) is dict:
        # Check if format uses mapping keys.
        match = _format_spec_re.search(format_string)
        if match and match.group(1) is not None:
            mapping_mode = True

    if mapping_mode is False and type(args) is not tuple:
        args = (args,)

    min_len = 0
    max_len = 0
    last_end = 0
    arg_idx = 0

    # We need to iterate over the format string and add up the parts.
    for match in _format_spec_re.finditer(format_string):
        start, end = match.span()

        literal_len = start - last_end
        min_len += literal_len
        max_len += literal_len

        last_end = end

        item_len, args_consumed = _getFormatSpecSize(match, args, arg_idx, mapping_mode)

        if item_len is None:
            return None

        min_len += item_len
        max_len += item_len
        arg_idx += args_consumed

    literal_len = len(format_string) - last_end
    min_len += literal_len
    max_len += literal_len

    return min_len, max_len


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
