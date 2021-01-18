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
""" Low level constant code generation.

This deals with constants, there creation, there access, and some checks about
them. Even mutable constants should not change during the course of the
program.

There are shared constants, which are created for multiple modules to use, you
can think of them as globals. And there are module local constants, which are
for a single module only.

"""

import ctypes
import marshal
import os
import sys

from nuitka import Options
from nuitka.__past__ import (  # pylint: disable=I0021,redefined-builtin
    iterItems,
    xrange,
)
from nuitka.Constants import compareConstants, getConstantWeight, isMutable
from nuitka.constants.Serialization import ConstantAccessor
from nuitka.PythonVersions import python_version
from nuitka.Tracing import codegen_missing
from nuitka.Version import getNuitkaVersion

from .ErrorCodes import getReleaseCode
from .GlobalConstants import getConstantDefaultPopulation
from .Namify import namifyConstant
from .templates.CodeTemplatesConstants import template_constants_reading
from .templates.CodeTemplatesModules import template_header_guard


def generateConstantReferenceCode(to_name, expression, emit, context):
    """ Assign the constant behind the expression to to_name."""

    getConstantAccess(
        to_name=to_name,
        constant=expression.getCompileTimeConstant(),
        emit=emit,
        context=context,
    )


def generateConstantNoneReferenceCode(to_name, expression, emit, context):
    """ Assign 'None' to to_name."""

    # No context or other knowledge needed, pylint: disable=unused-argument

    if to_name.c_type == "nuitka_bool":
        emit("%s = NUITKA_BOOL_FALSE;" % to_name)
    else:
        emit("%s = Py_None;" % to_name)


def generateConstantTrueReferenceCode(to_name, expression, emit, context):
    """ Assign 'True' to to_name."""

    # No context or other knowledge needed, pylint: disable=unused-argument

    if to_name.c_type == "nuitka_bool":
        emit("%s = NUITKA_BOOL_TRUE;" % to_name)
    else:
        emit("%s = Py_True;" % to_name)


def generateConstantFalseReferenceCode(to_name, expression, emit, context):
    """ Assign 'False' to to_name."""

    # No context or other knowledge needed, pylint: disable=unused-argument

    if to_name.c_type == "nuitka_bool":
        emit("%s = NUITKA_BOOL_FALSE;" % to_name)
    else:
        emit("%s = Py_False;" % to_name)


def generateConstantEllipsisReferenceCode(to_name, expression, emit, context):
    """ Assign 'Ellipsis' to to_name."""

    # No context or other knowledge needed, pylint: disable=unused-argument

    if to_name.c_type == "nuitka_bool":
        emit("%s = NUITKA_BOOL_FALSE;" % to_name)
    else:
        emit("%s = Py_Ellipsis;" % to_name)


sizeof_long = ctypes.sizeof(ctypes.c_long)

max_unsigned_long = 2 ** (sizeof_long * 8) - 1

# The gcc gives a warning for -2**sizeof_long*8-1, which is still an "int", but
# seems to not work (without warning) as literal, so avoid it.
min_signed_long = -(2 ** (sizeof_long * 8 - 1) - 1)

done = set()


def decideMarshal(constant_value):
    """Decide of a constant can be created using "marshal" module methods.

    This is not the case for everything. A prominent exception is types,
    they are constants, but the "marshal" module refuses to work with
    them.
    """

    # Many cases to deal with, pylint: disable=too-many-return-statements

    constant_type = type(constant_value)

    if constant_type is type:
        # Types cannot be marshaled, there is no choice about it.
        return False
    elif constant_type is dict:
        # Look at all the keys an values, if one of it cannot be marshaled,
        # or should not, that is it.
        for key, value in iterItems(constant_value):
            if not decideMarshal(key):
                return False
            if not decideMarshal(value):
                return False
    elif constant_type in (tuple, list, set, frozenset):
        for element_value in constant_value:
            if not decideMarshal(element_value):
                return False
    elif constant_type is xrange:
        return False
    elif constant_type is slice:
        return False

    return True


def isMarshalConstant(constant_value):
    """Decide if we want to use marshal to create a constant.

    The reason we do this, is because creating dictionaries with 700
    elements creates a lot of C code, while gaining usually no performance
    at all. The MSVC compiler is especially notorious about hanging like
    forever with this active, due to its optimizer not scaling.

    Therefore we use a constant "weight" (how expensive it is), and apply
    that to decide.

    If marshal is not possible, or constant "weight" is too large, we
    don't do it. Also, for some constants, marshal can fail, and return
    other values. Check that too. In that case, we have to create it.
    """

    if not decideMarshal(constant_value):
        return False

    if getConstantWeight(constant_value) < 20:
        return False

    try:
        marshal_value = marshal.dumps(constant_value)
    except ValueError:
        if Options.is_debug:
            codegen_missing.warning("Failed to marshal constant %r." % constant_value)

        return False

    restored = marshal.loads(marshal_value)

    r = compareConstants(constant_value, restored)
    if not r:
        pass
        # TODO: Potentially warn about these, where that is not the case.

    return r


