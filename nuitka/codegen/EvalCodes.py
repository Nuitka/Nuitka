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
""" Eval/exec/execfile/compile built-in related codes. """

from nuitka import Options
from nuitka.nodes.shapes.BuiltinTypeShapes import ShapeTypeDict
from nuitka.PythonVersions import python_version

from .CodeHelpers import generateExpressionCode
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes
)
from .VariableCodes import getVariableAssignmentCode


def getStoreLocalsCode(locals_name, variables, is_dict, emit, context):
    for variable, version in variables:
        if not variable.isModuleVariable():
            key_name = context.getConstantCode(
                constant = variable.getName()
            )

            value_name = context.allocateTempName("locals_value", unique = True)

            if is_dict:
                emit(
                    "%s = PyDict_GetItem( %s, %s );" % (
                       value_name,
                       locals_name,
                       key_name,
                    )
                )
            else:
                emit(
                   "%s = PyObject_GetItem( %s, %s );" % (
                       value_name,
                       locals_name,
                       key_name,
                    )
                )

                getErrorExitBoolCode(
                    condition = """\
%s == NULL && !EXCEPTION_MATCH_BOOL_SINGLE( GET_ERROR_OCCURRED(), PyExc_KeyError )""" % value_name,
                    emit      = emit,
                    context   = context
                )

                emit("CLEAR_ERROR_OCCURRED();")

                context.addCleanupTempName(value_name)

            emit("if ( %s != NULL )" % value_name)
            emit('{')

            getVariableAssignmentCode(
                variable      = variable,
                version       = version,
                tmp_name      = value_name,
                needs_release = None, # TODO: Could be known maybe.
                in_place      = False,
                emit          = emit,
                context       = context
            )

            emit('}')


def generateBuiltinCompileCode(to_name, expression, emit, context):

    source_name = context.allocateTempName("compile_source")
    filename_name = context.allocateTempName("compile_filename")
    mode_name = context.allocateTempName("compile_mode")

    generateExpressionCode(
        to_name    = source_name,
        expression = expression.getSourceCode(),
        emit       = emit,
        context    = context
    )
    generateExpressionCode(
        to_name    = filename_name,
        expression = expression.getFilename(),
        emit       = emit,
        context    = context
    )
    generateExpressionCode(
        to_name    = mode_name,
        expression = expression.getMode(),
        emit       = emit,
        context    = context
    )

    if expression.getFlags() is not None:
        flags_name = context.allocateTempName("compile_flags")

        generateExpressionCode(
            to_name    = flags_name,
            expression = expression.getFlags(),
            emit       = emit,
            context    = context
        )
    else:
        flags_name = "NULL"

    if expression.getDontInherit() is not None:
        dont_inherit_name = context.allocateTempName("compile_dont_inherit")

        generateExpressionCode(
            to_name    = dont_inherit_name,
            expression = expression.getDontInherit(),
            emit       = emit,
            context    = context
        )
    else:
        dont_inherit_name = "NULL"

    if expression.getOptimize() is not None:
        optimize_name = context.allocateTempName("compile_dont_inherit")

        generateExpressionCode(
            to_name    = optimize_name,
            expression = expression.getOptimize(),
            emit       = emit,
            context    = context
        )
    else:
        optimize_name = "NULL"

    context.setCurrentSourceCodeReference(
        expression.getCompatibleSourceReference()
    )

    getBuiltinCompileCode(
        to_name           = to_name,
        source_name       = source_name,
        filename_name     = filename_name,
        mode_name         = mode_name,
        flags_name        = flags_name,
        dont_inherit_name = dont_inherit_name,
        optimize_name     = optimize_name,
        emit              = emit,
        context           = context
    )


