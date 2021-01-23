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
""" Code generation for slicing.

This is about slice lookups, assignments, and deletions. There is also a
special case, for using index values instead of objects. The slice objects
are also created here, and can be used for indexing.
"""

from nuitka import Options
from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    generateChildExpressionsCode,
    generateExpressionCode,
    generateExpressionsCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getErrorExitCode
from .IndexCodes import (
    getIndexCode,
    getIndexValueCode,
    getMaxIndexCode,
    getMinIndexCode,
)


def _isSmallNumberConstant(node):
    if node.isNumberConstant():
        value = node.getCompileTimeConstant()
        return abs(int(value)) < 2 ** 63 - 1
    else:
        return False


def _generateSliceRangeIdentifier(lower, upper, scope, emit, context):
    lower_name = context.allocateTempName(scope + "slicedel_index_lower", "Py_ssize_t")
    upper_name = context.allocateTempName(scope + "_index_upper", "Py_ssize_t")

    if lower is None:
        getMinIndexCode(to_name=lower_name, emit=emit)
    elif lower.isExpressionConstantRef() and _isSmallNumberConstant(lower):
        getIndexValueCode(
            to_name=lower_name, value=int(lower.getCompileTimeConstant()), emit=emit
        )
    else:
        value_name = context.allocateTempName(scope + "_lower_index_value")

        generateExpressionCode(
            to_name=value_name, expression=lower, emit=emit, context=context
        )

        getIndexCode(
            to_name=lower_name, value_name=value_name, emit=emit, context=context
        )

    if upper is None:
        getMaxIndexCode(to_name=upper_name, emit=emit)
    elif upper.isExpressionConstantRef() and _isSmallNumberConstant(upper):
        getIndexValueCode(
            to_name=upper_name, value=int(upper.getCompileTimeConstant()), emit=emit
        )
    else:
        value_name = context.allocateTempName(scope + "_upper_index_value")

        generateExpressionCode(
            to_name=value_name, expression=upper, emit=emit, context=context
        )

        getIndexCode(
            to_name=upper_name, value_name=value_name, emit=emit, context=context
        )

    return lower_name, upper_name


def _decideSlicing(lower, upper):
    return (lower is None or lower.isIndexable()) and (
        upper is None or upper.isIndexable()
    )


def generateSliceLookupCode(to_name, expression, emit, context):
    assert python_version < 0x300

    lower = expression.subnode_lower
    upper = expression.subnode_upper

    if _decideSlicing(lower, upper):
        lower_name, upper_name = _generateSliceRangeIdentifier(
            lower=lower, upper=upper, scope="slice", emit=emit, context=context
        )

        source_name = context.allocateTempName("slice_source")

        generateExpressionCode(
            to_name=source_name,
            expression=expression.subnode_expression,
            emit=emit,
            context=context,
        )

        with withObjectCodeTemporaryAssignment(
            to_name, "slice_result", expression, emit, context
        ) as result_name:

            _getSliceLookupIndexesCode(
                to_name=result_name,
                source_name=source_name,
                lower_name=lower_name,
                upper_name=upper_name,
                emit=emit,
                context=context,
            )
    else:
        source_name, lower_name, upper_name = generateExpressionsCode(
            names=("slice_source", "slice_lower", "slice_upper"),
            expressions=(
                expression.subnode_expression,
                expression.subnode_lower,
                expression.subnode_upper,
            ),
            emit=emit,
            context=context,
        )

        with withObjectCodeTemporaryAssignment(
            to_name, "slice_result", expression, emit, context
        ) as result_name:
            _getSliceLookupCode(
                to_name=result_name,
                source_name=source_name,
                lower_name=lower_name,
                upper_name=upper_name,
                emit=emit,
                context=context,
            )


