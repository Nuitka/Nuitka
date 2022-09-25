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
""" Frame codes

This is about frame stacks and their management. There are different kinds
of frames for different uses.
"""

from nuitka.PythonVersions import python_version

from .CodeHelpers import _generateStatementSequenceCode
from .Emission import SourceCodeCollector
from .ErrorCodes import getFrameVariableTypeDescriptionCode
from .ExceptionCodes import getTracebackMakingIdentifier
from .Indentation import indented
from .LabelCodes import getGotoCode, getLabelCode
from .ModuleCodes import getModuleAccessCode
from .templates.CodeTemplatesFrames import (
    template_frame_attach_locals,
    template_frame_guard_full_block,
    template_frame_guard_full_exception_handler,
    template_frame_guard_full_return_handler,
    template_frame_guard_generator,
    template_frame_guard_generator_exception_handler,
    template_frame_guard_generator_return_handler,
    template_frame_guard_once_block,
    template_frame_guard_once_exception_handler,
)


def getFrameLocalsStorageSize(type_descriptions):
    candidates = set()

    for type_description in type_descriptions:
        candidate = "+".join(
            getTypeSizeOf(type_indicator) for type_indicator in sorted(type_description)
        )

        candidates.add(candidate)

    if not candidates:
        return "0"

    candidates = list(sorted(candidates))
    result = candidates.pop()

    while candidates:
        # assert False, (type_descriptions, context.frame_variables_stack[-1])

        result = "MAX(%s, %s)" % (result, candidates.pop())

    return result


def _searchLocalVariableByName(local_variables, variable_name):
    for local_variable in local_variables:
        if local_variable.getName() == variable_name:
            return local_variable

    return None


def generateStatementsFrameCode(statement_sequence, emit, context):
    # This is a wrapper that provides also handling of frames, which got a
    # lot of variants and details, therefore lots of branches and details.
    # pylint: disable=too-many-branches,too-many-locals,too-many-statements

    context.pushCleanupScope()

    guard_mode = statement_sequence.getGuardMode()

    code_object = statement_sequence.getCodeObject()
    code_identifier = context.getCodeObjectHandle(code_object=code_object)

    parent_exception_exit = context.getExceptionEscape()

    # For nested frames, make sure to restore set the type description.
    if context.getFrameHandle() is not None:
        real_parent_exception_exit = parent_exception_exit
        parent_exception_exit = context.allocateLabel("nested_frame_exit")

    # Allow stacking of frame handles.
    context.pushFrameHandle(code_identifier, statement_sequence.hasStructureMember())

    context.setExceptionEscape(context.allocateLabel("frame_exception_exit"))

    needs_preserve = statement_sequence.needsFrameExceptionPreserving()

    if statement_sequence.mayReturn():
        parent_return_exit = context.getReturnTarget()

        context.setReturnTarget(context.allocateLabel("frame_return_exit"))
    else:
        parent_return_exit = None

    # We need to define that all the variables needs to be pushed. We do not
    # have a flag that says "always NULL" for variables. With efficient NULL
    # passing however (not at all, TODO), that doesn't matter much.
    local_variables = statement_sequence.getParentVariableProvider().getLocalVariables()

    context.pushFrameVariables(
        tuple(
            _searchLocalVariableByName(local_variables, variable_name)
            for variable_name in code_object.getVarNames()
        )
    )

    # Now generate the statements code into a local buffer, to we can wrap
    # the frame stuff around it.
    local_emit = SourceCodeCollector()

    _generateStatementSequenceCode(
        statement_sequence=statement_sequence, emit=local_emit, context=context
    )

    if statement_sequence.mayRaiseException(BaseException):
        frame_exception_exit = context.getExceptionEscape()
    else:
        frame_exception_exit = None

    if parent_return_exit is not None:
        frame_return_exit = context.getReturnTarget()
    else:
        frame_return_exit = None

    type_descriptions = context.getFrameVariableTypeDescriptions()

    if guard_mode == "generator":
        # TODO: This case should care about "needs_preserve", as for
        # Python3 it is actually not a stub of empty code.

        getFrameGuardLightCode(
            code_identifier=code_identifier,
            type_descriptions=type_descriptions,
            codes=local_emit.codes,
            parent_exception_exit=parent_exception_exit,
            frame_exception_exit=frame_exception_exit,
            parent_return_exit=parent_return_exit,
            frame_return_exit=frame_return_exit,
            emit=emit,
            context=context,
        )
    elif guard_mode == "full":
        getFrameGuardHeavyCode(
            code_identifier=code_identifier,
            type_descriptions=type_descriptions,
            parent_exception_exit=parent_exception_exit,
            parent_return_exit=parent_return_exit,
            frame_exception_exit=frame_exception_exit,
            frame_return_exit=frame_return_exit,
            codes=local_emit.codes,
            needs_preserve=needs_preserve,
            emit=emit,
            context=context,
        )
    elif guard_mode == "once":
        getFrameGuardOnceCode(
            code_identifier=code_identifier,
            parent_exception_exit=parent_exception_exit,
            parent_return_exit=parent_return_exit,
            frame_exception_exit=frame_exception_exit,
            frame_return_exit=frame_return_exit,
            codes=local_emit.codes,
            needs_preserve=needs_preserve,
            emit=emit,
            context=context,
        )
    else:
        assert False, guard_mode

    context.popFrameVariables()
    context.popFrameHandle()

    # For nested frames, make sure to restore set the type description.
    if context.getFrameHandle() is not None:
        label = context.allocateLabel("skip_nested_handling")
        getGotoCode(label, emit)
        getLabelCode(parent_exception_exit, emit)
        emit(getFrameVariableTypeDescriptionCode(context))
        getGotoCode(real_parent_exception_exit, emit)
        getLabelCode(label, emit)

        parent_exception_exit = real_parent_exception_exit

    context.popCleanupScope()

    context.setExceptionEscape(parent_exception_exit)

    if frame_return_exit is not None:
        context.setReturnTarget(parent_return_exit)