def getConstantAccess(to_name, constant, emit, context):
    # Many cases, because for each type, we may copy or optimize by creating
    # empty.  pylint: disable=too-many-branches,too-many-statements

    if to_name.c_type == "nuitka_bool" and Options.is_debug:
        codegen_missing.info("Missing optimization for constant to C bool.")

    if type(constant) is dict:
        if constant:
            for key, value in iterItems(constant):
                # key cannot be mutable.
                assert not isMutable(key)
                if isMutable(value):
                    needs_deep = True
                    break
            else:
                needs_deep = False

            if needs_deep:
                code = "DEEP_COPY(%s)" % context.getConstantCode(constant)
            else:
                code = "PyDict_Copy(%s)" % context.getConstantCode(constant)
        else:
            code = "PyDict_New()"

        ref_count = 1
    elif type(constant) is set:
        if constant:
            code = "PySet_New(%s)" % context.getConstantCode(constant)
        else:
            code = "PySet_New(NULL)"

        ref_count = 1
    elif type(constant) is list:
        if constant:
            for value in constant:
                if isMutable(value):
                    needs_deep = True
                    break
            else:
                needs_deep = False

            if needs_deep:
                code = "DEEP_COPY(%s)" % context.getConstantCode(constant)
            else:
                code = "LIST_COPY(%s)" % context.getConstantCode(constant)
        else:
            code = "PyList_New(0)"

        ref_count = 1
    elif type(constant) is tuple:
        for value in constant:
            if isMutable(value):
                needs_deep = True
                break
        else:
            needs_deep = False

        if needs_deep:
            code = "DEEP_COPY(%s)" % context.getConstantCode(constant)

            ref_count = 1
        else:
            code = context.getConstantCode(constant)

            ref_count = 0
    elif type(constant) is bytearray:
        code = "BYTEARRAY_COPY(%s)" % context.getConstantCode(constant)
        ref_count = 1
    else:
        code = context.getConstantCode(constant=constant)

        ref_count = 0

    if to_name.c_type == "PyObject *":
        value_name = to_name
    else:
        value_name = context.allocateTempName("constant_value")

    emit("%s = %s;" % (value_name, code))

    if to_name is not value_name:
        to_name.getCType().emitAssignConversionCode(
            to_name=to_name,
            value_name=value_name,
            needs_check=False,
            emit=emit,
            context=context,
        )

        # Above is supposed to transfer ownership.
        if ref_count:
            getReleaseCode(value_name, emit, context)
    else:
        if ref_count:
            context.addCleanupTempName(value_name)


def getConstantsDefinitionCode():
    """Create the code code "__constants.c" and "__constants.h" files.

    This needs to create code to make all global constants (used in more
    than one module) and create them.

    """
    constant_accessor = ConstantAccessor(
        data_filename="__constants.const", top_level_name="global_constants"
    )

    lines = []

    for constant_value in getConstantDefaultPopulation():
        identifier = constant_accessor.getConstantCode(constant_value)

        assert "[" in identifier, (identifier, constant_value)

        lines.append("// %s" % repr(constant_value))
        lines.append(
            "#define const_%s %s" % (namifyConstant(constant_value), identifier)
        )

    sys_executable = None

    if not Options.shallMakeModule():
        if Options.isStandaloneMode():
            # The directory is added back at run time.
            sys_executable = constant_accessor.getConstantCode(
                os.path.basename(sys.executable)
            )
        else:
            sys_executable = constant_accessor.getConstantCode(sys.executable)

    sys_prefix = None
    sys_base_prefix = None
    sys_exec_prefix = None
    sys_base_exec_prefix = None

    # TODO: This part is needed for main program only, so do it there?
    if not Options.shallMakeModule() and not Options.isStandaloneMode():
        sys_prefix = constant_accessor.getConstantCode(sys.prefix)
        sys_exec_prefix = constant_accessor.getConstantCode(sys.exec_prefix)

        if python_version >= 0x300:
            sys_base_prefix = constant_accessor.getConstantCode(sys.base_prefix)
            sys_base_exec_prefix = constant_accessor.getConstantCode(
                sys.base_exec_prefix
            )

    lines.insert(
        0,
        "extern PyObject *global_constants[%d];"
        % constant_accessor.getConstantsCount(),
    )

    header = template_header_guard % {
        "header_guard_name": "__NUITKA_GLOBAL_CONSTANTS_H__",
        "header_body": "\n".join(lines),
    }

    major, minor, micro = getNuitkaVersion().split(".")[:3]

    if "rc" in micro:
        micro = micro[: micro.find("rc")]
        level = "candidate"
    else:
        level = "release"

    body = template_constants_reading % {
        "global_constants_count": constant_accessor.getConstantsCount(),
        "sys_executable": sys_executable,
        "sys_prefix": sys_prefix,
        "sys_base_prefix": sys_base_prefix,
        "sys_exec_prefix": sys_exec_prefix,
        "sys_base_exec_prefix": sys_base_exec_prefix,
        "nuitka_version_major": major,
        "nuitka_version_minor": minor,
        "nuitka_version_micro": micro,
        "nuitka_version_level": level,
    }

    return header, body