def generateAssignmentSliceCode(statement, emit, context):
    assert python_version < 0x300

    lookup_source = statement.subnode_expression
    lower = statement.subnode_lower
    upper = statement.subnode_upper
    value = statement.subnode_source

    value_name = context.allocateTempName("sliceass_value")

    generateExpressionCode(
        to_name=value_name, expression=value, emit=emit, context=context
    )

    target_name = context.allocateTempName("sliceass_target")

    generateExpressionCode(
        to_name=target_name, expression=lookup_source, emit=emit, context=context
    )

    if _decideSlicing(lower, upper):
        lower_name, upper_name = _generateSliceRangeIdentifier(
            lower=lower, upper=upper, scope="sliceass", emit=emit, context=context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            value.getSourceReference()
            if Options.is_fullcompat
            else statement.getSourceReference()
        )

        _getSliceAssignmentIndexesCode(
            target_name=target_name,
            lower_name=lower_name,
            upper_name=upper_name,
            value_name=value_name,
            emit=emit,
            context=context,
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        lower_name, upper_name = generateExpressionsCode(
            names=("sliceass_lower", "sliceass_upper"),
            expressions=(lower, upper),
            emit=emit,
            context=context,
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            value.getSourceReference()
            if Options.is_fullcompat
            else statement.getSourceReference()
        )

        _getSliceAssignmentCode(
            target_name=target_name,
            upper_name=upper_name,
            lower_name=lower_name,
            value_name=value_name,
            emit=emit,
            context=context,
        )

        context.setCurrentSourceCodeReference(old_source_ref)


def generateDelSliceCode(statement, emit, context):
    assert python_version < 0x300

    target = statement.subnode_expression
    lower = statement.subnode_lower
    upper = statement.subnode_upper

    target_name = context.allocateTempName("slicedel_target")

    generateExpressionCode(
        to_name=target_name, expression=target, emit=emit, context=context
    )

    if _decideSlicing(lower, upper):
        lower_name, upper_name = _generateSliceRangeIdentifier(
            lower=lower, upper=upper, scope="slicedel", emit=emit, context=context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            (upper or lower or statement).getSourceReference()
            if Options.is_fullcompat
            else statement.getSourceReference()
        )

        _getSliceDelIndexesCode(
            target_name=target_name,
            lower_name=lower_name,
            upper_name=upper_name,
            emit=emit,
            context=context,
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        lower_name, upper_name = generateExpressionsCode(
            names=("slicedel_lower", "slicedel_upper"),
            expressions=(lower, upper),
            emit=emit,
            context=context,
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            (upper or lower or target).getSourceReference()
            if Options.is_fullcompat
            else statement.getSourceReference()
        )

        _getSliceDelCode(
            target_name=target_name,
            lower_name=lower_name,
            upper_name=upper_name,
            emit=emit,
            context=context,
        )

        context.setCurrentSourceCodeReference(old_source_ref)


def generateBuiltinSlice3Code(to_name, expression, emit, context):
    lower_name, upper_name, step_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "sliceobj_value", expression, emit, context
    ) as result_name:
        emit(
            "%s = MAKE_SLICEOBJ3(%s, %s, %s);"
            % (
                result_name,
                lower_name if lower_name is not None else "Py_None",
                upper_name if upper_name is not None else "Py_None",
                step_name if step_name is not None else "Py_None",
            )
        )

        getErrorExitCode(
            check_name=result_name,
            release_names=(lower_name, upper_name, step_name),
            needs_check=False,  # Note: Cannot fail
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateBuiltinSlice2Code(to_name, expression, emit, context):
    lower_name, upper_name = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "sliceobj_value", expression, emit, context
    ) as result_name:
        emit(
            "%s = MAKE_SLICEOBJ2(%s, %s);"
            % (
                result_name,
                lower_name if lower_name is not None else "Py_None",
                upper_name if upper_name is not None else "Py_None",
            )
        )

        getErrorExitCode(
            check_name=result_name,
            release_names=(lower_name, upper_name),
            needs_check=False,  # Note: Cannot fail
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def generateBuiltinSlice1Code(to_name, expression, emit, context):
    (upper_name,) = generateChildExpressionsCode(
        expression=expression, emit=emit, context=context
    )

    with withObjectCodeTemporaryAssignment(
        to_name, "sliceobj_value", expression, emit, context
    ) as result_name:
        emit(
            "%s = MAKE_SLICEOBJ1(%s);"
            % (
                result_name,
                upper_name if upper_name is not None else "Py_None",
            )
        )

        getErrorExitCode(
            check_name=result_name,
            release_name=upper_name,
            needs_check=False,  # Note: Cannot fail
            emit=emit,
            context=context,
        )

        context.addCleanupTempName(result_name)


def _getSliceLookupCode(to_name, source_name, lower_name, upper_name, emit, context):
    emit(
        "%s = LOOKUP_SLICE(%s, %s, %s);"
        % (
            to_name,
            source_name,
            lower_name if lower_name is not None else "Py_None",
            upper_name if upper_name is not None else "Py_None",
        )
    )

    getErrorExitCode(
        check_name=to_name,
        release_names=(source_name, lower_name, upper_name),
        emit=emit,
        context=context,
    )

    context.addCleanupTempName(to_name)


def _getSliceLookupIndexesCode(
    to_name, lower_name, upper_name, source_name, emit, context
):
    emit(
        "%s = LOOKUP_INDEX_SLICE(%s, %s, %s);"
        % (to_name, source_name, lower_name, upper_name)
    )

    getErrorExitCode(
        check_name=to_name, release_name=source_name, emit=emit, context=context
    )

    context.addCleanupTempName(to_name)


def _getSliceAssignmentIndexesCode(
    target_name, lower_name, upper_name, value_name, emit, context
):
    res_name = context.getBoolResName()

    emit(
        "%s = SET_INDEX_SLICE(%s, %s, %s, %s);"
        % (res_name, target_name, lower_name, upper_name, value_name)
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(value_name, target_name),
        emit=emit,
        context=context,
    )


def _getSliceAssignmentCode(
    target_name, lower_name, upper_name, value_name, emit, context
):
    res_name = context.getBoolResName()

    emit(
        "%s = SET_SLICE(%s, %s, %s, %s);"
        % (
            res_name,
            target_name,
            lower_name if lower_name is not None else "Py_None",
            upper_name if upper_name is not None else "Py_None",
            value_name,
        )
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(target_name, lower_name, upper_name, value_name),
        emit=emit,
        context=context,
    )


def _getSliceDelIndexesCode(target_name, lower_name, upper_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = DEL_INDEX_SLICE(%s, %s, %s);"
        % (res_name, target_name, lower_name, upper_name)
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_name=target_name,
        emit=emit,
        context=context,
    )


def _getSliceDelCode(target_name, lower_name, upper_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = DEL_SLICE(%s, %s, %s);"
        % (
            res_name,
            target_name,
            lower_name if lower_name is not None else "Py_None",
            upper_name if upper_name is not None else "Py_None",
        )
    )

    getErrorExitBoolCode(
        condition="%s == false" % res_name,
        release_names=(target_name, lower_name, upper_name),
        emit=emit,
        context=context,
    )
