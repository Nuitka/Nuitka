#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Codes for PGO.

These generate the PGO probes and the checks that PGO data assumptions hold
at run time, e.g. for the result of a class creation '__prepare__' call, and
are meant to be reusable for other kinds of PGO data.
"""

from nuitka.nodes.shapes.BuiltinTypeShapes import (
    tshape_bool,
    tshape_bytearray,
    tshape_bytes,
    tshape_complex,
    tshape_dict,
    tshape_float,
    tshape_frozenset,
    tshape_int,
    tshape_list,
    tshape_long,
    tshape_none,
    tshape_set,
    tshape_str,
    tshape_tuple,
    tshape_type,
    tshape_unicode,
)
from nuitka.nodes.shapes.StandardShapes import tshape_unknown
from nuitka.PythonVersions import python_version

from .ErrorCodes import getErrorExitRaiseCode, getRaiseExceptionStateCode

# The recorded PGO values must match exactly, so subclasses are a mismatch.
_value_type_check_codes = {
    tshape_none: "(%s == Py_None)",
    tshape_bool: "PyBool_Check(%s)",
    tshape_float: "PyFloat_CheckExact(%s)",
    tshape_complex: "PyComplex_CheckExact(%s)",
    tshape_bytearray: "PyByteArray_CheckExact(%s)",
    tshape_tuple: "PyTuple_CheckExact(%s)",
    tshape_list: "PyList_CheckExact(%s)",
    tshape_set: "PySet_CheckExact(%s)",
    tshape_frozenset: "PyFrozenSet_CheckExact(%s)",
    tshape_dict: "PyDict_CheckExact(%s)",
    tshape_type: "PyType_CheckExact(%s)",
}

# Only empty values are recorded by PGO so far, hence the sizes are all 0.
_value_size_check_codes = {
    tshape_bytearray: "PyByteArray_GET_SIZE(%s) == 0",
    tshape_tuple: "PyTuple_GET_SIZE(%s) == 0",
    tshape_list: "PyList_GET_SIZE(%s) == 0",
    tshape_set: "PySet_GET_SIZE(%s) == 0",
    tshape_frozenset: "PySet_GET_SIZE(%s) == 0",
    tshape_dict: "DICT_SIZE(%s) == 0",
}

if python_version >= 0x300:
    _value_type_check_codes[tshape_int] = "PyLong_CheckExact(%s)"
    _value_type_check_codes[tshape_str] = "PyUnicode_CheckExact(%s)"
    _value_type_check_codes[tshape_bytes] = "PyBytes_CheckExact(%s)"

    _value_size_check_codes[tshape_str] = "PyUnicode_GET_LENGTH(%s) == 0"
    _value_size_check_codes[tshape_bytes] = "PyBytes_GET_SIZE(%s) == 0"
else:
    _value_type_check_codes[tshape_int] = "PyInt_CheckExact(%s)"
    _value_type_check_codes[tshape_long] = "PyLong_CheckExact(%s)"
    _value_type_check_codes[tshape_str] = "PyString_CheckExact(%s)"
    _value_type_check_codes[tshape_unicode] = "PyUnicode_CheckExact(%s)"

    _value_size_check_codes[tshape_str] = "PyString_GET_SIZE(%s) == 0"
    _value_size_check_codes[tshape_unicode] = "PyUnicode_GET_SIZE(%s) == 0"


def getPGOProbeModuleEnterCode(module_name):
    """Get the PGO probe code for entering a module.

    Args:
        module_name: Module name of the module, a `ModuleName` object.

    Returns:
        Code for the probe.
    """

    return "PGO_onModuleEntered(%s);" % module_name.asCString()


def getPGOProbeModuleExitCode(module_name, had_error):
    """Get the PGO probe code for leaving a module.

    Args:
        module_name: Module name of the module, a `ModuleName` object.
        had_error: Whether the module was left with an error.

    Returns:
        Code for the probe.
    """

    return "PGO_onModuleExit(%s, %s);" % (
        module_name.asCString(),
        "true" if had_error else "false",
    )


def _getValueTypeCheckCode(type_shape_to_check, value_name):
    """Get the C condition for the type check of a value shape.

    Args:
        type_shape_to_check: The type shape the value should have.
        value_name: Name of the value to check.

    Returns:
        C condition for the type check.
    """

    check_code = _value_type_check_codes.get(type_shape_to_check)

    if check_code is None:
        assert False, type_shape_to_check

    return check_code % value_name


def _getValueSizeCheckCode(type_shape_to_check, value_name):
    """Get the C condition for the size check of a value shape.

    Args:
        type_shape_to_check: The type shape the value should have.
        value_name: Name of the value to check.

    Returns:
        C condition for the size check.

    Notes:
        Only empty values are used from PGO data for now, so sizes are
        compared against 0, and this must only be used after the type check
        has passed.
    """

    check_code = _value_size_check_codes.get(type_shape_to_check)

    if check_code is None:
        assert False, type_shape_to_check

    return check_code % value_name


def checkPGOValueShape(
    type_shape_to_check, value_name, description, may_raise, emit, context
):
    """Check that a value has the type shape known from PGO data.

    Args:
        type_shape_to_check: The type shape to check for.
        value_name: Name of the value to check.
        description: Description of the value for error messages.
        may_raise: Whether a PGO mismatch may raise an exception, otherwise
            the check can only be a `NUITKA_CANNOT_GET_HERE`.
        emit: Function to emit code.
        context: Code generation context.

    Notes:
        The type and size conditions to check are produced by
        `_getValueTypeCheckCode` and `_getValueSizeCheckCode`, this only
        handles their failure.
    """

    assert type_shape_to_check is not tshape_unknown, type_shape_to_check

    condition = "!(%s && %s)" % (
        _getValueTypeCheckCode(
            type_shape_to_check=type_shape_to_check, value_name=value_name
        ),
        _getValueSizeCheckCode(
            type_shape_to_check=type_shape_to_check, value_name=value_name
        ),
    )

    if may_raise:
        getErrorExitRaiseCode(
            condition=condition,
            set_exception=getRaiseExceptionStateCode(
                exception_type_name="RuntimeError",
                exception_message="PGO mismatch for %s." % description,
                context=context,
            ),
            emit=emit,
            context=context,
        )
    else:
        emit("""\
if (%s) {
    NUITKA_CANNOT_GET_HERE("PGO mismatch for %s.");
}""" % (condition, description))


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
