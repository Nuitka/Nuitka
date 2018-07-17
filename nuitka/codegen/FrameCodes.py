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
""" Frame codes

This is about frame stacks and their management. There are different kinds
of frames for different uses.
"""

from nuitka.PythonVersions import python_version

from . import Emission
from .CodeHelpers import _generateStatementSequenceCode
from .ErrorCodes import getFrameVariableTypeDescriptionCode
from .ExceptionCodes import getTracebackMakingIdentifier
from .Indentation import indented
from .LabelCodes import getGotoCode, getLabelCode
from .ModuleCodes import getModuleAccessCode
from .templates.CodeTemplatesFrames import (
    template_frame_attach_locals,
    template_frame_guard_cache_decl,
    template_frame_guard_frame_decl,
    template_frame_guard_full_block,
    template_frame_guard_full_exception_handler,
    template_frame_guard_full_return_handler,
    template_frame_guard_generator,
    template_frame_guard_generator_exception_handler,
    template_frame_guard_generator_return_handler,
    template_frame_guard_once
)


def getFrameLocalsStorageSize(type_descriptions):
    candidates = set()

    for type_description in type_descriptions:
        candidate = '+'.join(
            getTypeSizeOf(type_indicator)
            for type_indicator in sorted(type_description)
        )

        candidates.add(candidate)

    if not candidates:
        return '0'

    candidates = list(sorted(candidates))
    result = candidates.pop()

    while candidates:
        # assert False, (type_descriptions, context.frame_variables_stack[-1])

        result = "MAX( %s, %s )" % (result, candidates.pop())

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
    code_identifier = context.getCodeObjectHandle(
        code_object = code_object
    )

    parent_exception_exit = context.getExceptionEscape()

    # For nested frames, make sure to restore set the type description.
    if context.getFrameHandle() is not None:
        real_parent_exception_exit = parent_exception_exit
        parent_exception_exit = context.allocateLabel("nested_frame_exit")

    if statement_sequence.hasStructureMember():
        frame_identifier = "%s->m_frame" % context.getContextObjectName()
    else:
        frame_identifier = code_identifier.replace("codeobj_", "frame_")

    # Allow stacking of frame handles.
    frame_identifier = context.pushFrameHandle(
        frame_identifier
    )

    context.setExceptionEscape(
        context.allocateLabel("frame_exception_exit")
    )

    needs_preserve = statement_sequence.needsFrameExceptionPreserving()

    if statement_sequence.mayReturn():
        parent_return_exit = context.getReturnTarget()

        context.setReturnTarget(
            context.allocateLabel("frame_return_exit")
        )
    else:
        parent_return_exit = None

    # We need to define that all the variables needs to be pushed. We do not
    # have a flag that says "always NULL" for variables. With efficient NULL
    # passing however (not at all, TODO), that doesn't matter much.
    local_variables = statement_sequence.getParentVariableProvider().getLocalVariables()

    context.pushFrameVariables(
        tuple(
            _searchLocalVariableByName(local_variables, variable_name)
            for variable_name in
            code_object.getVarNames()
        )
    )

    # Now generate the statements code into a local buffer, to we can wrap
    # the frame stuff around it.
    local_emit = Emission.SourceCodeCollector()

    _generateStatementSequenceCode(
        statement_sequence = statement_sequence,
        emit               = local_emit,
        context            = context
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
            code_identifier       = code_identifier,
            type_descriptions     = type_descriptions,
            codes                 = local_emit.codes,
            parent_exception_exit = parent_exception_exit,
            frame_exception_exit  = frame_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_return_exit     = frame_return_exit,
            emit                  = emit,
            context               = context
        )
    elif guard_mode == "full":
        getFrameGuardHeavyCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = code_identifier,
            type_descriptions     = type_descriptions,
            parent_exception_exit = parent_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_exception_exit  = frame_exception_exit,
            frame_return_exit     = frame_return_exit,
            codes                 = local_emit.codes,
            needs_preserve        = needs_preserve,
            emit                  = emit,
            context               = context
        )
    elif guard_mode == "once":
        getFrameGuardOnceCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = code_identifier,
            parent_exception_exit = parent_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_exception_exit  = frame_exception_exit,
            frame_return_exit     = frame_return_exit,
            codes                 = local_emit.codes,
            needs_preserve        = needs_preserve,
            emit                  = emit,
            context               = context
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
    if type_indicator in ('O', 'o', 'N', 'c'):
        return "sizeof(void *)"
    elif type_indicator == 'b':
        return "sizeof(nuitka_bool)"
    else:
        assert False, type_indicator


