#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

from . import Contexts, Emission
from .ExceptionCodes import getTracebackMakingIdentifier
from .GlobalsLocalsCodes import getLoadLocalsCode
from .Indentation import indented
from .ModuleCodes import getModuleAccessCode
from .templates.CodeTemplatesFrames import (
    template_frame_guard_cache_decl,
    template_frame_guard_coroutine,
    template_frame_guard_frame_decl,
    template_frame_guard_full_block,
    template_frame_guard_full_exception_handler,
    template_frame_guard_full_return_handler,
    template_frame_guard_generator,
    template_frame_guard_generator_exception_handler,
    template_frame_guard_generator_return_handler,
    template_frame_guard_once
)


def generateStatementsFrameCode(statement_sequence, emit, context):
    # This is a wrapper that provides also handling of frames, which got a
    # lot of variants and details, therefore lots of branches.
    # pylint: disable=R0912,R0915

    context = Contexts.PythonStatementCContext(context)

    provider = statement_sequence.getParentVariableProvider()
    guard_mode = statement_sequence.getGuardMode()

    parent_exception_exit = context.getExceptionEscape()

    # Allow stacking of frame handles.
    old_frame_handle = context.getFrameHandle()

    if guard_mode != "pass_through":
        if provider.isExpressionGeneratorObjectBody():
            context.setFrameHandle("generator->m_frame")
        elif provider.isExpressionCoroutineObjectBody():
            context.setFrameHandle("coroutine->m_frame")
        elif provider.isCompiledPythonModule():
            context.setFrameHandle("frame_module")
        else:
            context.setFrameHandle("frame_function")

        context.setExceptionEscape(
            context.allocateLabel("frame_exception_exit")
        )
    else:
        context.setFrameHandle("PyThreadState_GET()->frame")

    needs_preserve = statement_sequence.needsFrameExceptionPreserving()

    if statement_sequence.mayReturn() and guard_mode != "pass_through":
        parent_return_exit = context.getReturnTarget()

        context.setReturnTarget(
            context.allocateLabel("frame_return_exit")
        )
    else:
        parent_return_exit = None

    # Now generate the statements code into a local buffer, to we can wrap
    # the frame stuff around it.
    local_emit = Emission.SourceCodeCollector()

    from .CodeGeneration import _generateStatementSequenceCode
    _generateStatementSequenceCode(
        statement_sequence = statement_sequence,
        emit               = local_emit,
        context            = context
    )

    if statement_sequence.mayRaiseException(BaseException) or \
       guard_mode == "generator":
        frame_exception_exit = context.getExceptionEscape()
    else:
        frame_exception_exit = None

    if parent_return_exit is not None:
        frame_return_exit = context.getReturnTarget()
    else:
        frame_return_exit = None

    if guard_mode == "generator":
        assert provider.isExpressionGeneratorObjectBody() or provider.isExpressionCoroutineObjectBody()

        # TODO: This case should care about "needs_preserve", as for
        # Python3 it is actually not a stub of empty code.

        getFrameGuardLightCode(
            code_identifier       = statement_sequence.getCodeObjectHandle(
                context = context
            ),
            codes                 = local_emit.codes,
            parent_exception_exit = parent_exception_exit,
            frame_exception_exit  = frame_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_return_exit     = frame_return_exit,
            provider              = provider,
            emit                  = emit,
            context               = context
        )
    elif guard_mode == "pass_through":
        # This case does not care about "needs_preserve", as for that kind
        # of frame, it is an empty code stub anyway.
        local_emit.emitTo(emit)
    elif guard_mode == "full":
        assert provider.isExpressionFunctionBody() or \
               provider.isExpressionClassBody()

        getFrameGuardHeavyCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = statement_sequence.getCodeObjectHandle(
                context
            ),
            parent_exception_exit = parent_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_exception_exit  = frame_exception_exit,
            frame_return_exit     = frame_return_exit,
            codes                 = local_emit.codes,
            needs_preserve        = needs_preserve,
            provider              = provider,
            emit                  = emit,
            context               = context
        )
    elif guard_mode == "once":
        getFrameGuardOnceCode(
            frame_identifier      = context.getFrameHandle(),
            code_identifier       = statement_sequence.getCodeObjectHandle(
                context = context
            ),
            parent_exception_exit = parent_exception_exit,
            parent_return_exit    = parent_return_exit,
            frame_exception_exit  = frame_exception_exit,
            frame_return_exit     = frame_return_exit,
            codes                 = local_emit.codes,
            needs_preserve        = needs_preserve,
            provider              = provider,
            emit                  = emit,
            context               = context
        )
    else:
        assert False, guard_mode

    context.setExceptionEscape(parent_exception_exit)

    if frame_return_exit is not None:
        context.setReturnTarget(parent_return_exit)

    context.setFrameHandle(old_frame_handle)

    # Complain if any temporary was not dealt with yet.
    assert not context.getCleanupTempnames(), \
      context.getCleanupTempnames()


def getFrameGuardHeavyCode(frame_identifier, code_identifier, codes,
                           needs_preserve, parent_exception_exit,
                           parent_return_exit, frame_exception_exit,
                           frame_return_exit, provider, emit, context):
    # We really need this many parameters here. pylint: disable=R0913

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
            "codes"             : indented(codes, 0),
            "module_identifier" : getModuleAccessCode(context = context),
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
        frame_locals_name, locals_code = getFrameLocalsUpdateCode(
            provider = provider,
            context  = context
        )

        emit(
            template_frame_guard_full_exception_handler % {
                "frame_identifier"      : frame_identifier,
                "frame_locals_name"     : frame_locals_name,
                "store_frame_locals"    : indented(
                    locals_code,
                    2,
                    vert_block = True
                ),
                "tb_making"             : getTracebackMakingIdentifier(
                                              context     = context,
                                              lineno_name = "exception_lineno"
                                          ),
                "parent_exception_exit" : parent_exception_exit,
                "frame_exception_exit"  : frame_exception_exit,
                "needs_preserve"        : 1 if needs_preserve else 0,
            }
        )

    emit("%s:;\n" % no_exception_exit)


def getFrameGuardOnceCode(frame_identifier, code_identifier,
                          codes, parent_exception_exit, parent_return_exit,
                          frame_exception_exit, frame_return_exit,
                          needs_preserve, provider, emit, context):
    # We really need this many parameters here. pylint: disable=R0913

    # Used for modules only currently, but that ought to change.
    assert parent_return_exit is None and frame_return_exit is None

    if not provider.isCompiledPythonModule():
        _frame_locals_name, locals_code = getFrameLocalsUpdateCode(
            provider = provider,
            context  = context
        )

        # TODO: Not using locals, which is only OK for modules
        assert False, locals_code

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
            "module_identifier"     : getModuleAccessCode(context = context),
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
                           parent_return_exit, frame_exception_exit,
                           frame_return_exit, provider, emit, context):
    context.markAsNeedsExceptionVariables()

    assert frame_exception_exit is not None

    if context.getOwner().isExpressionGeneratorObjectBody():
        kind = "generator"
        template = template_frame_guard_generator
    else:
        kind = "coroutine"
        template = template_frame_guard_coroutine

    context.addFrameDeclaration(
        template_frame_guard_cache_decl % {
            "frame_identifier" : "frame_" + kind,
        }
    )

    no_exception_exit = context.allocateLabel("frame_no_exception")

    emit(
        template % {
            "frame_cache_identifier" : "cache_frame_" + kind,
            "code_identifier"        : code_identifier,
            "codes"                  : indented(codes, 0),
            "module_identifier"      : getModuleAccessCode(context = context),
            "no_exception_exit"      : no_exception_exit,
        }
    )

    if frame_return_exit is not None:
        emit(
            template_frame_guard_generator_return_handler % {
                "frame_identifier"  : "%s->m_frame" % kind,
                "return_exit"       : parent_return_exit,
                "frame_return_exit" : frame_return_exit,
            }
        )

    frame_locals_name, locals_code = getFrameLocalsUpdateCode(
        provider = provider,
        context  = context
    )

    if kind == "generator":
        template = template_frame_guard_generator_exception_handler
    else:
        template = template_frame_guard_generator_exception_handler

    # TODO: Don't create locals for StopIteration or GeneratorExit, that is just
    # wasteful.
    emit(
        template % {
            "frame_identifier"      : "%s->m_frame" % kind,
            "frame_locals_name"     : frame_locals_name,
            "store_frame_locals"    : indented(
                locals_code,
                2,
                vert_block = True
            ),
            "tb_making"             : getTracebackMakingIdentifier(
                                          context     = context,
                                          lineno_name = "exception_lineno"
                                      ),
            "frame_exception_exit"  : frame_exception_exit,
            "parent_exception_exit" : parent_exception_exit,
            "no_exception_exit"     : no_exception_exit,
        }
    )


def getFrameLocalsUpdateCode(provider, context):
    locals_codes = Emission.SourceCodeCollector()

    context.setCurrentSourceCodeReference(
        provider.getSourceReference()
    )

    frame_locals_name = context.allocateTempName(
        "frame_locals",
        unique = True
    )

    getLoadLocalsCode(
        to_name  = frame_locals_name,
        provider = provider,
        mode     = "updated",
        emit     = locals_codes.emit,
        context  = context
    )

    if context.needsCleanup(frame_locals_name):
        context.removeCleanupTempName(frame_locals_name)

    return frame_locals_name, locals_codes.codes


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

        if preserver_id == 0 and python_version < 300:
            emit(
                "PRESERVE_FRAME_EXCEPTION( %(frame_identifier)s );" % {
                    "frame_identifier" : context.getFrameHandle()
                }
            )
        else:
            context.addExceptionPreserverVariables(preserver_id)

            emit(
                """\
exception_preserved_type_%(preserver_id)d = PyThreadState_GET()->exc_type;
Py_XINCREF( exception_preserved_type_%(preserver_id)d );
exception_preserved_value_%(preserver_id)d = PyThreadState_GET()->exc_value;
Py_XINCREF( exception_preserved_value_%(preserver_id)d );
exception_preserved_tb_%(preserver_id)d = (PyTracebackObject *)PyThreadState_GET()->exc_traceback;
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

        if preserver_id == 0  and python_version < 300:
            emit(
                "RESTORE_FRAME_EXCEPTION( %(frame_identifier)s );" % {
                    "frame_identifier" : context.getFrameHandle()
                }
            )
        else:
            # pylint: disable=C0301

            emit(
                """\
SET_CURRENT_EXCEPTION( exception_preserved_type_%(preserver_id)d, exception_preserved_value_%(preserver_id)d, exception_preserved_tb_%(preserver_id)d );""" % {
                    "preserver_id" : preserver_id,
                }
            )
