#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code generation for type alias statement helpers."""

from .CodeHelpers import decideConversionCheckNeeded
from .PythonAPICodes import (
    ConstantArg,
    TupleArg,
    generateCAPIObjectCode,
    makeArgDescFromExpression,
)


def generateTypeAliasCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_TYPE_ALIAS",
        tstate=False,
        arg_desc=(
            ConstantArg(expression.subnode_name.getCompileTimeConstant()),
            TupleArg("type_params_value", expression.subnode_type_params),
            ("value_value", expression.subnode_value),
            ConstantArg(context.getModuleName().asString()),
        ),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateTypeVarCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_TYPE_VAR",
        tstate=True,
        arg_desc=(ConstantArg(expression.name),)
        + makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        none_null=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateTypeVarTupleCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_TYPE_VAR_TUPLE",
        tstate=True,
        arg_desc=(ConstantArg(expression.name),)
        + makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        none_null=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateParamSpecCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_PARAM_SPEC",
        tstate=True,
        arg_desc=(ConstantArg(expression.name),)
        + makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        none_null=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def generateTypeGenericCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="MAKE_TYPE_GENERIC",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        source_ref=expression.getCompatibleSourceReference(),
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