def getBuiltinCompileCode(to_name, source_name, filename_name, mode_name,
                          flags_name, dont_inherit_name, optimize_name, emit,
                          context):
    if python_version < 300:
        args = (
            source_name,
            filename_name,
            mode_name,
            flags_name,
            dont_inherit_name
        )
    else:
        args = (
            source_name,
            filename_name,
            mode_name,
            flags_name,
            dont_inherit_name,
            optimize_name
        )

    emit(
        "%s = COMPILE_CODE( %s );" % (
            to_name,
            ", ".join(args)
        )
    )

    getReleaseCodes(
        release_names = (source_name, filename_name, mode_name, flags_name,
                         dont_inherit_name, optimize_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getBuiltinEvalCode(to_name, source_name, filename_name, globals_name,
                       locals_name, mode_name, emit, context):
    compiled_name = context.allocateTempName("eval_compiled")

    getBuiltinCompileCode(
        to_name           = compiled_name,
        source_name       = source_name,
        filename_name     = filename_name,
        mode_name         = mode_name,
        flags_name        = "NULL",
        dont_inherit_name = "NULL",
        optimize_name     = "NULL",
        emit              = emit,
        context           = context
    )

    emit(
        "%s = EVAL_CODE( %s, %s, %s );" % (
            to_name,
            compiled_name,
            globals_name,
            locals_name
        )
    )

    getReleaseCodes(
        release_names = (compiled_name, globals_name, locals_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def generateExecCode(statement, emit, context):
    source_arg = statement.getSourceCode()
    globals_arg = statement.getGlobals()
    locals_arg = statement.getLocals()

    source_name = context.allocateTempName("exec_source")
    globals_name = context.allocateTempName("exec_globals")
    locals_name = context.allocateTempName("exec_locals")

    generateExpressionCode(
        to_name    = source_name,
        expression = source_arg,
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = globals_name,
        expression = globals_arg,
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = locals_name,
        expression = locals_arg,
        emit       = emit,
        context    = context
    )

    source_ref = statement.getSourceReference()

    # Filename with origin in improved mode.
    if Options.isFullCompat():
        filename_name = context.getConstantCode(
            constant = "<string>"
        )
    else:
        filename_name = context.getConstantCode(
            constant = "<string at %s>" % source_ref.getAsString()
        )

    old_source_ref = context.setCurrentSourceCodeReference(
        locals_arg.getSourceReference()
          if Options.isFullCompat() else
        statement.getSourceReference()
    )

    compiled_name = context.allocateTempName("exec_compiled")

    getBuiltinCompileCode(
        to_name           = compiled_name,
        source_name       = source_name,
        filename_name     = filename_name,
        mode_name         = context.getConstantCode(
            constant = "exec"
        ),
        flags_name        = "NULL",
        dont_inherit_name = "NULL",
        optimize_name     = "NULL",
        emit              = emit,
        context           = context
    )

    to_name = context.allocateTempName("exec_result")

    emit(
        "%s = EVAL_CODE( %s, %s, %s );" % (
            to_name,
            compiled_name,
            globals_name,
            locals_name
        )
    )

    getReleaseCodes(
        release_names = (compiled_name, globals_name, locals_name),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    # Immediately release the exec result.
    context.addCleanupTempName(to_name)
    getReleaseCode(
        release_name = to_name,
        emit         = emit,
        context      = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)



def _generateEvalCode(to_name, node, emit, context):
    source_name = context.allocateTempName("eval_source")
    globals_name = context.allocateTempName("eval_globals")
    locals_name = context.allocateTempName("eval_locals")

    generateExpressionCode(
        to_name    = source_name,
        expression = node.getSourceCode(),
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = globals_name,
        expression = node.getGlobals(),
        emit       = emit,
        context    = context
    )

    generateExpressionCode(
        to_name    = locals_name,
        expression = node.getLocals(),
        emit       = emit,
        context    = context
    )

    if node.isExpressionBuiltinEval() or \
         (python_version >= 300 and node.isExpressionBuiltinExec()):
        filename = "<string>"
    else:
        filename = "<execfile>"

    getBuiltinEvalCode(
        to_name       = to_name,
        source_name   = source_name,
        globals_name  = globals_name,
        locals_name   = locals_name,
        filename_name = context.getConstantCode(
            constant = filename
        ),
        mode_name     = context.getConstantCode(
            constant = "eval" if node.isExpressionBuiltinEval() else "exec"
        ),
        emit          = emit,
        context       = context
    )


def generateEvalCode(to_name, expression, emit, context):
    return _generateEvalCode(
        to_name = to_name,
        node    = expression,
        emit    = emit,
        context = context
    )


def generateExecfileCode(to_name, expression, emit, context):
    assert python_version < 300

    return _generateEvalCode(
        to_name = to_name,
        node    = expression,
        emit    = emit,
        context = context
    )


def generateLocalsDictSyncCode(statement, emit, context):
    locals_arg = statement.getLocals()
    locals_name = context.allocateTempName("sync_locals")

    generateExpressionCode(
        to_name    = locals_name,
        expression = locals_arg,
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(
        statement.getSourceReference()
    )

    getStoreLocalsCode(
        locals_name = locals_name,
        variables   = statement.previous_traces,
        is_dict     = locals_arg.getTypeShape() is ShapeTypeDict,
        emit        = emit,
        context     = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)