def getFrameAttachLocalsCode(context, frame_identifier):
    frame_variable_codes = context.getFrameVariableCodeNames()
    frame_variable_codes = ",\n    ".join(frame_variable_codes)
    if frame_variable_codes:
        frame_variable_codes = ",\n    " + frame_variable_codes


    return template_frame_attach_locals % {
        "frame_identifier"      : frame_identifier,
        "type_description"      : context.getFrameVariableTypeDescriptionName(),
        "frame_variable_refs"   : frame_variable_codes
    }


def getFrameGuardHeavyCode(frame_identifier, code_identifier, codes,
                           type_descriptions, needs_preserve, parent_exception_exit,
                           parent_return_exit, frame_exception_exit,
                           frame_return_exit, emit, context):
    # We really need this many parameters here.

    no_exception_exit = context.allocateLabel("frame_no_exception")

    context.addFrameDeclaration(
        template_frame_guard_cache_decl % {
            "frame_identifier" : frame_identifier,
        }
    )
    context.addFrameDeclaration(
        template_frame_guard_frame_decl % {
            "frame_identifier" : frame_identifier,
        }
    )

    emit(
        template_frame_guard_full_block % {
            "frame_identifier"  : frame_identifier,
            "code_identifier"   : code_identifier,
            "locals_size"       : getFrameLocalsStorageSize(type_descriptions),
            "codes"             : indented(codes, 0),
            "module_identifier" : getModuleAccessCode(context),
            "no_exception_exit" : no_exception_exit,
            "needs_preserve"    : 1 if needs_preserve else 0,
        }
    )

    if frame_return_exit is not None:
        emit(
            template_frame_guard_full_return_handler % {
                "frame_identifier"  : frame_identifier,
                "return_exit"       : parent_return_exit,
                "frame_return_exit" : frame_return_exit,
                "needs_preserve"    : 1 if needs_preserve else 0,
            }
        )

    if frame_exception_exit is not None:

        emit(
            template_frame_guard_full_exception_handler % {
                "frame_identifier"      : frame_identifier,
                "tb_making"             : getTracebackMakingIdentifier(
                                              context     = context,
                                              lineno_name = "exception_lineno"
                                          ),
                "parent_exception_exit" : parent_exception_exit,
                "frame_exception_exit"  : frame_exception_exit,
                "attach_locals"         : getFrameAttachLocalsCode(context, frame_identifier),
                "needs_preserve"        : 1 if needs_preserve else 0,
            }
        )

    emit("%s:;\n" % no_exception_exit)


def getFrameGuardOnceCode(frame_identifier, code_identifier,
                          codes, parent_exception_exit, parent_return_exit,
                          frame_exception_exit, frame_return_exit,
                          needs_preserve, emit, context):
    # We really need this many parameters here.

    # Used for modules only currently, but that ought to change.
    assert parent_return_exit is None and frame_return_exit is None

    context.addFrameDeclaration(
        template_frame_guard_frame_decl % {
            "frame_identifier" : frame_identifier,
        }
    )

    emit(
        template_frame_guard_once % {
            "frame_identifier"      : frame_identifier,
            "code_identifier"       : code_identifier,
            "codes"                 : indented(codes, 0),
            "module_identifier"     : getModuleAccessCode(context),
            "tb_making"             : getTracebackMakingIdentifier(
                                         context     = context,
                                         lineno_name = "exception_lineno"
                                      ),
            "parent_exception_exit" : parent_exception_exit,
            "frame_exception_exit"  : frame_exception_exit,
            "no_exception_exit"     : context.allocateLabel(
                "frame_no_exception"
            ),
            "needs_preserve"        : 1 if needs_preserve else 0
        }
    )


def getFrameGuardLightCode(code_identifier, codes, parent_exception_exit,
                           type_descriptions,
                           parent_return_exit, frame_exception_exit,
                           frame_return_exit, emit, context):
    context.markAsNeedsExceptionVariables()

    context_identifier = context.getContextObjectName()

    context.addFrameDeclaration(
        template_frame_guard_cache_decl % {
            "frame_identifier" : "frame_" + context_identifier,
        }
    )

    no_exception_exit = context.allocateLabel("frame_no_exception")

    frame_identifier = context_identifier + "->m_frame"

    emit(
        template_frame_guard_generator % {
            "context_identifier"     : context_identifier,
            "frame_cache_identifier" : "cache_frame_" + context_identifier,
            "code_identifier"        : code_identifier,
            "locals_size"            : getFrameLocalsStorageSize(type_descriptions),
            "codes"                  : indented(codes, 0),
            "module_identifier"      : getModuleAccessCode(context),
            "no_exception_exit"      : no_exception_exit,
        }
    )

    if frame_return_exit is not None:
        emit(
            template_frame_guard_generator_return_handler % {
                "context_identifier" : context_identifier,
                "frame_identifier"   : "%s->m_frame" % context_identifier,
                "return_exit"        : parent_return_exit,
                "frame_return_exit"  : frame_return_exit,
            }
        )

    if frame_exception_exit is not None:
        emit(
            template_frame_guard_generator_exception_handler % {
                "context_identifier"     : context_identifier,
                "frame_identifier"       : "%s->m_frame" % context_identifier,
                "frame_cache_identifier" : "cache_frame_" + context_identifier,
                "tb_making"              : getTracebackMakingIdentifier(
                                               context     = context,
                                               lineno_name = "exception_lineno"
                                           ),
                "attach_locals"          : indented(
                    getFrameAttachLocalsCode(context, frame_identifier)
                ),
                "frame_exception_exit"   : frame_exception_exit,
                "parent_exception_exit"  : parent_exception_exit
            }
        )

    emit("%s:;\n" % no_exception_exit)


def generateFramePreserveExceptionCode(statement, emit, context):
    emit("// Preserve existing published exception.")

    if python_version < 300:
        emit(
            "PRESERVE_FRAME_EXCEPTION( %(frame_identifier)s );" % {
                "frame_identifier" : context.getFrameHandle()
            }
        )
    else:
        preserver_id = statement.getPreserverId()

        if preserver_id == 0:
            assert False

            emit(
                "PRESERVE_FRAME_EXCEPTION( %(frame_identifier)s );" % {
                    "frame_identifier" : context.getFrameHandle()
                }
            )
        else:
            context.addExceptionPreserverVariables(preserver_id)

            # TODO: Multiple thread state calls should be avoided.
            emit(
                """\
exception_preserved_type_%(preserver_id)d = EXC_TYPE(PyThreadState_GET());
Py_XINCREF( exception_preserved_type_%(preserver_id)d );
exception_preserved_value_%(preserver_id)d = EXC_VALUE(PyThreadState_GET());
Py_XINCREF( exception_preserved_value_%(preserver_id)d );
exception_preserved_tb_%(preserver_id)d = (PyTracebackObject *)EXC_TRACEBACK(PyThreadState_GET());
Py_XINCREF( exception_preserved_tb_%(preserver_id)d );
""" % {
                    "preserver_id"  : preserver_id,
                }
            )


def generateFrameRestoreExceptionCode(statement, emit, context):
    emit("// Restore previous exception.")

    if python_version < 300:
        emit(
            "RESTORE_FRAME_EXCEPTION( %(frame_identifier)s );" % {
                "frame_identifier" : context.getFrameHandle()
            }
        )
    else:
        preserver_id = statement.getPreserverId()

        emit(
            """\
SET_CURRENT_EXCEPTION( exception_preserved_type_%(preserver_id)d, \
exception_preserved_value_%(preserver_id)d, \
exception_preserved_tb_%(preserver_id)d );""" % {
                "preserver_id" : preserver_id,
            }
        )
