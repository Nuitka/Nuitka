#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
from nuitka.Constants import isNumberConstant
from nuitka.PythonVersions import python_version

from .CodeHelpers import (
    generateChildExpressionsCode,
    generateExpressionCode,
    generateExpressionsCode
)
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes
)
from .IndexCodes import (
    getIndexCode,
    getIndexValueCode,
    getMaxIndexCode,
    getMinIndexCode
)


def generateSliceRangeIdentifier(lower, upper, scope, emit, context):
    lower_name = context.allocateTempName(
        scope + "slicedel_index_lower",
        "Py_ssize_t"
    )
    upper_name = context.allocateTempName(
        scope + "_index_upper",
        "Py_ssize_t"
    )

    def isSmallNumberConstant(node):
        value = node.getConstant()

        if isNumberConstant(value):
            return abs(int(value)) < 2**63-1
        else:
            return False

    if lower is None:
        getMinIndexCode(
            to_name = lower_name,
            emit    = emit
        )
    elif lower.isExpressionConstantRef() and isSmallNumberConstant(lower):
        getIndexValueCode(
            to_name = lower_name,
            value   = int(lower.getConstant()),
            emit    = emit
        )
    else:
        value_name = context.allocateTempName(scope + "_lower_index_value")

        generateExpressionCode(
            to_name    = value_name,
            expression = lower,
            emit       = emit,
            context    = context
        )

        getIndexCode(
            to_name    = lower_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )

    if upper is None:
        getMaxIndexCode(
            to_name = upper_name,
            emit    = emit
        )
    elif upper.isExpressionConstantRef() and isSmallNumberConstant(upper):
        getIndexValueCode(
            to_name = upper_name,
            value   = int(upper.getConstant()),
            emit    = emit
        )
    else:
        value_name = context.allocateTempName(scope + "_upper_index_value")

        generateExpressionCode(
            to_name    = value_name,
            expression = upper,
            emit       = emit,
            context    = context
        )

        getIndexCode(
            to_name    = upper_name,
            value_name = value_name,
            emit       = emit,
            context    = context
        )

    return lower_name, upper_name

def _decideSlicing(lower, upper):
    return (lower is None or lower.isIndexable()) and \
           (upper is None or upper.isIndexable())


def generateSliceLookupCode(to_name, expression, emit, context):
    assert python_version < 300

    lower = expression.getLower()
    upper = expression.getUpper()

    if _decideSlicing(lower, upper):
        lower_name, upper_name = generateSliceRangeIdentifier(
            lower   = lower,
            upper   = upper,
            scope   = "slice",
            emit    = emit,
            context = context
        )

        source_name = context.allocateTempName("slice_source")

        generateExpressionCode(
            to_name    = source_name,
            expression = expression.getLookupSource(),
            emit       = emit,
            context    = context
        )

        getSliceLookupIndexesCode(
            to_name     = to_name,
            source_name = source_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )
    else:
        source_name, lower_name, upper_name = generateExpressionsCode(
            names       = ("slice_source", "slice_lower", "slice_upper"),
            expressions = (
                expression.getLookupSource(),
                expression.getLower(),
                expression.getUpper()
            ),
            emit        = emit,
            context     = context
        )

        getSliceLookupCode(
            to_name     = to_name,
            source_name = source_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )


def generateAssignmentSliceCode(statement, emit, context):
    assert python_version < 300

    lookup_source = statement.getLookupSource()
    lower         = statement.getLower()
    upper         = statement.getUpper()
    value         = statement.getAssignSource()

    value_name = context.allocateTempName("sliceass_value")

    generateExpressionCode(
        to_name    = value_name,
        expression = value,
        emit       = emit,
        context    = context
    )

    target_name = context.allocateTempName("sliceass_target")

    generateExpressionCode(
        to_name    = target_name,
        expression = lookup_source,
        emit       = emit,
        context    = context
    )


    if _decideSlicing(lower, upper):
        lower_name, upper_name = generateSliceRangeIdentifier(
            lower   = lower,
            upper   = upper,
            scope   = "sliceass",
            emit    = emit,
            context = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            value.getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        getSliceAssignmentIndexesCode(
            target_name = target_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        lower_name, upper_name = generateExpressionsCode(
            names       = (
                "sliceass_lower", "sliceass_upper"
            ),
            expressions = (
                lower,
                upper
            ),
            emit        = emit,
            context     = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            value.getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        getSliceAssignmentCode(
            target_name = target_name,
            upper_name  = upper_name,
            lower_name  = lower_name,
            value_name  = value_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)


def generateDelSliceCode(statement, emit, context):
    assert python_version < 300

    target  = statement.getLookupSource()
    lower   = statement.getLower()
    upper   = statement.getUpper()

    target_name = context.allocateTempName("slicedel_target")

    generateExpressionCode(
        to_name    = target_name,
        expression = target,
        emit       = emit,
        context    = context
    )

    if _decideSlicing(lower, upper):
        lower_name, upper_name = generateSliceRangeIdentifier(
            lower   = lower,
            upper   = upper,
            scope   = "slicedel",
            emit    = emit,
            context = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            (upper or lower or statement).getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        getSliceDelIndexesCode(
            target_name = target_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)
    else:
        lower_name, upper_name = generateExpressionsCode(
            names       = (
                "slicedel_lower", "slicedel_upper"
            ),
            expressions = (
                lower,
                upper
            ),
            emit        = emit,
            context     = context
        )

        old_source_ref = context.setCurrentSourceCodeReference(
            (upper or lower or target).getSourceReference()
               if Options.isFullCompat() else
            statement.getSourceReference()
        )

        getSliceDelCode(
            target_name = target_name,
            lower_name  = lower_name,
            upper_name  = upper_name,
            emit        = emit,
            context     = context
        )

        context.setCurrentSourceCodeReference(old_source_ref)





def generateBuiltinSliceCode(to_name, expression, emit, context):
    lower_name, upper_name, step_name = generateChildExpressionsCode(
        expression = expression,
        emit       = emit,
        context    = context
    )

    emit(
        "%s = MAKE_SLICEOBJ3( %s, %s, %s );" % (
            to_name,
            lower_name if lower_name is not None else "Py_None",
            upper_name if upper_name is not None else "Py_None",
            step_name if step_name is not None else "Py_None",
        )
    )

    getReleaseCodes(
        release_names = (lower_name, upper_name, step_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name  = to_name,
        needs_check = False, # Note: Cannot fail
        emit        = emit,
        context     = context
    )


    context.addCleanupTempName(to_name)


def getSliceLookupCode(to_name, source_name, lower_name, upper_name, emit,
                       context):
    emit(
        "%s = LOOKUP_SLICE( %s, %s, %s );" % (
            to_name,
            source_name,
            lower_name if lower_name is not None else "Py_None",
            upper_name if upper_name is not None else "Py_None"
        )
    )

    getReleaseCodes(
        release_names = (source_name, lower_name, upper_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getSliceLookupIndexesCode(to_name, lower_name, upper_name, source_name,
                              emit, context):
    emit(
        "%s = LOOKUP_INDEX_SLICE( %s, %s, %s );" % (
            to_name,
            source_name,
            lower_name,
            upper_name,
        )
    )

    getReleaseCode(
        release_name = source_name,
        emit         = emit,
        context      = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)




def getSliceAssignmentIndexesCode(target_name, lower_name, upper_name,
                                  value_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = SET_INDEX_SLICE( %s, %s, %s, %s );" % (
            res_name,
            target_name,
            lower_name,
            upper_name,
            value_name
        )
    )

    getReleaseCodes(
        release_names = (value_name, target_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )


def getSliceAssignmentCode(target_name, lower_name, upper_name, value_name,
                           emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = SET_SLICE( %s, %s, %s, %s );" % (
            res_name,
            target_name,
            lower_name if lower_name is not None else "Py_None",
            upper_name if upper_name is not None else "Py_None",
            value_name
        )
    )

    getReleaseCodes(
        release_names = (target_name, lower_name, upper_name, value_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )


def getSliceDelIndexesCode(target_name, lower_name, upper_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = DEL_INDEX_SLICE( %s, %s, %s );" % (
            res_name,
            target_name,
            lower_name,
            upper_name
        )
    )

    getReleaseCode(
        release_name = target_name,
        emit         = emit,
        context      = context
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )


def getSliceDelCode(target_name, lower_name, upper_name, emit, context):
    res_name = context.getBoolResName()

    emit(
        "%s = DEL_SLICE( %s, %s, %s );" % (
            res_name,
            target_name,
            lower_name if lower_name is not None else "Py_None",
            upper_name if upper_name is not None else "Py_None"
        )
    )

    getReleaseCodes(
        release_names = (target_name, lower_name, upper_name),
        emit          = emit,
        context       = context
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )
