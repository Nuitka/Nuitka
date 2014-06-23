#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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


from nuitka.Utils import python_version

from . import CodeTemplates, Emission
from .ExceptionCodes import getTracebackMakingIdentifier
from .GlobalsLocalsCodes import getLoadLocalsCode
from .Indentation import indented
from .LabelCodes import getGotoCode
from .LineNumberCodes import getSetLineNumberCodeRaw
from .ModuleCodes import getModuleAccessCode


def getFrameGuardHeavyCode(frame_identifier, code_identifier, codes,
                           needs_preserve, parent_exception_exit,
                           parent_return_exit, frame_exception_exit,
                           frame_return_exit, provider, context):
    no_exception_exit = context.allocateLabel("frame_no_exception")

    result = CodeTemplates.template_frame_guard_full_block % {
        "frame_identifier"  : frame_identifier,
        "code_identifier"   : code_identifier,
        "codes"             : indented(codes, 0),
        "module_identifier" : getModuleAccessCode(context = context),
        "no_exception_exit" : no_exception_exit,
        "needs_preserve"    : 1 if needs_preserve else 0,
    }

    if frame_return_exit is not None:
        result += CodeTemplates.template_frame_guard_full_return_handler % {
            "frame_identifier"  : frame_identifier,
            "return_exit"       : parent_return_exit,
            "frame_return_exit" : frame_return_exit,
            "needs_preserve"    : 1 if needs_preserve else 0,
        }


    if frame_exception_exit is not None:
        locals_code = getFrameLocalsUpdateCode(
            provider = provider,
            context  = context
        )

        result += CodeTemplates.template_frame_guard_full_exception_handler % {
            "frame_identifier"      : frame_identifier,
            "store_frame_locals"    : indented(
                locals_code,
                0,
                vert_block = True
            ),
            "tb_making"             : getTracebackMakingIdentifier(context),
            "parent_exception_exit" : parent_exception_exit,
            "frame_exception_exit"  : frame_exception_exit,
            "needs_preserve"        : 1 if needs_preserve else 0,
        }

    result += "%s:;\n" % no_exception_exit

    return result


def getFrameGuardOnceCode(frame_identifier, code_identifier,
                          codes, parent_exception_exit, parent_return_exit,
                          frame_exception_exit, frame_return_exit,
                          needs_preserve, provider, context):
    # Used for modules only currently, but that ought to change.
    assert parent_return_exit is None and frame_return_exit is None

    if not provider.isPythonModule():
        locals_code = getFrameLocalsUpdateCode(
            provider = provider,
            context  = context
        )

        # TODO: Not using locals, which is only OK for modules
        assert False, locals_code

    return CodeTemplates.template_frame_guard_once % {
        "frame_identifier"      : frame_identifier,
        "code_identifier"       : code_identifier,
        "codes"                 : indented(codes, 0),
        "module_identifier"     : getModuleAccessCode(context = context),
        "tb_making"             : getTracebackMakingIdentifier(context),
        "parent_exception_exit" : parent_exception_exit,
        "frame_exception_exit"  : frame_exception_exit,
        "no_exception_exit"     : context.allocateLabel(
            "frame_no_exception"
        ),
        "needs_preserve"        : 1 if needs_preserve else 0
    }


