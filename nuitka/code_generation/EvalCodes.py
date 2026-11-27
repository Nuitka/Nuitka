#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Eval/exec/execfile/compile built-in related codes."""

from nuitka.PythonVersions import python_version
from nuitka.States import states

from .CodeHelpers import (
    decideConversionCheckNeeded,
    generateExpressionCode,
    withObjectCodeTemporaryAssignment,
)
from .ErrorCodes import getErrorExitBoolCode, getReleaseCode
from .PythonAPICodes import (
    generateCAPIObjectCode,
    getCAPIObjectCode,
    getReferenceExportCode,
    makeArgDescFromExpression,
)
from .VariableCodes import getVariableAssignmentCode


def _getStoreLocalsCode(locals_name, variable_traces, is_dict, emit, context):
    for variable, variable_trace in sorted(
        variable_traces, key=lambda x: x[0].getName()
    ):
        if not variable.isModuleVariable():
            key_name = context.getConstantCode(constant=variable.getName())

            value_name = context.allocateTempName("locals_value", unique=True)

            if is_dict:
                emit(
                    "%s = DICT_GET_ITEM0(tstate, %s, %s);"
                    % (value_name, locals_name, key_name)
                )
            else:
                emit(
                    "%s = LOOKUP_SUBSCRIPT(tstate, %s, %s);"
                    % (value_name, locals_name, key_name)
                )

                getErrorExitBoolCode(
                    condition="""\
%s == NULL && !EXCEPTION_MATCH_BOOL_SINGLE(tstate, GET_ERROR_OCCURRED(tstate), PyExc_KeyError)"""
                    % value_name,
                    emit=emit,
                    context=context,
                )

                emit("CLEAR_ERROR_OCCURRED(tstate);")

                context.addCleanupTempName(value_name)

            emit("if (%s != NULL)" % value_name)
            emit("{")

            getVariableAssignmentCode(
                variable=variable,
                variable_trace=variable_trace,
                tmp_name=value_name,
                needs_release=None,  # TODO: Could be known maybe.
                inplace=False,
                emit=emit,
                context=context,
            )

            emit("}")


def generateBuiltinCompileCode(to_name, expression, emit, context):
    generateCAPIObjectCode(
        to_name=to_name,
        capi="COMPILE_CODE",
        tstate=True,
        arg_desc=makeArgDescFromExpression(expression),
        may_raise=expression.mayRaiseExceptionOperation(),
        conversion_check=decideConversionCheckNeeded(to_name, expression),
        none_null=True,
        source_ref=expression.getCompatibleSourceReference(),
        emit=emit,
        context=context,
    )


def _getBuiltinCompileCode(
    to_name,
    source_name,
    filename_name,
    mode_name,
    flags_name,
    dont_inherit_name,
    optimize_name,
    for_exec,
    emit,
    context,
):
    if python_version < 0x300:
        args = (
            "tstate",
            source_name,
            filename_name,
            mode_name,
            flags_name,
            dont_inherit_name,
        )
    else:
        args = (
            "tstate",
            source_name,
            filename_name,
            mode_name,
            flags_name,
            dont_inherit_name,
            optimize_name,
        )

    getCAPIObjectCode(
        to_name=to_name,
        capi="COMPILE_CODE_EXEC" if for_exec else "COMPILE_CODE",
        arg_names=args,
        may_raise=True,
        conversion_check=False,
        ref_count=1,
        release_names=(
            source_name,
            filename_name,
            mode_name,
            flags_name,
            dont_inherit_name,
            optimize_name,
        ),
        emit=emit,
        context=context,
    )


def getBuiltinEvalCode(
    to_name,
    source_name,
    filename_name,
    globals_name,
    locals_name,
    mode_name,
    closure_name,
    for_exec,
    emit,
    context,
):
    compiled_name = context.allocateTempName("eval_compiled")

    _getBuiltinCompileCode(
        to_name=compiled_name,
        source_name=source_name,
        filename_name=filename_name,
        mode_name=mode_name,
        flags_name="NULL",
        dont_inherit_name="NULL",
        optimize_name="NULL",
        for_exec=for_exec,
        emit=emit,
        context=context,
    )

    getCAPIObjectCode(
        to_name=to_name,
        capi="EVAL_CODE",
        arg_names=(
            "tstate",
            compiled_name,
            globals_name,
            locals_name,
            closure_name or "NULL",
        ),
        may_raise=True,
        conversion_check=False,
        ref_count=1,
        release_names=(compiled_name, globals_name, locals_name, closure_name),
        emit=emit,
        context=context,
    )


def generateExecCode(statement, emit, context):
    source_arg = statement.subnode_source_code
    globals_arg = statement.subnode_globals_arg
    locals_arg = statement.subnode_locals_arg

    source_name = context.allocateTempName("exec_source")
    globals_name = context.allocateTempName("exec_globals")
    locals_name = context.allocateTempName("exec_locals")

    generateExpressionCode(
        to_name=source_name, expression=source_arg, emit=emit, context=context
    )

    generateExpressionCode(
        to_name=globals_name, expression=globals_arg, emit=emit, context=context
    )

    generateExpressionCode(
        to_name=locals_name, expression=locals_arg, emit=emit, context=context
    )

    source_ref = statement.getSourceReference()

    filename_name = context.allocateTempName("exec_filename")

    # Default filename with origin in improved mode.
    filename_name.getCType().emitAssignmentCodeFromConstant(
        to_name=filename_name,
        constant=(
            "<string>"
            if states.is_full_compat
            else "<string at %s>" % source_ref.getAsString()
        ),
        may_escape=False,
        emit=emit,
        context=context,
    )

    getReferenceExportCode(filename_name, emit, context)
    context.addCleanupTempName(filename_name)

    getReferenceExportCode(source_name, emit, context)
    context.addCleanupTempName(source_name)

    with context.withCurrentSourceCodeReference(
        locals_arg.getSourceReference()
        if states.is_full_compat
        else statement.getSourceReference()
    ):
        res_name = context.getBoolResName()

        emit(
            "%s = EXEC_FILE_ARG_HANDLING(tstate, &%s, &%s);"
            % (res_name, source_name, filename_name)
        )

        getErrorExitBoolCode(
            condition="%s == false" % res_name, emit=emit, context=context
        )

        compiled_name = context.allocateTempName("exec_compiled")

        _getBuiltinCompileCode(
            to_name=compiled_name,
            source_name=source_name,
            filename_name=filename_name,
            mode_name=context.getConstantCode(constant="exec"),
            flags_name="NULL",
            dont_inherit_name="NULL",
            optimize_name="NULL",
            for_exec=True,
            emit=emit,
            context=context,
        )

        to_name = context.allocateTempName("exec_result")

        getCAPIObjectCode(
            to_name=to_name,
            capi="EVAL_CODE",
            arg_names=("tstate", compiled_name, globals_name, locals_name, "NULL"),
            may_raise=True,
            conversion_check=False,
            ref_count=1,
            release_names=(
                compiled_name,
                globals_name,
                locals_name,
                source_name,
                filename_name,
            ),
            emit=emit,
            context=context,
        )

        getReleaseCode(release_name=to_name, emit=emit, context=context)


def _generateEvalCode(to_name, node, emit, context):
    source_name = context.allocateTempName("eval_source")
    globals_name = context.allocateTempName("eval_globals")
    locals_name = context.allocateTempName("eval_locals")

    generateExpressionCode(
        to_name=source_name,
        expression=node.subnode_source_code,
        emit=emit,
        context=context,
    )

    generateExpressionCode(
        to_name=globals_name,
        expression=node.subnode_globals_arg,
        emit=emit,
        context=context,
    )

    generateExpressionCode(
        to_name=locals_name,
        expression=node.subnode_locals_arg,
        emit=emit,
        context=context,
    )

    if node.isExpressionBuiltinEval() or (
        python_version >= 0x300 and node.isExpressionBuiltinExec()
    ):
        filename = "<string>"
    else:
        filename = "<execfile>"

    if (
        python_version >= 0x3B0
        and node.isExpressionBuiltinExec()
        and node.subnode_closure is not None
    ):
        closure_name = context.allocateTempName("eval_closure")

        generateExpressionCode(
            to_name=closure_name,
            expression=node.subnode_closure,
            emit=emit,
            context=context,
        )
    else:
        closure_name = None

    if node.isExpressionBuiltinEval() and python_version >= 0x3E0:
        # Since Python 3.14, the "eval" built-in suppresses constant
        # immortalization, unlike "exec" and older "eval" implementations.
        for_exec = False
    else:
        for_exec = True

    getBuiltinEvalCode(
        to_name=to_name,
        source_name=source_name,
        globals_name=globals_name,
        locals_name=locals_name,
        filename_name=context.getConstantCode(constant=filename),
        mode_name=context.getConstantCode(
            constant="eval" if node.isExpressionBuiltinEval() else "exec"
        ),
        closure_name=closure_name,
        for_exec=for_exec,
        emit=emit,
        context=context,
    )


def generateEvalCode(to_name, expression, emit, context):
    with withObjectCodeTemporaryAssignment(
        to_name, "eval_result", expression, emit, context
    ) as value_name:
        _generateEvalCode(
            to_name=value_name, node=expression, emit=emit, context=context
        )


def generateExecfileCode(to_name, expression, emit, context):
    assert python_version < 0x300

    with withObjectCodeTemporaryAssignment(
        to_name, "execfile_result", expression, emit, context
    ) as value_name:
        _generateEvalCode(
            to_name=value_name, node=expression, emit=emit, context=context
        )


def generateLocalsDictSyncCode(statement, emit, context):
    locals_arg = statement.subnode_locals_arg
    locals_name = context.allocateTempName("sync_locals")

    generateExpressionCode(
        to_name=locals_name, expression=locals_arg, emit=emit, context=context
    )

    with context.withCurrentSourceCodeReference(statement.getSourceReference()):
        _getStoreLocalsCode(
            locals_name=locals_name,
            variable_traces=statement.getPreviousVariablesTraces(),
            is_dict=locals_arg.hasShapeDictionaryExact(),
            emit=emit,
            context=context,
        )

    getReleaseCode(release_name=locals_name, emit=emit, context=context)


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
