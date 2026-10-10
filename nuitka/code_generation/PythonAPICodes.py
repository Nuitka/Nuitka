#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for standard CPython/API calls.

This is generic stuff, geared at calling functions that accept Python objects
and return Python objects. As these all work in a similar way, it makes sense
to concentrate the best way to do to make those calls here.

Also, many Nuitka helper codes turn out to be very similar to Python C/API
and then can use the same code.
"""

from .CodeHelpers import generateExpressionCode
from .ErrorCodes import getErrorExitCode, getReleaseCode


def makeArgDescFromExpression(expression):
    """Helper for providing arg_desc consistently for generateCAPIObject methods."""

    if hasattr(expression, "named_children"):
        result = []

        for child_desc in expression.named_children:
            if "|" in child_desc:
                child_name = child_desc.split("|")[0]
            else:
                child_name = child_desc

            result.append(
                (child_name + "_value", getattr(expression, "subnode_" + child_name))
            )

        return tuple(result)

    return tuple(
        (child_name + "_value", child_value)
        for child_name, child_value in expression.getVisitableNodesNamed()
    )


def generateCAPIObjectCodeCommon(
    to_name,
    capi,
    tstate,
    arg_desc,
    may_raise,
    conversion_check,
    ref_count,
    source_ref,
    emit,
    context,
    none_null=False,
):
    """Generate C code for calling a C-API object creation function.

    Args:
        to_name: The variable name to assign the result to.
        capi: The C function name to call.
        tstate: Whether to pass the thread state as the first argument.
        arg_desc: Tuple of (arg_name, expression) for arguments.
        may_raise: Whether the call may raise an exception.
        conversion_check: Check to decide if a conversion is needed.
        ref_count: The reference count of the returned object (usually 1 or 0 for borrowed return value).
        source_ref: Source code reference.
        emit: Function to emit generated code.
        context: Context object for code generation.
        none_null: If True, all arguments with None expression are passed as NULL and acceptable.
                   If set/tuple/list, only argument names present in it are passed as NULL and acceptable.
    """
    # Complex code due to the need to handle tuple arguments.
    # pylint: disable=too-many-locals

    arg_names = []
    release_names = []

    if tstate:
        arg_names.append("tstate")

    for arg_name, arg_expression in arg_desc:
        if arg_expression is None:
            if none_null is True or (none_null and arg_name in none_null):
                arg_names.append("NULL")
            else:
                raise ValueError("None expression not allowed for %s" % arg_name)
        elif type(arg_expression) is tuple:
            sub_names = []

            for sub_index, sub_expression in enumerate(arg_expression):
                sub_name = context.allocateTempName(
                    arg_name + "_element_%d" % sub_index
                )

                generateExpressionCode(
                    to_name=sub_name,
                    expression=sub_expression,
                    emit=emit,
                    context=context,
                )

                sub_names.append(sub_name)

            if sub_names:
                arg_name = "tmp_%s_array_%d" % (
                    arg_name,
                    context.allocateTempNumber(arg_name),
                )

                emit(
                    "PyObject *%s[] = {%s};"
                    % (arg_name, ", ".join(str(name) for name in sub_names))
                )
                arg_names.append(arg_name)
                arg_names.append(str(len(sub_names)))
                release_names.extend(sub_names)
            else:
                arg_names.append("NULL")
                arg_names.append("0")

        else:
            arg_name = context.allocateTempName(arg_name)

            generateExpressionCode(
                to_name=arg_name,
                expression=arg_expression,
                emit=emit,
                context=context,
            )

            arg_names.append(arg_name)
            release_names.append(arg_name)

    context.setCurrentSourceCodeReference(source_ref)

    getCAPIObjectCode(
        to_name=to_name,
        capi=capi,
        arg_names=arg_names,
        may_raise=may_raise,
        conversion_check=conversion_check,
        ref_count=ref_count,
        release_names=release_names,
        emit=emit,
        context=context,
    )


def generateCAPIObjectCode(
    to_name,
    capi,
    tstate,
    arg_desc,
    may_raise,
    conversion_check,
    source_ref,
    emit,
    context,
    none_null=False,
):
    """See generateCAPIObjectCodeCommon, changes ref_count to 1."""
    generateCAPIObjectCodeCommon(
        to_name=to_name,
        capi=capi,
        tstate=tstate,
        arg_desc=arg_desc,
        may_raise=may_raise,
        conversion_check=conversion_check,
        ref_count=1,
        source_ref=source_ref,
        emit=emit,
        context=context,
        none_null=none_null,
    )


def generateCAPIObjectCode0(
    to_name,
    capi,
    tstate,
    arg_desc,
    may_raise,
    conversion_check,
    source_ref,
    emit,
    context,
    none_null=False,
):
    """See generateCAPIObjectCodeCommon, changes ref_count to 0."""
    generateCAPIObjectCodeCommon(
        to_name=to_name,
        capi=capi,
        tstate=tstate,
        arg_desc=arg_desc,
        may_raise=may_raise,
        conversion_check=conversion_check,
        ref_count=0,
        source_ref=source_ref,
        emit=emit,
        context=context,
        none_null=none_null,
    )


def getCAPIObjectCode(
    to_name,
    capi,
    arg_names,
    may_raise,
    conversion_check,
    ref_count,
    release_names,
    emit,
    context,
):
    if to_name is not None:
        # TODO: Use context manager here too.
        if to_name.c_type == "PyObject *":
            value_name = to_name
        else:
            value_name = context.allocateTempName("capi_result")

        emit(
            "%s = %s(%s);"
            % (value_name, capi, ", ".join(str(arg_name) for arg_name in arg_names))
        )

        getErrorExitCode(
            check_name=value_name,
            release_names=release_names,
            needs_check=may_raise,
            emit=emit,
            context=context,
        )

        if ref_count:
            context.addCleanupTempName(value_name)

        if to_name is not value_name:
            to_name.getCType().emitAssignConversionCode(
                to_name=to_name,
                value_name=value_name,
                needs_check=conversion_check,
                emit=emit,
                context=context,
            )

            if ref_count:
                getReleaseCode(value_name, emit, context)
    else:
        assert not may_raise, capi
        assert not ref_count

        emit("%s(%s);" % (capi, ", ".join(str(arg_name) for arg_name in arg_names)))

        getReleaseCode(release_names, emit, context)


def getReferenceExportCode(base_name, emit, context):
    if not context.needsCleanup(base_name):
        emit("Py_INCREF(%s);" % base_name)


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