def getFrameGuardLightCode(frame_identifier, code_identifier, codes,
                           parent_exception_exit, parent_return_exit,
                           frame_exception_exit, frame_return_exit,
                           provider, context):
    context.markAsNeedsExceptionVariables()

    assert frame_exception_exit is not None

    no_exception_exit = context.allocateLabel("frame_no_exception")

    result = CodeTemplates.template_frame_guard_generator % {
        "frame_identifier"      : frame_identifier,
        "code_identifier"       : code_identifier,
        "codes"                 : indented(codes, 0),
        "module_identifier"     : getModuleAccessCode(context = context),
        "no_exception_exit"     : no_exception_exit,
    }

    if frame_return_exit is not None:
        result += CodeTemplates.template_frame_guard_generator_return_handler %\
           {
            "frame_identifier"  : frame_identifier,
            "return_exit"       : parent_return_exit,
            "frame_return_exit" : frame_return_exit,
        }

    locals_code = getFrameLocalsUpdateCode(
        provider = provider,
        context  = context
    )

    result += CodeTemplates.template_frame_guard_generator_exception_handler % {
        "frame_identifier"      : frame_identifier,
        "store_frame_locals"    : indented(locals_code, 0, vert_block = True),
        "tb_making"             : getTracebackMakingIdentifier(context),
        "frame_exception_exit"  : frame_exception_exit,
        "parent_exception_exit" : parent_exception_exit,
        "no_exception_exit"     : no_exception_exit,
    }

    return result


def getFrameLocalsUpdateCode(provider, context):
    locals_codes = Emission.SourceCodeCollector()

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

    locals_codes.emit(
        CodeTemplates.template_frame_locals_update % {
            "locals_identifier" : frame_locals_name
        }
    )

    if context.needsCleanup(frame_locals_name):
        context.removeCleanupTempName(frame_locals_name)

    return locals_codes.codes


def getFramePreserveExceptionCode(emit, context):
    emit("// Preserve existing published exception.")

    if python_version < 300:
        emit(
            "PRESERVE_FRAME_EXCEPTION( %(frame_identifier)s );" % {
                "frame_identifier" : context.getFrameHandle()
            }
        )
    else:
        exception_target = context.pushFrameExceptionPreservationDepth()

        if exception_target is None:
            emit(
                "PRESERVE_FRAME_EXCEPTION( %(frame_identifier)s );" % {
                    "frame_identifier" : context.getFrameHandle()
                }
            )
        else:
            keeper_type, keeper_value, keeper_tb = exception_target

            emit(
                """\
%(keeper_type)s = INCREASE_REFCOUNT( PyThreadState_GET()->exc_type );
%(keeper_value)s = INCREASE_REFCOUNT_X( PyThreadState_GET()->exc_value );
%(keeper_tb)s = (PyTracebackObject *)INCREASE_REFCOUNT_X( PyThreadState_GET()->exc_traceback );
""" % {
                    "keeper_type"  : keeper_type,
                    "keeper_value" : keeper_value,
                    "keeper_tb"    : keeper_tb
                }
            )


def getFrameRestoreExceptionCode(emit, context):
    emit("// Restore previous exception.")

    if python_version < 300:
        emit(
            "RESTORE_FRAME_EXCEPTION( %(frame_identifier)s );" % {
                "frame_identifier" : context.getFrameHandle()
            }
        )
    else:
        exception_target = context.popFrameExceptionPreservationDepth()

        if exception_target is None:
            emit(
                "RESTORE_FRAME_EXCEPTION( %(frame_identifier)s );" % {
                    "frame_identifier" : context.getFrameHandle()
                }
            )
        else:
            keeper_type, keeper_value, keeper_tb = exception_target

            emit(
                """\
SET_CURRENT_EXCEPTION( %(keeper_type)s, %(keeper_value)s, %(keeper_tb)s);""" % {
                    "keeper_type"  : keeper_type,
                    "keeper_value" : keeper_value,
                    "keeper_tb"    : keeper_tb
                }
            )


def getFrameReraiseExceptionCode(emit, context):
    assert python_version >= 300

    emit(
        """\
exception_type = INCREASE_REFCOUNT( PyThreadState_GET()->exc_type );
exception_value = INCREASE_REFCOUNT( PyThreadState_GET()->exc_value );
exception_tb = (PyTracebackObject *)INCREASE_REFCOUNT( PyThreadState_GET()->exc_traceback );
""" )
    getSetLineNumberCodeRaw("exception_tb->tb_lineno", emit, context)
    getFrameRestoreExceptionCode(emit, context)

    getGotoCode(context.getExceptionEscape(), emit )