def getTypeSizeOf(type_indicator):
    if type_indicator in ("O", "o", "N", "c"):
        return "sizeof(void *)"
    elif type_indicator == "b":
        return "sizeof(nuitka_bool)"
    elif type_indicator == "L":
        return "sizeof(nuitka_ilong)"
    else:
        assert False, type_indicator


def getFrameAttachLocalsCode(context, frame_identifier):
    frame_variable_codes = context.getFrameVariableCodeNames()
    frame_variable_codes = ",\n    ".join(frame_variable_codes)
    if frame_variable_codes:
        frame_variable_codes = ",\n    " + frame_variable_codes

    return template_frame_attach_locals % {
        "frame_identifier": frame_identifier,
        "type_description": context.getFrameTypeDescriptionDeclaration(),
        "frame_variable_refs": frame_variable_codes,
    }


def getFrameGuardHeavyCode(
    code_identifier,
    codes,
    type_descriptions,
    needs_preserve,
    parent_exception_exit,
    parent_return_exit,
    frame_exception_exit,
    frame_return_exit,
    emit,
    context,
):
    # We really need this many parameters here and it gets very
    # detail rich, pylint: disable=too-many-locals

    no_exception_exit = context.allocateLabel("frame_no_exception")

    frame_identifier = context.getFrameHandle()
    frame_cache_identifier = context.variable_storage.addFrameCacheDeclaration(
        frame_identifier.code_name
    )

    (
        _exception_type,
        _exception_value,
        _exception_tb,
        exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    emit(
        template_frame_guard_full_block
        % {
            "frame_identifier": frame_identifier,
            "frame_cache_identifier": frame_cache_identifier,
            "code_identifier": code_identifier,
            "locals_size": getFrameLocalsStorageSize(type_descriptions),
            "codes": indented(codes, 0),
            "module_identifier": getModuleAccessCode(context),
            "no_exception_exit": no_exception_exit,
            "needs_preserve": 1 if needs_preserve else 0,
        }
    )

    if frame_return_exit is not None:
        emit(
            template_frame_guard_full_return_handler
            % {
                "frame_identifier": frame_identifier,
                "return_exit": parent_return_exit,
                "frame_return_exit": frame_return_exit,
                "needs_preserve": 1 if needs_preserve else 0,
            }
        )

    if frame_exception_exit is not None:
        (
            _exception_type,
            _exception_value,
            exception_tb,
            exception_lineno,
        ) = context.variable_storage.getExceptionVariableDescriptions()

        emit(
            template_frame_guard_full_exception_handler
            % {
                "frame_identifier": frame_identifier,
                "frame_cache_identifier": frame_cache_identifier,
                "tb_making": getTracebackMakingIdentifier(
                    context=context, lineno_name=exception_lineno
                ),
                "parent_exception_exit": parent_exception_exit,
                "frame_exception_exit": frame_exception_exit,
                "attach_locals": getFrameAttachLocalsCode(context, frame_identifier),
                "needs_preserve": 1 if needs_preserve else 0,
                "exception_tb": exception_tb,
                "exception_lineno": exception_lineno,
            }
        )

    getLabelCode(no_exception_exit, emit)


def getFrameGuardOnceCode(
    code_identifier,
    codes,
    parent_exception_exit,
    parent_return_exit,
    frame_exception_exit,
    frame_return_exit,
    needs_preserve,
    emit,
    context,
):
    # We really need this many parameters here.
    no_exception_exit = context.allocateLabel("frame_no_exception")

    # Used for modules only currently, but that ought to change.
    assert parent_return_exit is None and frame_return_exit is None

    emit(
        template_frame_guard_once_block
        % {
            "frame_identifier": context.getFrameHandle(),
            "code_identifier": code_identifier,
            "codes": indented(codes, 0),
            "module_identifier": getModuleAccessCode(context),
            "no_exception_exit": no_exception_exit,
            "needs_preserve": 1 if needs_preserve else 0,
        }
    )

    if frame_exception_exit is not None:
        (
            _exception_type,
            _exception_value,
            exception_tb,
            exception_lineno,
        ) = context.variable_storage.getExceptionVariableDescriptions()

        emit(
            template_frame_guard_once_exception_handler
            % {
                "frame_identifier": context.getFrameHandle(),
                "tb_making": getTracebackMakingIdentifier(
                    context=context, lineno_name=exception_lineno
                ),
                "parent_exception_exit": parent_exception_exit,
                "frame_exception_exit": frame_exception_exit,
                "needs_preserve": 1 if needs_preserve else 0,
                "exception_tb": exception_tb,
                "exception_lineno": exception_lineno,
            }
        )

    getLabelCode(no_exception_exit, emit)


def getFrameGuardLightCode(
    code_identifier,
    codes,
    parent_exception_exit,
    type_descriptions,
    parent_return_exit,
    frame_exception_exit,
    frame_return_exit,
    emit,
    context,
):
    # We really need this many parameters here and it gets very
    # detail rich, pylint: disable=too-many-locals
    (
        exception_type,
        _exception_value,
        exception_tb,
        exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    context_identifier = context.getContextObjectName()

    no_exception_exit = context.allocateLabel("frame_no_exception")

    frame_identifier = context.getFrameHandle()
    frame_cache_identifier = context.variable_storage.addFrameCacheDeclaration(
        frame_identifier.code_name
    )

    emit(
        template_frame_guard_generator
        % {
            "context_identifier": context_identifier,
            "frame_cache_identifier": frame_cache_identifier,
            "code_identifier": code_identifier,
            "locals_size": getFrameLocalsStorageSize(type_descriptions),
            "codes": indented(codes, 0),
            "module_identifier": getModuleAccessCode(context),
            "no_exception_exit": no_exception_exit,
        }
    )

    if frame_return_exit is not None:
        emit(
            template_frame_guard_generator_return_handler
            % {
                "context_identifier": context_identifier,
                "frame_identifier": "%s->m_frame" % context_identifier,
                "return_exit": parent_return_exit,
                "frame_return_exit": frame_return_exit,
            }
        )

    if frame_exception_exit is not None:
        emit(
            template_frame_guard_generator_exception_handler
            % {
                "context_identifier": context_identifier,
                "frame_identifier": frame_identifier,
                "frame_cache_identifier": frame_cache_identifier,
                "exception_type": exception_type,
                "exception_tb": exception_tb,
                "exception_lineno": exception_lineno,
                "tb_making": getTracebackMakingIdentifier(
                    context=context, lineno_name=exception_lineno
                ),
                "attach_locals": indented(
                    getFrameAttachLocalsCode(context, frame_identifier)
                ),
                "frame_exception_exit": frame_exception_exit,
                "parent_exception_exit": parent_exception_exit,
            }
        )

    getLabelCode(no_exception_exit, emit)


def generateFramePreserveExceptionCode(statement, emit, context):
    if python_version < 0x300:
        emit("// Preserve existing published exception.")

        emit(
            "PRESERVE_FRAME_EXCEPTION(%(frame_identifier)s);"
            % {"frame_identifier": context.getFrameHandle()}
        )
    else:
        preserver_id = statement.getPreserverId()

        assert preserver_id != 0, statement
        exception_preserved = context.addExceptionPreserverVariables(preserver_id)

        emit(
            """\
// Preserve existing published exception id %(preserver_id)d.
%(exception_preserved)s = GET_CURRENT_EXCEPTION();
"""
            % {
                "exception_preserved": exception_preserved,
                "preserver_id": preserver_id,
            }
        )


def generateFrameRestoreExceptionCode(statement, emit, context):
    if python_version < 0x300:
        emit(
            """\
// Restore previous exception.
RESTORE_FRAME_EXCEPTION(%(frame_identifier)s);"""
            % {"frame_identifier": context.getFrameHandle()}
        )
    else:
        preserver_id = statement.getPreserverId()

        exception_preserved = context.addExceptionPreserverVariables(preserver_id)

        emit(
            """\
// Restore previous exception id %(preserver_id)d.
SET_CURRENT_EXCEPTION(&%(exception_preserved)s);
"""
            % {
                "exception_preserved": exception_preserved,
                "preserver_id": preserver_id,
            }
        )
