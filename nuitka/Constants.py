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
""" Module for constants in Nuitka.

This contains tools to compare, classify and test constants.
"""

import math
import sys
from types import BuiltinFunctionType

from nuitka.Builtins import builtin_type_names
from nuitka.PythonVersions import python_version

from .__past__ import GenericAlias, UnionType, iterItems, long, unicode, xrange
from .Builtins import (
    builtin_anon_names,
    builtin_anon_value_list,
    builtin_exception_values_list,
    builtin_named_values_list,
)

NoneType = type(None)


def compareConstants(a, b):
    # Many many cases to deal with, pylint: disable=too-many-branches,too-many-return-statements

    # Supposed fast path for comparison.
    if type(a) is not type(b):
        return False

    # Now it's either not the same, or it is a container that contains NaN or it
    # is a complex or float that is NaN, the other cases can use == at the end.
    if type(a) is complex:
        return compareConstants(a.imag, b.imag) and compareConstants(a.real, b.real)

    if type(a) is float:
        # Check sign first, -0.0 is not 0.0, or -nan is not nan, it has a
        # different sign for a start.
        if math.copysign(1.0, a) != math.copysign(1.0, b):
            return False

        if math.isnan(a) and math.isnan(b):
            return True

        return a == b

    if type(a) in (tuple, list):
        if len(a) != len(b):
            return False

        for ea, eb in zip(a, b):
            if not compareConstants(ea, eb):
                return False
        return True

    if type(a) is dict:
        if len(a) != len(b):
            return False

        for ea1, ea2 in iterItems(a):
            for eb1, eb2 in iterItems(b):
                if compareConstants(ea1, eb1) and compareConstants(ea2, eb2):
                    break
            else:
                return False
        return True

    if type(a) in (frozenset, set):
        if len(a) != len(b):
            return False

        for ea in a:
            if ea not in b:
                # Due to NaN values, we need to compare each set element with
                # all the other set to be really sure.
                for eb in b:
                    if compareConstants(ea, eb):
                        break
                else:
                    return False
        return True

    if type(a) is xrange:
        return str(a) == str(b)

    # The NaN values of float and complex may let this fail, even if the
    # constants are built in the same way, therefore above checks.
    return a == b


# These built-in type references are kind of constant too. The list should be
# complete.
constant_builtin_types = (
    int,
    str,
    float,
    list,
    tuple,
    set,
    dict,
    slice,
    complex,
    xrange,
    NoneType,
)

if python_version >= 0x300:
    constant_builtin_types += (bytes,)
else:
    constant_builtin_types += (
        unicode,
        long,
        # This has no name in Python, but the natural one in C-API.
        builtin_anon_names["instance"],
    )


def isConstant(constant):
    # Too many cases and all return, that is how we do it here,
    # pylint: disable=too-many-branches,too-many-return-statements

    constant_type = type(constant)

    if constant_type is dict:
        for key, value in iterItems(constant):
            if not isConstant(key):
                return False
            if not isConstant(value):
                return False
        return True
    elif constant_type in (tuple, list):
        for element_value in constant:
            if not isConstant(element_value):
                return False
        return True
    elif constant_type is slice:
        if (
            not isConstant(constant.start)
            or not isConstant(constant.stop)
            or not isConstant(constant.step)
        ):
            return False

        return True
    elif constant_type in (
        str,
        unicode,
        complex,
        int,
        long,
        bool,
        float,
        NoneType,
        range,
        bytes,
        set,
        frozenset,
        xrange,
        bytearray,
    ):
        return True
    elif constant in (Ellipsis, NoneType, NotImplemented):
        return True
    elif constant in builtin_anon_value_list:
        return True
    elif constant_type is type:
        # Maybe pre-build this as a set for quicker testing.
        return (
            constant.__name__ in builtin_type_names
            or constant in builtin_exception_values_list
        )
    elif constant_type is BuiltinFunctionType and constant in builtin_named_values_list:
        # TODO: Some others could also be usable and even interesting, but
        # then probably should go into other node types, e.g. str.join is
        # a candidate.
        return True
    elif constant_type is GenericAlias:
        return True
    elif constant_type is UnionType:
        return True
    elif constant is sys.version_info:
        return True
    else:
        return False


