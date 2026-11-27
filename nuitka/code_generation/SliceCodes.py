#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for slicing and slice objects."""

from nuitka.PythonVersions import python_version
from nuitka.States import states

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateExpressionCode,
    generateExpressionsCode,
)
from .IndexCodes import (
    getIndexCode,
    getIndexValueCode,
    getMaxIndexCode,
    getMinIndexCode,
)
from .PythonAPICodes import (
    OptionalArg,
    generateCAPIObjectCode,
    getCAPIErrorCode,
    getCAPIObjectCode,
    makeArgDescFromExpression,
)


def _generateSliceRangeIdentifier(lower, upper, scope, emit, context):
    lower_name = context.allocateTempName(scope + "slicedel_index_lower", "Py_ssize_t")
    upper_name = context.allocateTempName(scope + "_index_upper", "Py_ssize_t")

    if lower is None or lower.isExpressionConstantNoneRef():
        getMinIndexCode(to_name=lower_name, emit=emit)
    elif lower.isExpressionIntegerSubscript():
        getIndexValueCode(to_name=lower_name, value=lower.getIndexValue(), emit=emit)
    else:
        value_name = context.allocateTempName(scope + "_lower_index_value")

        generateExpressionCode(
            to_name=value_name, expression=lower, emit=emit, context=context
        )

        getIndexCode(
            to_name=lower_name, value_name=value_name, emit=emit, context=context
        )

    if upper is None or upper.isExpressionConstantNoneRef():
        getMaxIndexCode(to_name=upper_name, emit=emit)
    elif upper.isExpressionIntegerSubscript():
        getIndexValueCode(to_name=upper_name, value=upper.getIndexValue(), emit=emit)
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
    return (lower is None or lower.isKnownToBeValidIndex()) and (
        upper is None or upper.isKnownToBeValidIndex()
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

        getCAPIObjectCode(
            to_name=to_name,
            capi="LOOKUP_INDEX_SLICE",
            arg_names=(source_name, lower_name, upper_name),
            may_raise=expression.mayRaiseExceptionOperation(),
            conversion_check=decideConversionCheckNeeded(to_name, expression),
            ref_count=1,
            release_names=(source_name,),
            emit=emit,
            context=context,
        )
    else:
        generateCAPIObjectCode(
            to_name=to_name,
            capi="LOOKUP_SLICE",
            tstate=True,
            arg_desc=(
                ("slice_source", expression.subnode_expression),
                OptionalArg("slice_lower", expression.subnode_lower, "Py_None"),
                OptionalArg("slice_upper", expression.subnode_upper, "Py_None"),
            ),
            may_raise=expression.mayRaiseExceptionOperation(),
            conversion_check=decideConversionCheckNeeded(to_name, expression),
            source_ref=expression.getCompatibleSourceReference(),
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

        with context.withCurrentSourceCodeReference(
            value.getSourceReference()
            if states.is_full_compat
            else statement.getSourceReference()
        ):
            _getSliceAssignmentIndexesCode(
                target_name=target_name,
                lower_name=lower_name,
                upper_name=upper_name,
                value_name=value_name,
                emit=emit,
                context=context,
            )
    else:
        lower_name, upper_name = generateExpressionsCode(
            names=("sliceass_lower", "sliceass_upper"),
            expressions=(lower, upper),
            emit=emit,
            context=context,
        )

        with context.withCurrentSourceCodeReference(
            value.getSourceReference()
            if states.is_full_compat
            else statement.getSourceReference()
        ):
            _getSliceAssignmentCode(
                target_name=target_name,
                upper_name=upper_name,
                lower_name=lower_name,
                value_name=value_name,
                emit=emit,
                context=context,
            )


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

        with context.withCurrentSourceCodeReference(
            (upper or lower or statement).getSourceReference()
            if states.is_full_compat
            else statement.getSourceReference()
        ):
            _getSliceDelIndexesCode(
                target_name=target_name,
                lower_name=lower_name,
                upper_name=upper_name,
                emit=emit,
                context=context,
            )
    else:
        lower_name, upper_name = generateExpressionsCode(
            names=("slicedel_lower", "slicedel_upper"),
            expressions=(lower, upper),
            emit=emit,
            context=context,
        )

        with context.withCurrentSourceCodeReference(
            (upper or lower or target).getSourceReference()
            if states.is_full_compat
            else statement.getSourceReference()
        ):
            _getSliceDelCode(
                target_name=target_name,
                lower_name=lower_name,
                upper_name=upper_name,
                emit=emit,
                context=context,
            )


def generateBuiltinSlice3Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_SLICE_OBJECT3",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinSlice2Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_SLICE_OBJECT2",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateBuiltinSlice1Code(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_SLICE_OBJECT1",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def _getSliceAssignmentIndexesCode(
    target_name, lower_name, upper_name, value_name, emit, context
):
    getCAPIErrorCode(
        capi="SET_INDEX_SLICE",
        arg_names=(target_name, lower_name, upper_name, value_name),
        may_raise=True,
        release_names=(value_name, target_name),
        emit=emit,
        context=context,
    )


def _getSliceAssignmentCode(
    target_name, lower_name, upper_name, value_name, emit, context
):
    getCAPIErrorCode(
        capi="SET_SLICE",
        arg_names=(
            "tstate",
            target_name,
            lower_name if lower_name is not None else "Py_None",
            upper_name if upper_name is not None else "Py_None",
            value_name,
        ),
        may_raise=True,
        release_names=(target_name, lower_name, upper_name, value_name),
        emit=emit,
        context=context,
    )


def _getSliceDelIndexesCode(target_name, lower_name, upper_name, emit, context):
    getCAPIErrorCode(
        capi="DEL_INDEX_SLICE",
        arg_names=(target_name, lower_name, upper_name),
        may_raise=True,
        release_names=(target_name,),
        emit=emit,
        context=context,
    )


def _getSliceDelCode(target_name, lower_name, upper_name, emit, context):
    getCAPIErrorCode(
        capi="DEL_SLICE",
        arg_names=(
            "tstate",
            target_name,
            lower_name if lower_name is not None else "Py_None",
            upper_name if upper_name is not None else "Py_None",
        ),
        may_raise=True,
        release_names=(target_name, lower_name, upper_name),
        emit=emit,
        context=context,
    )


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