def isMutable(constant):
    """Is a constant mutable

    That means a user of a reference to it, can modify it. Strings are
    a prime example of immutable, dictionaries are mutable.
    """
    # Many cases and all return, that is how we do it here,
    # pylint: disable=too-many-branches,too-many-return-statements

    constant_type = type(constant)

    if constant_type in (
        str,
        unicode,
        complex,
        int,
        long,
        bool,
        float,
        NoneType,
        range,
        bytes,
        slice,
        xrange,
        type,
        BuiltinFunctionType,
    ):
        return False
    elif constant_type in (dict, list, set, bytearray):
        return True
    elif constant_type is tuple:
        for value in constant:
            if isMutable(value):
                return True
        return False
    elif constant_type is frozenset:
        for value in constant:
            if isMutable(value):
                return True
        return False
    elif constant is Ellipsis:
        return False
    elif constant is NotImplemented:
        return False
    elif constant_type is GenericAlias:
        return isMutable(constant.__origin__) or isMutable(constant.__args__)
    elif constant_type is UnionType:
        return False
    elif constant is sys.version_info:
        return False
    else:
        assert False, repr(constant)


def isHashable(constant):
    """Is a constant hashable

    That means a user of a reference to it, can use it for dicts and set
    keys. This is distinct from mutable, there is one types that is not
    mutable, and still not hashable: slices.
    """
    # Many cases and all return, that is how we do it here,
    # pylint: disable=too-many-return-statements

    constant_type = type(constant)

    if constant_type in (
        str,
        unicode,
        complex,
        int,
        long,
        bool,
        float,
        NoneType,
        xrange,
        bytes,
        type,
        BuiltinFunctionType,
    ):
        return True
    elif constant_type in (dict, list, set, slice, bytearray):
        return False
    elif constant_type is tuple:
        for value in constant:
            if not isHashable(value):
                return False
        return True
    elif constant_type is frozenset:
        for value in constant:
            if not isHashable(value):
                return False
        return True
    elif constant is Ellipsis:
        return True
    else:
        assert False, constant_type


def getUnhashableConstant(constant):
    # Too many cases and all return, that is how we do it here,
    # pylint: disable=too-many-return-statements

    constant_type = type(constant)

    if constant_type in (
        str,
        unicode,
        complex,
        int,
        long,
        bool,
        float,
        NoneType,
        xrange,
        bytes,
        type,
        BuiltinFunctionType,
    ):
        return None
    elif constant_type in (dict, list, set):
        return constant
    elif constant_type is tuple:
        for value in constant:
            res = getUnhashableConstant(value)
            if res is not None:
                return res
        return None
    elif constant is Ellipsis:
        return None
    elif constant in constant_builtin_types:
        return None
    elif constant_type is slice:
        return None
    else:
        assert False, constant_type


def createConstantDict(keys, values):
    # Create it proper size immediately.
    constant_value = dict.fromkeys(keys, None)

    for key, value in zip(keys, values):
        constant_value[key] = value

    return constant_value


def isCompileTimeConstantValue(value):
    """Determine if a value will be usable at compile time."""
    # This needs to match code in makeCompileTimeConstantReplacementNode
    if isConstant(value):
        return True
    elif type(value) is type:
        return True
    else:
        return False


# Shared empty values, it would cost time to create them locally.
the_empty_dict = {}
the_empty_list = []
the_empty_set = set()
the_empty_bytearray = bytearray()

the_empty_tuple = ()
the_empty_frozenset = frozenset()
the_empty_slice = slice(None)

the_empty_unicode = unicode()  # black doesn't let us write u"" anymore.
